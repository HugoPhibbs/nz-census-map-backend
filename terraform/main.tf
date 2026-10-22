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

### VPC network
resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_compute_network" "backend_vpc" {
  name                    = "nz-census-map-backend-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.compute]
}

resource "google_compute_subnetwork" "backend_vpc_subnet" {
  name          = "nz-census-map-backend-subnet"
  ip_cidr_range = "10.10.0.0/24" # From 10.10.0.0 to 10.10.0.255
  region        = var.gcp_region
  network       = google_compute_network.backend_vpc.id
}

### Backend API

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

    vpc_access {
      network_interfaces {
        subnetwork = google_compute_subnetwork.backend_vpc_subnet.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      args  = ["api"]

      resources {
        startup_cpu_boost = true
      }

      env {
        name  = "DB_HOST"
        value = google_compute_address.api_db_private_ip.address
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
        name = "DB_SSL_MODE"
        value = "require"
      }

      env {
        name  = "FRONTEND_DOMAIN"
        value = local.frontend_domain
      }

      env {
        name  = "REDIS_HOST"
        value = local.redis_ip
      }

      env {
        name  = "REDIS_PASSWORD"
        value = var.redis_password
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
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_sql_database_instance" "api_db" {
  name                = local.db_server_name
  database_version    = "POSTGRES_18"
  region              = var.gcp_region
  depends_on          = [google_project_service.sqladmin]
  deletion_protection = true

  settings {
    tier                        = "db-g1-small"
    edition                     = "ENTERPRISE"
    deletion_protection_enabled = true

    connector_enforcement = "NOT_REQUIRED"

    backup_configuration {
      enabled = true
    }

    ip_configuration {
      ipv4_enabled = false
      psc_config {
        psc_enabled               = true
        allowed_consumer_projects = [var.project_id]
      }
    }
  }
}

resource "google_compute_address" "api_db_private_ip" {
  name         = "nz-census-map-db-private-ip"
  region       = var.gcp_region
  subnetwork   = google_compute_subnetwork.backend_vpc_subnet.id
  address_type = "INTERNAL"
  address      = "10.10.0.50"
}

resource "google_compute_forwarding_rule" "api_db_forwarding_rule" {
  name       = "nz-census-map-db-forwarding-rule"
  region     = var.gcp_region
  network    = google_compute_network.backend_vpc.id
  ip_address = google_compute_address.api_db_private_ip.id
  target     = google_sql_database_instance.api_db.psc_service_attachment_link
  load_balancing_scheme = ""
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

### Redis instance
variable "redis_password" {
  type      = string
  sensitive = true
}

variable "redis_vm_zone" {
  type = string
}

variable "redis_vm_name" {
  type = string
}

locals {
  redis_ip         = "10.10.0.100"
  redis_max_memory = "128mb"
}

resource "google_compute_firewall" "allow_redis" {
  name          = "allow-redis"
  network       = google_compute_network.backend_vpc.name
  source_ranges = [google_compute_subnetwork.backend_vpc_subnet.ip_cidr_range]

  allow {
    protocol = "tcp"
    ports    = ["6379"]
  }
}

resource "google_compute_firewall" "allow_redis_iap" {
  name          = "allow-redis-iap"
  network       = google_compute_network.backend_vpc.name
  source_ranges = ["35.235.240.0/20"] # Google IAP TCP forwarding range

  allow {
    protocol = "tcp"
    ports    = ["6379"]
  }
}

resource "google_compute_router" "backend_router" {
  name    = "nz-census-map-backend-router"
  region  = var.gcp_region
  network = google_compute_network.backend_vpc.id
}

resource "google_compute_router_nat" "backend_nat" {
  name   = "nz-census-map-backend-nat"
  router = google_compute_router.backend_router.name
  region = var.gcp_region

  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"

  subnetwork {
    name                    = google_compute_subnetwork.backend_vpc_subnet.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
}

resource "google_compute_instance" "redis_instance" {
  name         = var.redis_vm_name
  machine_type = "e2-micro"
  zone         = "${var.gcp_region}-${var.redis_vm_zone}"
  depends_on   = [google_compute_router_nat.backend_nat]

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.backend_vpc_subnet.id
    network_ip = local.redis_ip
  }

  metadata = {
    startup-script = <<-EOT
      #!/bin/bash
      docker rm -f redis
      docker run -d --name redis --restart=always -p 6379:6379 redis:7.4-alpine \
        redis-server --requirepass "${var.redis_password}" --maxmemory ${local.redis_max_memory} --maxmemory-policy allkeys-lru
    EOT
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
