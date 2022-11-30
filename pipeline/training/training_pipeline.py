import kfp
import kfp.components as comp

from kfp.v2 import compiler
from google.cloud import aiplatform
from google_cloud_pipeline_components import aiplatform as gcc_aip

@kfp.dsl.pipeline(name="train-scikit")
def pipeline(
    project_id: str,
    location: str,
    staging_bucket: str,
    model_display_name: str
    ):


    training_job_run_op = gcc_aip.CustomPythonPackageTrainingJobRunOp(
        project=project_id,
        location=location,
        display_name=model_display_name,
        python_package_gcs_uri="gs://zencore-vertex-models/trainer-0.1.tar.gz",
        python_module_name="trainer.task",
        staging_bucket=staging_bucket,
        container_uri="us-docker.pkg.dev/vertex-ai/training/scikit-learn-cpu.0-23:latest",
        model_serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-23:latest",
        args=['cloud-samples-data', 'ai-platform/sklearn/census_data/adult.data']
    )

    # model_deploy_op = gcc_aip.ModelDeployOp(
    #     model=training_job_run_op.outputs["model"],
    #     endpoint=aiplatform.Endpoint(
    #         endpoint_name="projects/zencore-vertex/locations/us-east1/endpoints/5013984128891092992"
    #     ).resource_name
    # )

compiler.Compiler().compile(
    pipeline_func=pipeline,
    package_path='scikit-pipeline.json'
)

pipeline_job = aiplatform.PipelineJob(
    project="zencore-vertex",
    location="us-east1",
    display_name="scikit-training-pipeline",
    template_path="scikit-pipeline.json",
    pipeline_root="gs://zencore-vertex-pipeline-artifacts",
    parameter_values={
        "project_id": "zencore-vertex",
        "location": "us-east1",
        "staging_bucket": "gs://zencore-vertex-pipeline-artifacts",
        "model_display_name": "train-scikit-modelv1",
    }
)

pipeline_job.submit()