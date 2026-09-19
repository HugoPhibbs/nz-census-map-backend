import io
import os
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

NS = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

STATS_BASE_URL = "https://api.data.stats.govt.nz/rest/data/STATSNZ,"

WEB_DOWNLOAD_FOLDER = "./data/web-download"

REGIONS_DATA = {  # topic name, metadata file, demographic data file (to merge into)
    "sa2-sa3-ta": ("CEN23_TBT_008,1.0", "topics-sa2-sa3-ta-2023.xml", "demographic_data_download.csv"),
    "sa1": ("CEN23_TBT_012,1.0", "topics-sa1-2023.xml", "demographic_data_download_sa1.csv")
}

GROUP_NAMES = [
    "seeing",
    "hearing",
    "walking",
    "remembering",
    "communicating",
    "smoking",
    "difficulty washing",
]

CENSUS_YEAR = 2023


def get_group_variables(group_name, xml_path):
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read().lstrip()

    root = ET.parse(io.StringIO(content)).getroot()

    group_id = None
    for code_el in root.iter(f"{{{NS['structure']}}}Code"):
        name_el = code_el.find("common:Name", NS)
        if name_el is not None and name_el.text and group_name.lower() in name_el.text.strip().lower():
            group_id = code_el.get("id")
            break

    if group_id is None:
        return []

    child_ids = []
    for code_el in root.iter(f"{{{NS['structure']}}}Code"):
        parent_el = code_el.find("structure:Parent/Ref", NS)
        if parent_el is not None and parent_el.get("id") == group_id:
            child_ids.append(code_el.get("id"))

    return child_ids


def get_variable_codes():
    codes = {}
    for region, data in REGIONS_DATA.items():
        _, xml_meta_data, _ = data
        xml_path = f"./data/meta-data/{xml_meta_data}"
        # print(region)

        children_codes = []
        for group_name in GROUP_NAMES:
            group_codes = get_group_variables(group_name, xml_path)
            # print(group_name, group_codes)
            children_codes.extend(group_codes)

        codes[region] = children_codes

    return codes


def fetch_data_for_region(region, variable_codes, year):
    topic_code, _, demographic_data_file = REGIONS_DATA[region]
    url = f"{STATS_BASE_URL}{topic_code}/{'+'.join(variable_codes)}..{year}"

    response = requests.get(url,
                            headers={
                                "Ocp-Apim-Subscription-Key": os.getenv("STATS_NZ_API_KEY")
                            },
                            params={"format": "csvfilewithlabels"}
                            )

    response.raise_for_status()

    new_df = pd.read_csv(io.StringIO(response.text), low_memory=False)
    existing_df = pd.read_csv(
        f"{WEB_DOWNLOAD_FOLDER}/{demographic_data_file}",
        low_memory=False
    )

    merged_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Drop duplicates so we can easily re-run this script
    merged_df = merged_df.drop_duplicates()

    merged_df.to_csv(
        f"{WEB_DOWNLOAD_FOLDER}/{demographic_data_file}", 
        index=False
    )


if __name__ == "__main__":
    variable_codes = get_variable_codes()

    for region, codes in variable_codes.items():
        print(
            f"Fetching data for region: {region} with {len(codes)} variable codes.")
        fetch_data_for_region(region, codes, CENSUS_YEAR)
