import argparse
import json
import os
import subprocess
import time
import requests

from dotenv import load_dotenv

load_dotenv()

use_shell = os.name == "nt"
    

def tf_init():
    subprocess.run(["terraform", "-chdir=terraform", "init"], check=True, shell=use_shell)
    
def tf_env():
    var_pairs = [
        ("project_id", "PROJECT_ID"),
        ("gcp_region", "GCP_REGION"),
        ("bucket_name", "BUCKET_NAME"),
        ("redis_url", "REDIS_URL"),
        ("stats_nz_api_key", "STATS_NZ_API_KEY"),
        ("frontend_domain", "FRONTEND_DOMAIN"),
        ("db_connection_string_prod", "DB_CONNECTION_STRING_PROD"),
        ("firebase_hostsite_id", "FIREBASE_HOSTSITE_ID"),
        ("cloud_run_service_name", "CLOUD_RUN_SERVICE_NAME"),
        ("api_sa_name", "API_SA_NAME")
    ]
    
    tf_env = os.environ.copy()
    for name, env_key in var_pairs:
        tf_env[f"TF_VAR_{name}"] = os.environ[env_key]  # KeyError if unset, instead of get
    
    return tf_env

def try_tf_import(tf_resource_id: str, gcp_resource_id: str) -> bool:
    result = subprocess.run(
        ["terraform", "-chdir=terraform", "import", "-input=false", tf_resource_id, gcp_resource_id],
        env=tf_env(),
        check=False,
        shell=use_shell,
    )
    return result.returncode == 0

def tf_import():
    project = os.environ["PROJECT_ID"]
    region = os.environ["GCP_REGION"]

    imports = [
        ("google_storage_bucket.api_bucket", os.environ["BUCKET_NAME"]),
        ("google_service_account.api_sa", f"projects/{project}/serviceAccounts/{os.environ['API_SA_NAME']}@{project}.iam.gserviceaccount.com"),
        ("google_cloud_run_v2_service.api", f"projects/{project}/locations/{region}/services/{os.environ['CLOUD_RUN_SERVICE_NAME']}"),
        ("google_firebase_hosting_site.api_host_site", f"projects/{project}/sites/{os.environ['FIREBASE_HOSTSITE_ID']}"),
    ]
    
    state_list = subprocess.run(["terraform", "-chdir=terraform", "state", "list"], check=False, capture_output=True, text=True, shell=use_shell)
    in_state = set(state_list.stdout.split())

    # Check what resources already exist before trying to import them - importing an existing gives an error
    for address, resource_id in imports:
        if address in in_state:
            print(f"{address} is already in state, skipping")
        elif not try_tf_import(address, resource_id):
            print(f"Could not import {address}, terraform apply will try to create it")

def tf_plan():
    tf_import()
    subprocess.run(["terraform", "-chdir=terraform", "plan", "-input=false", "-out=terraform.tfplan"], check=True, env=tf_env(), shell=use_shell)

def tf_apply():
    subprocess.run(["terraform", "-chdir=terraform", "apply", "-auto-approve", "terraform.tfplan"], check=True, env=tf_env(), shell=use_shell)

def api_health_check(url):
    for attempt in range(10):
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                return True
            print(f"Attempt {attempt + 1}: API health check returned {response.status_code}")
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}: API health check failed with error: {e}")
        time.sleep(2)
    return False

def deploy_api():
    exists_cmd = [
        "gcloud", "run", "services", "describe", os.environ["CLOUD_RUN_SERVICE_NAME"],
        "--region", os.environ["GCP_REGION"],
        "--format=json"
    ]
    exists = subprocess.run(exists_cmd, check=False, shell=use_shell, capture_output=True, text=True).returncode == 0

    if not exists:
        raise RuntimeError(f"Cloud Run service {os.environ['CLOUD_RUN_SERVICE_NAME']} does not exist. Please run terraform apply first.")
    
    deploy_cmd = [
        "gcloud", "run", "deploy", os.environ["CLOUD_RUN_SERVICE_NAME"],
        "--source", ".",
        "--region", os.environ["GCP_REGION"],
        "--tag", "candidate",
        "--quiet",
        "--no-traffic"
    ]
    
    subprocess.run(deploy_cmd, check=True, shell=use_shell)
    
    describe_cmd = [
        "gcloud", "run", "services", "describe", os.environ["CLOUD_RUN_SERVICE_NAME"],
        "--region", os.environ["GCP_REGION"],
        "--format=json"
    ]
    service = json.loads(subprocess.run(describe_cmd, check=True, capture_output=True, text=True, shell=use_shell).stdout)
    candidate = next((t for t in service["status"]["traffic"] if t.get("tag") == "candidate"), None)
    candidate_url = candidate.get("url") if candidate else None
    revision_name = candidate["revisionName"]
    
    if not (candidate_url and api_health_check(candidate_url)):
        raise RuntimeError(f"Candidate revision {revision_name} failed health check. Aborting deployment.")
    
    print(f"Candidate revision {revision_name} is healthy. Moving traffic to it.")
    update_traffic_cmd = [
        "gcloud", "run", "services", "update-traffic", os.environ["CLOUD_RUN_SERVICE_NAME"],
        "--to-revisions", f"{revision_name}=100",
        "--region", os.environ["GCP_REGION"]
    ]
    subprocess.run(update_traffic_cmd, check=True, shell=use_shell)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deploy NZ Census Map Backend")
    parser.add_argument("--deploy-api", action="store_true",
                        help="Deploy the API to Cloud Run")
    
    parser.add_argument("--tf-all", action="store_true",
                        help="Run all terraform steps (init, plan, apply)")
    
    parser.add_argument("--tf-init", action="store_true",
                        help="Run terraform init")
    
    parser.add_argument("--tf-plan", action="store_true",
                        help="Run terraform plan") 
    
    parser.add_argument("--tf-apply", action="store_true",
                        help="Run terraform apply")
    
    parser.add_argument("--all", "-a", action="store_true",
                        help="Run all steps")

    args = parser.parse_args()
    
    if args.tf_init or args.tf_all or args.all:
        tf_init()

    if args.tf_plan or args.tf_all or args.all:
        tf_plan()
    
    if args.tf_apply or args.tf_all or args.all:
        tf_apply()

    if args.deploy_api or args.all:
        deploy_api()
