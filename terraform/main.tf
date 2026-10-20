terraform {
  backend "gcs" {
    bucket = "nz-census-map-terraform-state"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source = "hashicorp/google"
    }
    google-beta = {
      source = "hashicorp/google-beta"
    }
  }
}

### Local variables
locals {
  cloud_run_sa_name    = "nz-census-map-api-sa"
  frontend_domain      = "https://nz-census-map.com"
  db_server_name       = "nz-census-map-db"
  db_name              = "census_db"
  db_user              = "api_user"
  firebase_hostsite_id = "nz-census-map"
}

### Setting up providers

variable "project_id" {
  type = string
}

variable "gcp_region" {
  type = string
}

provider "google" {
  project = var.project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.project_id
  region  = var.gcp_region
}

### Storage bucket
variable "bucket_name" {
  type = string
}

resource "google_storage_bucket" "api_bucket" {
  name     = var.bucket_name
  location = var.gcp_region

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

variable "redis_url" {
  type      = string
  sensitive = true
}

variable "cloud_run_service_name" {
  type = string
}

resource "google_service_account" "api_sa" {
  account_id   = local.cloud_run_sa_name
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

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.api_db.connection_name]
      }
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      args  = ["api"]

      resources {
        startup_cpu_boost = true
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name  = "DB_HOST"
        value = "/cloudsql/${google_sql_database_instance.api_db.connection_name}"
      }

      env {
        name  = "DB_NAME"
        value = google_sql_database.api_db_database.name
      }

      env {
        name  = "DB_USER"
        value = google_sql_user.api_db_user.name
      }

      env {
        name  = "DB_PASSWORD"
        value = var.db_password
      }

      env {
        name  = "FRONTEND_DOMAIN"
        value = local.frontend_domain
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
      template[0].revision,            # E.g. 'candidate'
      build_config,
      client, # Who deployed
      client_version,
      traffic
    ]
  }
}

### PostgreSQL database
variable "db_password" {
  type      = string
  sensitive = true
}

resource "google_project_service" "sqladmin" {
  service = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_sql_database_instance" "api_db" {
  name             = local.db_server_name
  database_version = "POSTGRES_18"
  region           = var.gcp_region
  depends_on       = [google_project_service.sqladmin]

  settings {
    tier    = "db-g1-small"
    edition = "ENTERPRISE"

    backup_configuration {
      enabled = true
    }
  }
}

resource "google_sql_database" "api_db_database" {
  name     = local.db_name
  instance = google_sql_database_instance.api_db.name
}

resource "google_sql_user" "api_db_user" {
  name     = local.db_user
  instance = google_sql_database_instance.api_db.name
  password = var.db_password
}

resource "google_project_iam_member" "api_sa_cloud_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api_sa.email}"

  condition {
    title       = "Allow Cloud Run service account to access Cloud SQL"
    description = "This condition allows the Cloud Run service account to access the Cloud SQL instance."
    expression  = "resource.name == \"projects/${var.project_id}/instances/${google_sql_database_instance.api_db.name}\""
  }
}

### Firebase host for API
resource "google_firebase_hosting_site" "api_host_site" {
  provider = google-beta
  site_id  = local.firebase_hostsite_id
}

resource "google_firebase_hosting_version" "api_host_version" {
  provider = google-beta
  site_id  = google_firebase_hosting_site.api_host_site.site_id

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
  provider     = google-beta
  site_id      = google_firebase_hosting_site.api_host_site.site_id
  version_name = google_firebase_hosting_version.api_host_version.name
}
