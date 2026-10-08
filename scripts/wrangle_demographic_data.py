from dataclasses import asdict

import anthropic
import pandas as pd
from dotenv import load_dotenv
from variables_meta import AGGREGATE_GROUPS, VARIABLES, VARIABLES_PERCENTAGE

load_dotenv() # For Anthropic API key
ai_client = anthropic.Anthropic()

def load_and_clean_df(path, area_id_col="CEN23_TBT_GEO_006"):
    demo_df = pd.read_csv(path, low_memory=False)

    year_col    = "Census year"
    var_col     = "CEN23_TBT_IND_003"
    value_col   = "OBS_VALUE"

    demo_df = demo_df[demo_df["Observation Status"] != "Confidential"]

    demo_df = demo_df[[area_id_col, year_col, var_col, value_col]].rename(
        columns={
            area_id_col: "area_id",
            year_col: "census_year",
            var_col: "variable_id",
            value_col: "variable_value",
        }
    )
    
    return demo_df

def aggregate_health_data(demo_df):
    demo_df = demo_df.copy()
    
    var_to_group = {
        v.variable_id: v.aggregate_group_id
        for v in VARIABLES
        if v.aggregate_group_id is not None
    }
    
    is_grouped = demo_df["variable_id"].isin(var_to_group)
    grouped_rows = demo_df[is_grouped].copy()
    grouped_rows["aggregate_group_id"] = grouped_rows["variable_id"].map(var_to_group)

    summed = (
        grouped_rows
        .groupby(["area_id", "census_year", "aggregate_group_id"], as_index=False)
        .agg(variable_value=("variable_value", "sum"), n_present=("variable_value", "count"))
    )

    group_sizes = pd.Series(var_to_group).value_counts()
    summed = summed[summed["n_present"] == summed["aggregate_group_id"].map(group_sizes)]
    summed = summed.drop(columns="n_present")

    summed["variable_id"] = summed["aggregate_group_id"].map(
        lambda gid: AGGREGATE_GROUPS[gid].group_id
    )
    
    # Above code: drop any data variables (particularly health-related), where
    # The total number of occurences is below the amount that we are looking for (e.g. if there are dropped rows, then we don't want to include the aggregate row either, as it will be misleading)
    
    summed = summed.drop(columns="aggregate_group_id")

    demo_df = pd.concat([demo_df[~is_grouped], summed], ignore_index=True)
    
    return demo_df
    

def add_perc_data(demo_df):
    name_map = {pm.base_variable_id: pm.variable_id for pm in VARIABLES_PERCENTAGE}

    pop_resident_df = demo_df[demo_df["variable_id"] == "pop_resident_usual"][
        ["area_id", "census_year", "variable_value"]
    ].rename(columns={"variable_value": "resident_value"})

    base_df = demo_df[demo_df["variable_id"].isin(name_map)].copy()

    merged = base_df.merge(
        pop_resident_df, on=["area_id", "census_year"], how="inner"
    )
    merged = merged[merged["resident_value"].notna() & (merged["resident_value"] != 0)]

    merged["variable_value"] = merged["variable_value"] / merged["resident_value"] * 100
    merged["variable_id"] = merged["variable_id"].map(name_map)
    merged = merged.drop(columns=["resident_value"])

    demo_df = pd.concat([demo_df, merged], ignore_index=True)
    
    return demo_df

def remove_non_area_rows(demo_df):
    areas_table = pd.read_parquet("data/db-tables/areas_table.parquet")
    unique_area_ids = areas_table["area_id"].unique()

    demo_df = demo_df[demo_df["area_id"].isin(unique_area_ids)]  # Remove non-area rows, somehow these slipped thru
    
    return demo_df

def rename_variables(demo_df):
    VARIABLE_ID_MAP = {v.census_code: v.variable_id for v in VARIABLES}
    demo_df = demo_df[demo_df["variable_id"].isin(VARIABLE_ID_MAP)]
    demo_df["variable_id"] = demo_df["variable_id"].map(VARIABLE_ID_MAP)
    
    return demo_df

