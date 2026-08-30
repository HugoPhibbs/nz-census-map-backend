from dataclasses import asdict, dataclass

import pandas as pd
from enum import Enum


class VariableUnit(str, Enum):
    HOUR = "HOUR"
    COUNT = "COUNT"
    NZD = "NZD"
    YEAR = "YEAR"
    RATE = "RATE"


@dataclass
class VariableMeta:
    raw_name: str
    variable_name: str
    variable_description: str
    variable_unit: VariableUnit


VARIABLES = [
    VariableMeta(
        "Another gender / He ira kē anō",
        "pop_another_gender",
        "Population identifying as another gender",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Asian",
        "pop_ethinicity_asian",
        "Population identifying with Asian ethnicity",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Average - hours worked in employment per week",
        "avg_hours_worked_per_week",
        "Average hours worked in employment per week",
        VariableUnit.HOUR,
    ),
    VariableMeta(
        "Average - number of children born",
        "avg_children_born",
        "Average number of children born per woman",
        VariableUnit.RATE,
    ),
    VariableMeta(
        "Average - years at usual residence",
        "avg_years_at_usual_residence",
        "Average number of years lived at usual residence",
        VariableUnit.YEAR,
    ),
    VariableMeta(
        "Average - years since arrival in New Zealand",
        "avg_years_since_arrival_nz",
        "Average number of years since arrival in New Zealand",
        VariableUnit.YEAR,
    ),
    VariableMeta(
        "Census usually resident population count",
        "pop_resident_usual",
        "Total census usually resident population count",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "European",
        "pop_ethnicity_european",
        "Population identifying with European ethnicity",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Female / Wahine",
        "pop_gender_female",
        "Population identifying as female gender",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Female/Wahine",
        "pop_sex_female",
        "Population recorded as female sex at birth",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Male / Tāne",
        "pop_gender_male",
        "Population identifying as male gender",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Male/Tāne",
        "pop_sex_male",
        "Population recorded as male sex at birth",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Median ($) - total personal income",
        "median_personal_income",
        "Median total personal income",
        VariableUnit.NZD,
    ),
    VariableMeta(
        "Median - age",
        "median_age",
        "Median age of the population",
        VariableUnit.YEAR,
    ),
    VariableMeta(
        "Middle Eastern/Latin American/African",
        "pop_ethnicity_mela",
        "Population identifying with Middle Eastern, Latin American, or African ethnicity",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Māori",
        "pop_ethnicity_maori",
        "Population identifying with Māori ethnicity",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Māori descent",
        "pop_maori_descent",
        "Population reporting Māori descent",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "NZ born",
        "pop_birthplace_nz",
        "Population born in New Zealand",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Other ethnicity",
        "pop_ethnicity_other",
        "Population identifying with an ethnicity not otherwise listed",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Overseas born",
        "pop_birthplace_overseas",
        "Population born overseas",
        VariableUnit.COUNT,
    ),
    VariableMeta(
        "Pacific Peoples",
        "pop_ethnicity_pacific",
        "Population identifying with Pacific Peoples ethnicity",
        VariableUnit.COUNT,
    ),
]

df = pd.read_csv("data/web-download/demographic_data_download.csv")

area_id_col = "CEN23_TBT_GEO_006"
year_col    = "Census year"
var_col     = "Variable codes"
value_col   = "OBS_VALUE"

df = df[df["Observation Status"] != "Confidential"]

df = df[[area_id_col, year_col, var_col, value_col]].rename(
    columns={
        area_id_col: "area_code",
        year_col: "census_year",
        var_col: "variable_name",
        value_col: "variable_value",
    }
)

areas_table = pd.read_parquet("data/db-tables/areas_table.parquet")
unique_area_codes = areas_table["area_code"].unique()

df = df[df["area_code"].isin(unique_area_codes)]  # Remove non-area rows, somehow these slipped thru

VARIABLE_NAME_MAP = {v.raw_name: v.variable_name for v in VARIABLES}
df = df[df["variable_name"].isin(VARIABLE_NAME_MAP)]
df["variable_name"] = df["variable_name"].map(VARIABLE_NAME_MAP)

vars_rows = [asdict(v) for v in VARIABLES]
vars_df = pd.DataFrame(vars_rows)
vars_df = vars_df.drop(columns=["raw_name"])
vars_df.to_csv("data/db-tables/csv-debug/demographic_variables_table.csv", index=False)
vars_df.to_parquet("data/db-tables/demographic_variables_table.parquet", index=False)

df.to_csv("data/db-tables/csv-debug/demographic_data_table.csv", index=False)
df.to_parquet("data/db-tables/demographic_data_table.parquet", index=False)