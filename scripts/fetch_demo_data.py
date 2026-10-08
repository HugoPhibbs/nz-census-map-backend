import io
import os
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from dotenv import load_dotenv

from variables_meta import VARIABLES

load_dotenv()

NS = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

STATS_BASE_URL = "https://api.data.stats.govt.nz/rest/data/STATSNZ,"

WEB_DOWNLOAD_FOLDER = "./data/web-download"

AREA_DATA = {  # topic name, metadata file, demographic data file (to write/merge into)
    "sa2-sa3-ta": ("CEN23_TBT_008,1.0", "topics-sa2-sa3-ta-2023.xml", "demographic_data_download.csv"),
    "sa1": ("CEN23_TBT_012,1.0", "topics-sa1-2023.xml", "demographic_data_download_sa1.csv")
}



def fetch_and_save_data_for_area_group(area_group, variable_codes, years):
    topic_code, _, demographic_data_file = AREA_DATA[area_group]
    
    # existing_df = pd.read_csv(
    #     f"{WEB_DOWNLOAD_FOLDER}/{demographic_data_file}",
    #     low_memory=False
    # )
    
    new_df = pd.DataFrame()  # Initialize an empty DataFrame to hold new data

    for year in years:
        url = f"{STATS_BASE_URL}{topic_code}/{'+'.join(variable_codes)}..{year}"

        response = requests.get(url,
                                headers={
                                    "Ocp-Apim-Subscription-Key": os.getenv("STATS_NZ_API_KEY")
                                },
                                params={"format": "csvfilewithlabels"}
                                )

        response.raise_for_status()

        this_df = pd.read_csv(io.StringIO(response.text), low_memory=False)

        new_df = pd.concat([new_df, this_df], ignore_index=True)
    

    new_df.to_csv(f"{WEB_DOWNLOAD_FOLDER}/{demographic_data_file}_new", index=False)

if __name__ == "__main__":
    variable_codes = [v.census_code for v in VARIABLES]
    
    CENSUS_YEARS = [2013, 2018, 2023]

    for area_group in AREA_DATA:
        print(
            f"Fetching data for region group: {area_group} with {len(variable_codes)} variable codes.")
        fetch_and_save_data_for_area_group(area_group, variable_codes, CENSUS_YEARS)
