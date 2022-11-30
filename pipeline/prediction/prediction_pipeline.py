import kfp
from kfp.v2 import compiler
from kfp.v2.dsl import component, Input, Output, Artifact, Dataset

from google.cloud import storage
from google_cloud_pipeline_components import aiplatform as gcc_aip

PIPELINE_NAME = 'bean-type-prediction'
PIPELINE_DESTINATION = 'gs://zencore-vertex-pipeline-artifacts/compiledpipelines'
LOAD_PYTHON_FILE = 'gs://zencore-vertex-pipeline-artifacts/sparkjobs/load.py'

@component(packages_to_install=['google-cloud-dataproc'])
def dataproc_submit_op(
    cluster_name: str,
    project_id: str,
    region: str,
    display_name: str,
    input_path: str,
    output_type: str,
    output_destination: str,
    main_python_file_uri: str,
    dataprocjob: Output[Artifact],
    dataset: Output[Dataset],
    args: list = [],
    temp_bucket: str = ""):

    from datetime import datetime
    from google.cloud import dataproc_v1 as dataproc

    if temp_bucket == "":
        temp_bucket = f"{project_id}-dataproc-temp"

    time_string = datetime.now().strftime("%Y_%m_%dT%H_%M_%S_%fZ")

    if output_type == "gcs":
        output_path = f"{output_destination}/{display_name}-{time_string}"
    elif output_type == "bq":
        output_path = f"{output_destination}_{time_string}"
    else:
        raise ValueError("output_type must be either 'gcs' or 'bq'")

    dataset.uri = output_path

    args = args + ["--input-path", input_path]+ ["--output-path", output_path] + ["--temp-bucket", temp_bucket]

    job_client = dataproc.JobControllerClient(
        client_options={"api_endpoint": "{}-dataproc.googleapis.com:443".format(region)}
    )

    job = {
        "placement": {"cluster_name": cluster_name},
        "pyspark_job": {
            "main_python_file_uri": main_python_file_uri,
            "args": args
        }
    }

    operation = job_client.submit_job_as_operation(
        request={"project_id": project_id, "region": region, "job": job}
    )

    dataprocjob.metadata['job_id'] = operation.metadata.job_id
    dataprocjob.uri = f"https://dataproc.googleapis.com/v1/projects/{project_id}/regions/{region}/jobs/{operation.metadata.job_id}"

    operation.result()

@component
def get_source_uris_op(dataset: Input[Dataset]) -> list:
    return [f"{dataset.uri}/*.txt"]

@component
def get_prediction_output_uris_op(job: Input[Artifact]) -> str:
    return f"{job.metadata['gcsOutputDirectory']}"

@kfp.dsl.pipeline(name="scikit-batch-prediction")
def pipeline(
    project_id: str,
    location: str,
    display_name: str,
    dataproc_cluster: str,
    dataproc_python_file: str,
    input_table: str,
    preprocess_args: list,
    model_uri: str,
    staging_bucket: str,
    load_args: list,
    output_destination: str
    ):

    preprocess_task = dataproc_submit_op(
        project_id=project_id,
        region=location,
        cluster_name=dataproc_cluster,
        display_name=display_name,
        input_path=input_table,
        main_python_file_uri=dataproc_python_file,
        output_type="gcs",
        output_destination=staging_bucket,
        args=preprocess_args)

    model_upload_task = gcc_aip.ModelUploadOp(
        project=project_id,
        location=location,
        display_name=display_name,
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-23:latest",
        artifact_uri=model_uri
    )

    get_preprocessing_output = get_source_uris_op(
        dataset=preprocess_task.outputs['dataset']
    )

    prediction_task = gcc_aip.ModelBatchPredictOp(
        project=project_id,
        location=location,
        job_display_name=display_name,
        model=model_upload_task.outputs['model'],
        gcs_source_uris=get_preprocessing_output.output,
        instances_format="jsonl",
        gcs_destination_output_uri_prefix=staging_bucket,
        predictions_format="jsonl",
        machine_type="n1-standard-2",
        starting_replica_count=1,
        max_replica_count=1
    )

    get_prediction_path = get_prediction_output_uris_op(
        job=prediction_task.outputs['batchpredictionjob'].ignore_type()
    )

    bq_load_task = dataproc_submit_op(
        project_id=project_id,
        region=location,
        cluster_name=dataproc_cluster,
        display_name=display_name,
        main_python_file_uri=LOAD_PYTHON_FILE,
        input_path=get_prediction_path.output,
        output_type="bq",
        output_destination=output_destination,
        args=load_args
        )

compiler.Compiler().compile(
    pipeline_func=pipeline,
    package_path=f"{PIPELINE_NAME}-pipeline.json",
)

storage_client = storage.Client()

blob = storage.blob.Blob.from_string(f"{PIPELINE_DESTINATION}/{PIPELINE_NAME}-pipeline.json", client=storage_client)
blob.upload_from_filename(f"{PIPELINE_NAME}-pipeline.json")
