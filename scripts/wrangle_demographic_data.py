from dataclasses import asdict, dataclass

import pandas as pd
from enum import Enum


class VariableUnit(str, Enum):
    HOUR = "HOUR"
    COUNT = "COUNT"
    NZD = "NZD"
    YEAR = "YEAR"
    RATE = "RATE"
    PERCENTAGE = "PERCENTAGE"


@dataclass
class VariableMeta:
    raw_name: str
    variable_id: str
    variable_unit: VariableUnit
    plain_name: str = None
    
@dataclass
class VariablePercentageMeta:
    base_variable_id: str
    variable_id: str
    variable_unit: VariableUnit
    plain_name: str = None


VARIABLES = [
    VariableMeta(
        "Another gender / He ira kē anō",
        "pop_another_gender",
        VariableUnit.COUNT,
        "Another gender population",
    ),
    VariableMeta(
        "Asian",
        "pop_ethnicity_asian",
        VariableUnit.COUNT,
        "Asian population",
    ),
    VariableMeta(
        "Average - hours worked in employment per week",
        "avg_hours_worked_per_week",
        VariableUnit.HOUR,
        "Average hours worked per week",
    ),
    VariableMeta(
        "Average - number of children born",
        "avg_children_born",
        VariableUnit.RATE,
        "Average children born per woman",
    ),
    VariableMeta(
        "Average - years at usual residence",
        "avg_years_at_usual_residence",
        VariableUnit.YEAR,
        "Average years at usual residence",
    ),
    VariableMeta(
        "Average - years since arrival in New Zealand",
        "avg_years_since_arrival_nz",
        VariableUnit.YEAR,
        "Average years since arrival in NZ",
    ),
    VariableMeta(
        "Census usually resident population count",
        "pop_resident_usual",
        VariableUnit.COUNT,
        "Usually resident population",
    ),
    VariableMeta(
        "European",
        "pop_ethnicity_european",
        VariableUnit.COUNT,
        "European population",
    ),
    VariableMeta(
        "Female / Wahine",
        "pop_gender_female",
        VariableUnit.COUNT,
        "Female (gender) population",
    ),
    VariableMeta(
        "Female/Wahine",
        "pop_sex_female",
        VariableUnit.COUNT,
        "Female (sex) population",
    ),
    VariableMeta(
        "Male / Tāne",
        "pop_gender_male",
        VariableUnit.COUNT,
        "Male (gender) population",
    ),
    VariableMeta(
        "Male/Tāne",
        "pop_sex_male",
        VariableUnit.COUNT,
        "Male (sex) population",
    ),
    VariableMeta(
        "Median ($) - total personal income",
        "median_personal_income",
        VariableUnit.NZD,
        "Median personal income",
    ),
    VariableMeta(
        "Median - age",
        "median_age",
        VariableUnit.YEAR,
        "Median age",
    ),
    VariableMeta(
        "Middle Eastern/Latin American/African",
        "pop_ethnicity_mela",
        VariableUnit.COUNT,
        "Middle Eastern/Latin American/African population",
    ),
    VariableMeta(
        "Māori",
        "pop_ethnicity_maori",
        VariableUnit.COUNT,
        "Māori population",
    ),
    VariableMeta(
        "Māori descent",
        "pop_maori_descent",
        VariableUnit.COUNT,
        "Māori descent population",
    ),
    VariableMeta(
        "NZ born",
        "pop_birthplace_nz",
        VariableUnit.COUNT,
        "NZ-born population",
    ),
    VariableMeta(
        "Other ethnicity",
        "pop_ethnicity_other",
        VariableUnit.COUNT,
        "Other ethnicity population",
    ),
    VariableMeta(
        "Overseas born",
        "pop_birthplace_overseas",
        VariableUnit.COUNT,
        "Overseas-born population",
    ),
    VariableMeta(
        "Pacific Peoples",
        "pop_ethnicity_pacific",
        VariableUnit.COUNT,
        "Pacific Peoples population",
    ),
]

VARIABLES_PERCENTAGE = [
    VariablePercentageMeta(
        "pop_maori_descent",
        "perc_maori_descent",
        VariableUnit.PERCENTAGE,
        "Maori descent (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_maori",
        "perc_ethnicity_maori",
        VariableUnit.PERCENTAGE,
        "Māori ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_pacific",
        "perc_ethnicity_pacific",
        VariableUnit.PERCENTAGE,
        "Pacific Peoples ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_other",
        "perc_ethnicity_other",
        VariableUnit.PERCENTAGE,
        "Other ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_another_gender",
        "perc_another_gender",
        VariableUnit.PERCENTAGE,
        "Another gender (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_asian",
        "perc_ethnicity_asian",
        VariableUnit.PERCENTAGE,
        "Asian ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_european",
        "perc_ethnicity_european",
        VariableUnit.PERCENTAGE,
        "European ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_gender_female",
        "perc_gender_female",
        VariableUnit.PERCENTAGE,
        "Female gender (%)",
    ),
    VariablePercentageMeta(
        "pop_sex_female",
        "perc_sex_female",
        VariableUnit.PERCENTAGE,
        "Female sex (%)",
    ),
    VariablePercentageMeta(
        "pop_gender_male",
        "perc_gender_male",
        VariableUnit.PERCENTAGE,
        "Male gender (%)",
    ),
    VariablePercentageMeta(
        "pop_sex_male",
        "perc_sex_male",
        VariableUnit.PERCENTAGE,
        "Male sex (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_mela",
        "perc_ethnicity_mela",
        VariableUnit.PERCENTAGE,
        "Middle Eastern/Latin American/African ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_birthplace_nz",
        "perc_birthplace_nz",
        VariableUnit.PERCENTAGE,
        "NZ born (%)",
    ),
    VariablePercentageMeta(
        "pop_birthplace_overseas",
        "perc_birthplace_overseas",
        VariableUnit.PERCENTAGE,
        "Overseas born (%)",
    ),
]

