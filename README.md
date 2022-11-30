# Vertex AI - scikit

The repository contains pipelines and sample models to show running Scikit Learn models on Vertex AI

This repository contains
- Terraform to configure infrastructure
- Sample Models
- pyspark files to perform ETL
- Vertex Pipelines for a training and prediction workflow

## Background Reading
- Vertex Pipelines supports using the [Kubeflow Pipelines SDK V2](https://www.kubeflow.org/docs/components/pipelines/sdk-v2/) to author orchestration pipelines. Reviewing the Kubeflow Pipelines material will be helpful to understand the pipelines code.
- Vertex supports importing scikit models that have been trained in external systems. See the Scikit documentation on [model persistence](https://scikit-learn.org/stable/modules/model_persistence.html).

## Infrastructure Prerequisites

Terraform is provided to configure the necessary infrastructure assets required to deploy. You can run this by creating a `terraform.tfvars` file and running `terraform plan` and `terraform apply`

Sample tfvars file:
```
project_id     = "my-vertex-project"
default_region = "us-east1"
default_zone   = "us-east1-b"
```

## Importing Models
A sample notebook is available showing how to train an external model and upload it to GCS for import into Vertex AI. `./pipeline/models/bean_prediction/model.ipynb` shows this procedure. Data from BQ is loaded into the notebook, and a model is trained. The model is then exported, and uploaded to GCS in the last cell. Once this is complete the model can be [imported into Vertex AI](https://cloud.google.com/vertex-ai/docs/general/import-model) using the prebuilt container for scikit-learn.

## Prediction Pipeline Prerequisites
Prior to running the prediction pipeline, a set of artifacts need to be staged into GCS.
- both pyspark jobs from `./pipeline/etl/` need to be uploaded to a GCS bucket.
- The trained model needs to be uploaded to GCS. See Importing Models above.
- The pipeline needs to be compiled, and the resulting json needs to be uploaded to GCS. This can be performed by running `python ./pipeline/prediction/prediction_pipeline.py`

## Deploying a Prediction Pipeline Run
- After the prediction pipeline prerequistes are met,the prediction pipeline can be run with the `./pipeline//models/bean_prediction/run_pipeline.ipynb` notebook. Inputs to the notebook will need to be updated to reflect the appropriate location of staged artifacts.
