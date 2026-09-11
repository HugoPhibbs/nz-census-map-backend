import os

from dotenv import load_dotenv
import argparse
from pathlib import Path
import subprocess
import json
import sys

DEPLOY_DIR = Path(__file__).resolve().parent
ROOT_DIR = DEPLOY_DIR.parent

load_dotenv(DEPLOY_DIR.parent / ".env")  # One dir above


def push_func_env():
    ENV_VARS_TO_PUSH = [
        "STATS_NZ_API_KEY",
        "DB_CONNECTION_STRING_PROD"
    ]

    local_settings = {
        "IsEncrypted": False,
        "Values": {k: os.getenv(k) for k in ENV_VARS_TO_PUSH},
    }

    local_settings_path = ROOT_DIR / "local.settings.json"

    with open(local_settings_path, "w") as f:
        json.dump(local_settings, f, indent=4)

    cmd = [
        "func", "azure", "functionapp", "publish", "func-nz-census-map-api",
        "--publish-settings-only", "--python",
    ]

    subprocess.run(cmd, check=True, cwd=ROOT_DIR)

    os.remove(local_settings_path)


def tf_destroy(yes_all=False):
    cmd = ["terraform", "destroy"]
    if yes_all:
        cmd.append("-auto-approve")

    subprocess.run(cmd, check=True, cwd=DEPLOY_DIR)


def tf_init():
    subprocess.run(["terraform", "init"], check=True, cwd=DEPLOY_DIR)


def tf_plan():
    subprocess.run(["terraform", "plan"], check=True, cwd=DEPLOY_DIR)


def tf_apply(yes_all=False):
    cmd = ["terraform", "apply"]
    if yes_all:
        cmd.append("-auto-approve")

    subprocess.run(cmd, check=True, cwd=DEPLOY_DIR)


def fn_deploy():
    try:
        # update_reqs_cmd = [
        #     sys.executable, "-m", "pipreqs.pipreqs", ROOT_DIR,
        #     "--savepath", ROOT_DIR / "requirements.txt", "--force",
        #     "--ignore", ".venv,deploy,scripts,data,__pycache__"
        # ]
        # subprocess.run(update_reqs_cmd, check=True, cwd=ROOT_DIR)

        deploy_cmd = ["func", "azure", "functionapp",
                      "publish", "func-nz-census-map-api", "--python"]
        subprocess.run(deploy_cmd, check=True, cwd=ROOT_DIR)
    finally:
        pass
        # with open(ROOT_DIR / "requirements.txt", "w") as f:
        #     pass
            # subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f,
            #                check=True, cwd=ROOT_DIR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run deployment")
    parser.add_argument("--init", "-i", action="store_true",
                        help="Run terraform init")
    parser.add_argument("--plan", "-p", action="store_true",
                        help="Run terraform plan")
    parser.add_argument("--apply", "-a", action="store_true",
                        help="Run terraform apply")
    parser.add_argument("--yes-all", "-y", action="store_true",
                        help="Run terraform apply with auto-approve")
    parser.add_argument("--destroy", "-d", action="store_true",
                        help="Run terraform destroy")
    parser.add_argument("--deploy-func", "-df", action="store_true",
                        help="Deploy the Azure Function App")

    args = parser.parse_args()

    if args.destroy:
        tf_destroy(yes_all=args.yes_all)

    if args.init:
        tf_init()

    if args.plan:
        tf_plan()

    if args.apply:
        tf_apply(yes_all=args.yes_all)

    if args.deploy_func:
        push_func_env()
        fn_deploy()
