import os
import subprocess
from dotenv import load_dotenv
load_dotenv()


def set_project():
    set_project_cmd = ["gcloud", "config", "set",
                       "project", os.getenv("PROJECT_ID")]
    subprocess.run(set_project_cmd, check=True, shell=True)


def update_bucket_cors():
    update_cors_cmd = ["gcloud", "storage", "buckets", "update", f"gs://{os.getenv('BUCKET_NAME')}", "--cors-file=./deploy/bucket-cors.json"]
    
    subprocess.run(update_cors_cmd, check=True, shell=True)

def deploy_bucket():
    bucket_exists_cmd = ["gcloud", "storage", "buckets",
                         "describe", f"gs://{os.getenv('BUCKET_NAME')}"]
    if subprocess.run(bucket_exists_cmd, capture_output=True, shell=True).returncode == 0:
        print(
            f"Bucket {os.getenv('BUCKET_NAME')} already exists. Skipping creation.")
        return

    create_bucket_cmd = ["gcloud", "storage", "buckets",
                         "create", f"gs://{os.getenv('BUCKET_NAME')}", f"--location={os.getenv('GCP_REGION')}"]
    subprocess.run(create_bucket_cmd, check=True, shell=True)


def create_service_account():
    sa_exists_cmd = ["gcloud", "iam", "service-accounts", "describe",
                     f"{os.getenv('SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com"]
    if subprocess.run(sa_exists_cmd, capture_output=True, shell=True).returncode == 0:
        print(
            f"Service account {os.getenv('SA_NAME')} already exists. Skipping creation.")
        return

    create_sa_cmd = ["gcloud", "iam",
                     "service-accounts",
                     "create", os.getenv('SA_NAME'),
                     "--display-name=Cloud Run SA",
                     ]

    subprocess.run(create_sa_cmd, check=True, shell=True)

    grant_bucket_access_cmd = [
        "gcloud", "storage", "buckets", "add-iam-policy-binding", f"gs://{os.getenv('BUCKET_NAME')}",
        "--member", f"serviceAccount:{os.getenv('SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
        "--role", "roles/storage.objectAdmin",
    ]
    subprocess.run(grant_bucket_access_cmd, check=True, shell=True)

    grant_token_creator_cmd = [
        "gcloud", "iam", "service-accounts", "add-iam-policy-binding",
        f"{os.getenv('SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
        "--member", f"serviceAccount:{os.getenv('SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
        "--role", "roles/iam.serviceAccountTokenCreator",
    ]
    subprocess.run(grant_token_creator_cmd, check=True, shell=True)


def fill_bucket_with_data():
    files_to_upload = ["combined.pmtiles", "sa1.pmtiles"]
    for file in files_to_upload:
        upload_cmd = [
            "gsutil", "cp", f"./data/pmtiles/{file}", f"gs://{os.getenv('BUCKET_NAME')}/{file}"]
        subprocess.run(upload_cmd, check=True, shell=True)


def deploy_cloud_run():
    freeze_requirements_cmd = ["pip", "freeze", ">", "./requirements.txt"]
    subprocess.run(freeze_requirements_cmd, check=True, shell=True)

    cmd = ["gcloud", "run",
           "deploy", "nz-census-map-api",
           "--source", ".",
           "--region", f"{os.getenv('GCP_REGION')}",
           "--allow-unauthenticated",
           "--service-account", f"{os.getenv('SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
           "--env-vars-file=env.yaml"]

    subprocess.run(cmd, check=True, shell=True)


if __name__ == "__main__":    
    set_project()
    deploy_bucket()
    create_service_account()
    deploy_cloud_run()
    fill_bucket_with_data()
    update_bucket_cors()
