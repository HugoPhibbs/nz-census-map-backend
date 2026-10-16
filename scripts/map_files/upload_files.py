import os
import subprocess

from scripts.map_files.build_pmtiles import (
    AREA_BOUNDARIES_SA1_PATH,
    AREA_BOUNDARIES_SA2_PATH,
    AREA_BOUNDARIES_SA3_PATH,
    AREA_BOUNDARIES_TA_PATH,
    COMBINED_BASEMAP_PATH,
)

def fill_bucket_with_data():
    files_to_upload = [
        COMBINED_BASEMAP_PATH,
        AREA_BOUNDARIES_SA1_PATH,
        AREA_BOUNDARIES_SA2_PATH,
        AREA_BOUNDARIES_SA3_PATH,
        AREA_BOUNDARIES_TA_PATH
    ]
    for file in files_to_upload:
        upload_cmd = [
            "gsutil", "cp", f"./data/{file}", f"gs://{os.environ['BUCKET_NAME']}/{file}"]
        subprocess.run(upload_cmd, check=True)