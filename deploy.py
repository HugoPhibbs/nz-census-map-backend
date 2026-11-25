import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import requests

from dotenv import load_dotenv

load_dotenv()

use_shell = os.name == "nt"

TF_VARS = json.loads(
    (Path(__file__).parent / "terraform" / "prod.auto.tfvars.json").read_text()
)


def create_tf_backend_bucket():
    bucket_url = f"gs://{TF_VARS['project_id']}-terraform-state"

    bucket_exists = (
        subprocess.run(
            ["gcloud", "storage", "buckets", "describe", bucket_url],
            check=False,
            shell=use_shell,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )

    if bucket_exists:
        print(f"Backend bucket {bucket_url} already exists, skipping creation.")
        return

    create_bucket_cmd = [
        "gcloud",
        "storage",
        "buckets",
        "create",
        bucket_url,
        "--location",
        TF_VARS["gcp_region"],
        "--project",
        TF_VARS["project_id"],
        "--uniform-bucket-level-access",
    ]
    subprocess.run(create_bucket_cmd, check=True, shell=use_shell)

    add_bucket_versioning_cmd = [
        "gcloud",
        "storage",
        "buckets",
        "update",
        bucket_url,
        "--versioning",
    ]
    subprocess.run(add_bucket_versioning_cmd, check=True, shell=use_shell)


def tf_init(no_input: bool):
    init_cmd = ["terraform", "-chdir=terraform", "init"]

    if no_input:
        init_cmd.append("-input=false")

    subprocess.run(init_cmd, check=True, shell=use_shell)


def tf_env():
    secret_pairs = [
        ("redis_password", "REDIS_PASSWORD"),
        ("db_password", "DB_PASSWORD"),
        ("mcp_bearer_token", "MCP_BEARER_TOKEN"),
    ]

    tf_env = os.environ.copy()
    for name, env_key in secret_pairs:
        tf_env[f"TF_VAR_{name}"] = os.environ[env_key]

    return tf_env


def tf_plan(no_input: bool):
    plan_cmd = ["terraform", "-chdir=terraform", "plan"]
    
    if no_input:
        plan_cmd.append("-input=false")

    subprocess.run(plan_cmd, check=True, env=tf_env(), shell=use_shell)


def tf_apply(no_input: bool):
    apply_cmd = ["terraform", "-chdir=terraform", "apply"]
    
    if no_input:
        apply_cmd.extend(["-auto-approve", "-input=false"])
    
    subprocess.run(
        apply_cmd,
        check=True,
        env=tf_env(),
        shell=use_shell,
    )


def api_health_check(url):
    return _health_check(f"{url}/health", expected_status=200)


def mcp_health_check(url):
    # No auth header, so a live MCP server should reject us with 401
    return _health_check(f"{url}/mcp", expected_status=401)


def _health_check(url, expected_status):
    for attempt in range(10):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == expected_status:
                return True
            print(
                f"Attempt {attempt + 1}: API health check returned {response.status_code}"
            )
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}: API health check failed with error: {e}")
        time.sleep(2)
    return False

def restart_redis_vm():
    restart_cmd = [
        "gcloud",
        "compute",
        "instances",
        "reset",
        TF_VARS["redis_vm_name"],
        "--zone",
        f"{TF_VARS['gcp_region']}-{TF_VARS['redis_vm_zone']}",
    ]
    subprocess.run(restart_cmd, check=True, shell=use_shell)


def update_api():
    update_cloud_run_service(TF_VARS["cloud_run_service_name"], api_health_check)


def update_mcp():
    update_cloud_run_service(TF_VARS["mcp_service_name"], mcp_health_check)


def update_cloud_run_service(service_name, health_check):
    # Check if it exists first, we only intend to update the API, not deploy it for the first time (managed by Terraform)
    exists_cmd = [
        "gcloud",
        "run",
        "services",
        "describe",
        service_name,
        "--region",
        TF_VARS["gcp_region"],
        "--format=json",
    ]
    exists_result = subprocess.run(
        exists_cmd, check=False, shell=use_shell, capture_output=True, text=True
    )

    if exists_result.returncode != 0:
        raise RuntimeError(
            f"Could not find Cloud Run service {service_name}. If it doesn't exist, run terraform apply first.\n"
            f"gcloud output:\n{exists_result.stdout}{exists_result.stderr}"
        )

    deploy_cmd = [
        "gcloud",
        "run",
        "deploy",
        service_name,
        "--source",
        ".",
        "--region",
        TF_VARS["gcp_region"],
        "--tag",
        "candidate",
        "--quiet",
        "--no-traffic",
    ]

    subprocess.run(deploy_cmd, check=True, shell=use_shell)

    describe_cmd = [
        "gcloud",
        "run",
        "services",
        "describe",
        service_name,
        "--region",
        TF_VARS["gcp_region"],
        "--format=json",
    ]
    service = json.loads(
        subprocess.run(
            describe_cmd, check=True, capture_output=True, text=True, shell=use_shell
        ).stdout
    )
    candidate = next(
        (t for t in service["status"]["traffic"] if t.get("tag") == "candidate"), None
    )
    candidate_url = candidate.get("url") if candidate else None

    if not (candidate_url and health_check(candidate_url)):
        raise RuntimeError(
            f"Candidate revision failed health check. Aborting deployment."
        )

    revision_name = candidate["revisionName"]

    print(f"Candidate revision {revision_name} is healthy. Moving traffic to it.")
    update_traffic_cmd = [
        "gcloud",
        "run",
        "services",
        "update-traffic",
        service_name,
        "--to-revisions",
        f"{revision_name}=100",
        "--region",
        TF_VARS["gcp_region"],
    ]
    subprocess.run(update_traffic_cmd, check=True, shell=use_shell)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy NZ Census Map Backend")

    parser.add_argument(
        "--no-input",
        "-ni",
        action="store_true",
        help="Run without user input (for CI/CD)",
    )

    parser.add_argument(
        "--create-tf-backend-bucket",
        "-cbb",
        action="store_true",
        help="Create the GCS bucket for Terraform state",
    )

    parser.add_argument(
        "--update-api", action="store_true", help="Add the latest changes to the API on Cloud Run"
    )

    parser.add_argument(
        "--tf-init-apply",
        action="store_true",
        help="Run terraform init and apply",
    )

    parser.add_argument(
        "--update-mcp", action="store_true", help="Add the latest changes to the MCP server on Cloud Run"
    )

    parser.add_argument("--restart-redis", action="store_true", help="Restart the Redis VM")

    parser.add_argument("--tf-init", action="store_true", help="Run terraform init")

    parser.add_argument("--tf-plan", action="store_true", help="Run terraform plan")

    parser.add_argument("--tf-apply", action="store_true", help="Run terraform apply")

    args = parser.parse_args()

    if args.create_tf_backend_bucket:
        create_tf_backend_bucket()

    if args.tf_init or args.tf_init_apply:
        tf_init(no_input=args.no_input)

    if args.tf_plan:
        tf_plan(no_input=args.no_input)

    if args.tf_apply or args.tf_init_apply:
        tf_apply(no_input=args.no_input)

    if args.update_api:
        update_api()

    if args.update_mcp:
        update_mcp()

    if args.restart_redis:
        restart_redis_vm()