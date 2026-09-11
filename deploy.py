import subprocess

SA_NAME = "nz-census-map-api-sa"
BUCKET_NAME = "nz-census-map-api-bucket"
REGION = "europe-west2"
PROJECT_ID = "nz-census-map"

def set_project():
    set_project_cmd = ["gcloud", "config", "set", "project", PROJECT_ID]
    subprocess.run(set_project_cmd, check=True, shell=True)


def deploy_bucket():
    bucket_exists_cmd = ["gcloud", "storage", "buckets", "describe", f"gs://{BUCKET_NAME}"]
    if subprocess.run(bucket_exists_cmd, capture_output=True, shell=True).returncode == 0:
        print(f"Bucket {BUCKET_NAME} already exists. Skipping creation.")
        return
    
    create_bucket_cmd = ["gcloud", "storage", "buckets",
                         "create", f"gs://{BUCKET_NAME}", f"--location={REGION}"]
    subprocess.run(create_bucket_cmd, check=True, shell=True)


def create_service_account():
    sa_exists_cmd = ["gcloud", "iam", "service-accounts", "describe",
                     f"{SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com"]
    if subprocess.run(sa_exists_cmd, capture_output=True, shell=True).returncode == 0:
        print(f"Service account {SA_NAME} already exists. Skipping creation.")
        return
    
    create_sa_cmd = ["gcloud", "iam", "service-accounts", "create",
                     SA_NAME, "--display-name=Cloud Run SA"]
    subprocess.run(create_sa_cmd, check=True, shell=True)

    grant_bucket_access_cmd = [
        "gcloud", "storage", "buckets", "add-iam-policy-binding", f"gs://{BUCKET_NAME}",
        "--member", f"serviceAccount:{SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com",
        "--role", "roles/storage.objectAdmin",
    ]
    subprocess.run(grant_bucket_access_cmd, check=True, shell=True)


def deploy_cloud_run():
    cmd = ["gcloud", "run",
           "deploy", "nz-census-map-api",
           "--source", ".",
           "--region", f"{REGION}",
           "--allow-unauthenticated",
           "--service-account", f"{SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com",
           "--env-vars-file=env.yaml"]

    subprocess.run(cmd, check=True, shell=True)


if __name__ == "__main__":
    set_project()
    deploy_bucket()
    create_service_account()
    deploy_cloud_run()
