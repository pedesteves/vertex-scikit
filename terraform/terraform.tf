terraform {
  required_version = ">=1.0"

  backend "gcs" {
    bucket = "zencore-vertex-tfstate"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 3.90.0, <4.0.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 3.90.0, <4.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.default_region
  zone    = var.default_zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.default_region
  zone    = var.default_zone
}