def add_variable_descriptions(var_df):
    descriptions = []
    
    def gennerate_description(row):
        response = ai_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system="""
                You're given database row from a census variable data base. 
                
                Each row has three keys, values: variable_id, variable_unit and plain_name. 
                
                Your task is to generate a short, clear, and concise description of the variable.
                
                Respond with this description and nothing else. Unless you are stumped, then return NONE
                
                E.g. "variable_id: pop_resident_usual, variable_unit: COUNT, plain_name: Usually Resident Population" => "The total number of people who usually live in the area, according to the census."
                
                IMPORTANT: Handling health-related variables:
                e.g. id="perc_difficulty_hearing", this is percentage of people who have any trouble at all with hearing, so include this in the description. For example, "Percentage of people who have any difficulty hearing".
            """,
            messages=[{"role": "user", "content": str(row)}]
        )
        
        return response.content[0].text
    
    for row in var_df.itertuples(index=False):
        row_dict = row._asdict()
        description = gennerate_description(row_dict)
        
        if description == "NONE":
            raise ValueError(f"AI could not generate a description for variable_id: {row_dict['variable_id']}")
        descriptions.append(description)
        
    var_df["description"] = descriptions
    return var_df
        

def create_and_save_variables_table():
    base_vars_rows = [asdict(v) for v in VARIABLES]
    base_vars_rows = [row for row in base_vars_rows if row["keep"] == True]
    
    for row in base_vars_rows:
        del row["census_code"]
        del row["keep"]
        del row["aggregate_group_id"]
        
    aggregate_groups_rows = [asdict(agg) for agg in AGGREGATE_GROUPS.values()]
    
    for row in aggregate_groups_rows:
        group_id = row["group_id"]
        row["variable_id"] = group_id
        del row["group_id"]
        
    perc_rows = [asdict(pct) for pct in VARIABLES_PERCENTAGE]
    for row in perc_rows:
        del row["base_variable_id"]
    
    vars_df = pd.DataFrame(base_vars_rows + perc_rows + aggregate_groups_rows)
    
    vars_df = add_variable_descriptions(vars_df)
    
    vars_df.to_csv("data/db-tables/csv-debug/demographic_variables_table.csv", index=False)
    vars_df.to_parquet("data/db-tables/demographic_variables_table.parquet", index=False)
    
    
def remove_inland_water_areas_from_demo_df(demo_df: pd.DataFrame):
    inland_water_codes = pd.read_csv("./data/db-tables/inland_water_areas.csv", header=None, dtype=str)[0]
    return demo_df[~demo_df["area_id"].isin(inland_water_codes)]

def drop_intermediary_rows(demo_df):
    for variable in VARIABLES:
        if variable.keep == False:
            demo_df = demo_df[demo_df["variable_id"] != variable.variable_id]

    return demo_df

def drop_missing_rows(demo_df):
    demo_df = demo_df[demo_df["variable_value"].notna()] # Just incase any sneaked through
    return demo_df

def save_demo_df(demo_df):
    demo_df.to_csv("data/db-tables/csv-debug/demographic_data_table.csv", index=False)
    demo_df.to_parquet("data/db-tables/demographic_data_table.parquet", index=False)

if __name__ == "__main__":    
    demo_df = load_and_clean_df("data/web-download/demographic_data_download.csv_new")
    demo_s1_df = load_and_clean_df("data/web-download/demographic_data_download_sa1.csv_new", area_id_col="CEN23_TBT_GEO_002")
    
    demo_df = pd.concat([demo_df, demo_s1_df], ignore_index=True)
    
    demo_df = remove_non_area_rows(demo_df)
    demo_df = rename_variables(demo_df)
    demo_df = remove_inland_water_areas_from_demo_df(demo_df)
    demo_df = aggregate_health_data(demo_df)
    demo_df = add_perc_data(demo_df)
    demo_df = drop_intermediary_rows(demo_df)
    demo_df = drop_missing_rows(demo_df)
    
    demo_df["variable_value"] = demo_df["variable_value"].round(2)
    
    create_and_save_variables_table()
    save_demo_df(demo_df)
