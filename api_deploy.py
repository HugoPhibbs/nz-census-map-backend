import argparse
import subprocess

def deploy_cloud_run():
    cmd = ["gcloud", "run", "deploy", "nz-census-map-api", "--source", ".", "--region", "europe-west2", "--allow-unauthenticated", "--env-vars-file=env.yaml"]
    
    subprocess.run(cmd, check=True, shell=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy the application to Google Cloud Run.")
    args = parser.parse_args()

    deploy_cloud_run()