import argparse
import json
import os
import subprocess

from dotenv import load_dotenv

load_dotenv()

CLOUD_RUN_SERVICES = {
    "api": {
        "name": "nz-census-map-api",
        "command": "api",
        "env": ["DB_CONNECTION_STRING_PROD", "STATS_NZ_API_KEY",
                "BUCKET_NAME", "FRONTEND_DOMAIN"]
    },
    "mcp": {
        "name": "nz-census-map-mcp",
        "command": "mcp",
        "env": ["DB_CONNECTION_STRING_PROD", "MCP_BEARER_TOKEN"]
    },
}


def set_project():
    set_project_cmd = ["gcloud", "config", "set",
                       "project", os.getenv("PROJECT_ID")]
    subprocess.run(set_project_cmd, check=True, shell=True)


def update_bucket_cors():
    update_cors_cmd = ["gcloud", "storage", "buckets", "update",
                       f"gs://{os.getenv('BUCKET_NAME')}", "--cors-file=./deploy/bucket-cors.json"]

    subprocess.run(update_cors_cmd, check=True, shell=True)


def deploy_bucket():
    bucket_name = os.getenv("BUCKET_NAME")
    
    bucket_exists_cmd = ["gcloud", "storage", "buckets",
                         "describe", f"gs://{bucket_name}"]
    if  subprocess.run(bucket_exists_cmd, capture_output=True, shell=True).returncode == 0:
        print(
            f"Bucket {bucket_name} already exists. Skipping creation.")
    else:   
        create_bucket_cmd = ["gcloud", "storage", "buckets",
                            "create", f"gs://{bucket_name}", f"--location={os.getenv('GCP_REGION')}"]
        subprocess.run(create_bucket_cmd, check=True, shell=True)

    subprocess.run(["gcloud", "storage", "buckets", "add-iam-policy-binding", f"gs://{bucket_name}",
                    "--member=allUsers", "--role=roles/storage.legacyObjectReader"],
                   check=True, shell=True)

def create_service_account():
    sa_exists_cmd = ["gcloud", "iam", "service-accounts", "describe",
                     f"{os.getenv('API_SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com"]
    if subprocess.run(sa_exists_cmd, capture_output=True, shell=True).returncode == 0:
        print(
            f"Service account {os.getenv('API_SA_NAME')} already exists. Skipping creation.")
        return

    create_sa_cmd = ["gcloud", "iam",
                     "service-accounts",
                     "create", os.getenv('API_SA_NAME'),
                     "--display-name=Cloud Run SA",
                     ]

    subprocess.run(create_sa_cmd, check=True, shell=True)

    grant_bucket_access_cmd = [
        "gcloud", "storage", "buckets", "add-iam-policy-binding", f"gs://{os.getenv('BUCKET_NAME')}",
        "--member", f"serviceAccount:{os.getenv('API_SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
        "--role", "roles/storage.objectAdmin",
    ]
    subprocess.run(grant_bucket_access_cmd, check=True, shell=True)

    grant_token_creator_cmd = [
        "gcloud", "iam", "service-accounts", "add-iam-policy-binding",
        f"{os.getenv('API_SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
        "--member", f"serviceAccount:{os.getenv('API_SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
        "--role", "roles/iam.serviceAccountTokenCreator",
    ]
    subprocess.run(grant_token_creator_cmd, check=True, shell=True)


def fill_bucket_with_data():
    files_to_upload = ["combined.pmtiles", "sa1.pmtiles"]
    for file in files_to_upload:
        upload_cmd = [
            "gsutil", "cp", f"./data/pmtiles/{file}", f"gs://{os.getenv('BUCKET_NAME')}/{file}"]
        subprocess.run(upload_cmd, check=True, shell=True)

def deploy_cloud_run(service_name):
    service = CLOUD_RUN_SERVICES[service_name]

    env_str = ",".join(f"{k}={os.getenv(k)}" for k in service["env"])

    deploy_cmd = [
        "gcloud", "run", "deploy", service["name"],
        "--verbosity=debug",
        "--source .",
        "--region", os.getenv("GCP_REGION"),
        "--cpu-boost",
        "--min-instances=1",
        "--allow-unauthenticated",
        "--service-account", f"{os.getenv('API_SA_NAME')}@{os.getenv('PROJECT_ID')}.iam.gserviceaccount.com",
        '--command=""', # Leave empty to run entrypoint.sh
        f"--args={service['command']}",
        f'--set-env-vars="{env_str}"',
    ]

    # We need to join the list up so the env vars are passed through correctly (with double quotes). Otherwise, gcloud interprets each env var as a seperate arg
    subprocess.run(" ".join(deploy_cmd), check=True, shell=True)
    
def deploy_firebase_for_api():
    config = {
        "hosting": {
            "rewrites": [{
                "source": "**",
                "run": {
                    "serviceId": CLOUD_RUN_SERVICES["api"]["name"],
                    "region": os.getenv("GCP_REGION"),
                }
            }]
        }
    }
    
    filepath = "deploy/firebase.json"
    
    with open(filepath, "w") as f:
        json.dump(config, f, indent=2)
        
    try:    
        cmd = ["firebase", "deploy", "--only", "hosting",  "--project", os.getenv("PROJECT_ID"), "--config", "deploy/firebase.json"]
        subprocess.run(cmd, check=True, shell=True)
    finally:
        os.remove(filepath)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deploy NZ Census Map Backend")
    parser.add_argument("--set-project", "-sp",
                        action="store_true", help="Set the GCP project")
    parser.add_argument("--deploy-bucket", "-db",
                        action="store_true", help="Deploy the GCP bucket")
    parser.add_argument("--create-service-account", "-csa",
                        action="store_true", help="Create the service account")
    parser.add_argument("--deploy-api", "-dapi",
                        action="store_true", help="Deploy the API Cloud Run service")
    parser.add_argument("--deploy-mcp", "-dmcp",
                        action="store_true", help="Deploy the MCP Cloud Run service")
    parser.add_argument("--fill-bucket", "-fb",
                        action="store_true", help="Fill the bucket with data")
    parser.add_argument("--update-bucket-cors", "-ubc",
                        action="store_true", help="Update the bucket CORS settings")
    parser.add_argument("--deploy-firebase", "-df",
                        action="store_true", help="Deploy Firebase Hosting for API")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Run all steps")

    args = parser.parse_args()

    if args.set_project or args.all:
        set_project()

    if args.deploy_bucket or args.all:
        deploy_bucket()

    if args.create_service_account or args.all:
        create_service_account()

    if args.deploy_api or args.all:
        deploy_cloud_run("api")

    if args.deploy_mcp or args.all:
        deploy_cloud_run("mcp")

    if args.fill_bucket or args.all:
        fill_bucket_with_data()

    if args.update_bucket_cors or args.all:
        update_bucket_cors()
        
    if args.deploy_firebase or args.all:
        deploy_firebase_for_api()
