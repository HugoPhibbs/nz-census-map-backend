terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
    }
  }
}

### Setting up providers
variable "project_id" {
  type        = string
  description = "The GCP project ID"
}

variable "gcp_region" {
  type        = string
  description = "The GCP region"
}

provider "google" {
    project = var.project_id
    region = var.gcp_region
}

provider "google-beta" {
    project = var.project_id
    region = var.gcp_region
}

### Storage bucket

variable "bucket_name" {
  type        = string
  description = "The name of the GCP storage bucket"
}

resource "google_storage_bucket" "api_bucket" {
  name          = var.bucket_name
  location      = var.gcp_region

  cors {
    origin          = ["*"]
    method          = ["GET"]
    response_header = ["Content-Type", "Range", "Content-Range"]
    max_age_seconds = 3600
  }
}

# Open access to the bucket for all users
resource "google_storage_bucket_iam_member" "bucket_iam_member" {
  bucket = google_storage_bucket.api_bucket.name
  role   = "roles/storage.legacyObjectReader"
  member = "allUsers"
}

### Backend API
variable "db_connection_string_prod" {
  type      = string
  sensitive = true
}

variable "stats_nz_api_key" {
  type      = string
  sensitive = true
}

variable "redis_url" {
  type      = string
  sensitive = true
}

variable "frontend_domain" {
  type = string
}

variable "cloud_run_service_name" {
  type        = string
  description = "The name of the Cloud Run service"
}

variable "api_sa_name" {
  type        = string
  description = "The name of the service account for the API"
}

resource "google_service_account" "api_sa" {
  account_id   = var.api_sa_name
  display_name = "Cloud Run SA"
}

resource "google_cloud_run_v2_service" "api" {
  name     = var.cloud_run_service_name
  location = var.gcp_region

  invoker_iam_disabled = true # Public

  template {
    service_account = google_service_account.api_sa.email

    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      args  = ["api"]

      resources {
        startup_cpu_boost = true
      }

      env {
        name  = "DB_CONNECTION_STRING_PROD"
        value = var.db_connection_string_prod
      }

      env {
        name  = "STATS_NZ_API_KEY"
        value = var.stats_nz_api_key
      }

      env {
        name  = "FRONTEND_DOMAIN"
        value = var.frontend_domain
      }

      env {
        name  = "REDIS_URL"
        value = var.redis_url
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image, # Image name
      client, # Who deployed
      client_version,
      traffic
    ]
  }
}

### Firebase host for API
variable "firebase_hostsite_id" {
  type        = string
  description = "The ID of the Firebase hosting site"
}

resource "google_firebase_hosting_site" "api_host_site" {
  provider = google-beta
  site_id = var.firebase_hostsite_id
}

resource "google_firebase_hosting_version" "api_host_version" {
  provider = google-beta
  site_id = google_firebase_hosting_site.api_host_site.site_id

  config {
    rewrites {
      glob = "**"
      run {
        service_id = google_cloud_run_v2_service.api.name
        region     = google_cloud_run_v2_service.api.location
      }
    }
  }
}

resource "google_firebase_hosting_release" "api_host_release" {
  provider = google-beta
  site_id = google_firebase_hosting_site.api_host_site.site_id
  version_name = google_firebase_hosting_version.api_host_version.name
}