def add_perc_data(demo_df):
    name_map = {pm.base_variable_id: pm.variable_id for pm in VARIABLES_PERCENTAGE}

    pop_resident_df = demo_df[demo_df["variable_id"] == "pop_resident_usual"][
        ["area_code", "census_year", "variable_value"]
    ].rename(columns={"variable_value": "resident_value"})

    base_df = demo_df[demo_df["variable_id"].isin(name_map)].copy()

    merged = base_df.merge(
        pop_resident_df, on=["area_code", "census_year"], how="inner"
    )
    merged = merged[merged["resident_value"].notna() & (merged["resident_value"] != 0)]

    merged["variable_value"] = merged["variable_value"] / merged["resident_value"] * 100
    merged["variable_id"] = merged["variable_id"].map(name_map)
    merged = merged.drop(columns=["resident_value"])

    demo_df = pd.concat([demo_df, merged], ignore_index=True)
    
    return demo_df


def load_and_clean_df(path, area_id_col="CEN23_TBT_GEO_006"):
    demo_df = pd.read_csv(path, low_memory=False)

    year_col    = "Census year"
    var_col     = "Variable codes"
    value_col   = "OBS_VALUE"

    demo_df = demo_df[demo_df["Observation Status"] != "Confidential"]

    demo_df = demo_df[[area_id_col, year_col, var_col, value_col]].rename(
        columns={
            area_id_col: "area_code",
            year_col: "census_year",
            var_col: "variable_id",
            value_col: "variable_value",
        }
    )
    
    return demo_df

def remove_non_area_rows(demo_df):
    areas_table = pd.read_parquet("data/db-tables/areas_table.parquet")
    unique_area_codes = areas_table["area_code"].unique()

    demo_df = demo_df[demo_df["area_code"].isin(unique_area_codes)]  # Remove non-area rows, somehow these slipped thru
    
    return demo_df

def rename_variables(demo_df):
    VARIABLE_ID_MAP = {v.raw_name: v.variable_id for v in VARIABLES}
    demo_df = demo_df[demo_df["variable_id"].isin(VARIABLE_ID_MAP)]
    demo_df["variable_id"] = demo_df["variable_id"].map(VARIABLE_ID_MAP)
    
    return demo_df

def create_and_save_variables_table():
    base_vars_rows = [asdict(v) for v in VARIABLES]
    for row in base_vars_rows:
        del row["raw_name"]
        
    perc_rows = [asdict(pct) for pct in VARIABLES_PERCENTAGE]
    for row in perc_rows:
        del row["base_variable_id"]
    
    vars_df = pd.DataFrame(base_vars_rows + perc_rows)
    vars_df.to_csv("data/db-tables/csv-debug/demographic_variables_table.csv", index=False)
    vars_df.to_parquet("data/db-tables/demographic_variables_table.parquet", index=False)
    
def save_demo_df(demo_df):
    demo_df.to_csv("data/db-tables/csv-debug/demographic_data_table.csv", index=False)
    demo_df.to_parquet("data/db-tables/demographic_data_table.parquet", index=False)
    
def remove_inland_water_areas_from_demo_df(demo_df):
    inland_water_areas_df = pd.read_csv("./data/db-tables/inland_water_areas.csv")
    
    demo_df = demo_df.merge(
        inland_water_areas_df,
        on=["area_code", "census_year"],
        how="left",
        indicator=True,
    )
    demo_df = demo_df[demo_df["_merge"] == "left_only"].drop(columns="_merge")
    
    return demo_df
    
    
if __name__ == "__main__":    
    demo_df = load_and_clean_df("data/web-download/demographic_data_download.csv")
    demo_s1_df = load_and_clean_df("data/web-download/demographic_data_download_sa1.csv", area_id_col="CEN23_TBT_GEO_002")
    
    demo_df = pd.concat([demo_df, demo_s1_df], ignore_index=True)
    
    demo_df = remove_non_area_rows(demo_df)
    demo_df = rename_variables(demo_df)
    demo_df = add_perc_data(demo_df)
    
    demo_df["variable_value"] = demo_df["variable_value"].round(2)
    
    create_and_save_variables_table()
    save_demo_df(demo_df)