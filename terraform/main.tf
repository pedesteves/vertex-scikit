resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "dataproc" {
  service            = "dataproc.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "vertex" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "workbench" {
  service            = "notebooks.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "vertex" {
  account_id = "vertex-pipeline"
}

locals {
  vertex_roles = toset([
    "roles/aiplatform.admin",
    "roles/dataproc.admin",
    "roles/dataproc.worker",
    "roles/bigquery.admin",
    "roles/storage.objectAdmin"
  ])
}

resource "google_project_iam_member" "project" {
  for_each = local.vertex_roles
  role     = each.value
  member   = "serviceAccount:${google_service_account.vertex.email}"
}

resource "google_storage_bucket" "models" {
  name                        = "${var.project_id}-models"
  location                    = var.default_region
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "data" {
  name                        = "${var.project_id}-data"
  location                    = var.default_region
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "dataproc_staging" {
  name                        = "${var.project_id}-dataproc-staging"
  location                    = var.default_region
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "dataproc_temp" {
  name                        = "${var.project_id}-dataproc-temp"
  location                    = var.default_region
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "pipeline_artifacts" {
  name                        = "${var.project_id}-pipeline-artifacts"
  location                    = var.default_region
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_bigquery_dataset" "vertex" {
  dataset_id = "vertex"
  location   = var.default_region
}

resource "google_dataproc_cluster" "dataproc" {
  provider = google-beta

  name     = "dataproc"
  region   = var.default_region

  cluster_config {
    staging_bucket = google_storage_bucket.dataproc_staging.name
    temp_bucket    = google_storage_bucket.dataproc_temp.name

    master_config {
      num_instances = 1
      machine_type  = "e2-standard-4"
    }

    worker_config {
      num_instances    = 0
    }

    gce_cluster_config {
      service_account = google_service_account.vertex.email
      service_account_scopes = [
        "cloud-platform",
        "https://www.googleapis.com/auth/cloud.useraccounts.readonly",
        "https://www.googleapis.com/auth/devstorage.read_write",
        "https://www.googleapis.com/auth/logging.write"
      ]
      metadata = {
        "spark-bigquery-connector-version" = "0.22.2"
      }
    }
    initialization_action {
      script      = "gs://goog-dataproc-initialization-actions-${var.default_region}/connectors/connectors.sh"
      timeout_sec = 500
    }

    software_config{
      optional_components = ["JUPYTER"]
      override_properties = {
        "dataproc:dataproc.allow.zero.workers" = "true"
      }
    }

    endpoint_config {
      enable_http_port_access = "true"
    }
  }

}