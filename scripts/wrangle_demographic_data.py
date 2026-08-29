import pandas as pd

COLUMN_NAME_MAP = {
    "Area": "area_name",
    "CEN23_TBT_GEO_006": "area_id",
    "Census year": "census_year",
    "Another gender / He ira kē anō": "pop_another_gender",
    "Asian": "pop_ethinicity_asian",
    "Average - hours worked in employment per week": "avg_hours_worked_per_week",
    "Average - number of children born": "avg_birth_rate",
    "Average - years at usual residence": "avg_years_at_usual_residence",
    "Average - years since arrival in New Zealand": "avg_years_since_arrival_nz",
    "Census usually resident population count": "pop_resident_usual",
    "European": "pop_ethnicity_european",
    "Female / Wahine": "pop_gender_female",
    "Female/Wahine": "pop_sex_female",
    "Male / Tāne": "pop_gender_male",
    "Male/Tāne": "pop_sex_male",
    "Median ($) - total personal income": "median_personal_income",
    "Median - age": "median_age",
    "Middle Eastern/Latin American/African": "pop_ethnicity_mela",
    "Māori": "pop_ethnicity_maori",
    "Māori descent": "pop_maori_descent",
    "NZ born": "pop_birthplace_nz",
    "Number of children born - total sex at birth female census usually resident population count aged 15 years and over": "female_count_by_children_born_15plus",
    "Other ethnicity": "pop_ethnicity_other",
    "Overseas born": "pop_birthplace_overseas",
    "Pacific Peoples": "pop_ethnicity_pacific",
    # "Individual home ownership - total census usually resident population count aged 15 years and over": "pop_count_by_home_ownership_15plus",
    # "Individual unit data source - total census usually resident population count": "pop_count_by_data_source",
    # "Industry, by workplace address - total employed census usually resident population count aged 15 years and over": "employed_count_by_industry_15plus",
    # "Religious affiliation (total responses) - total census usually resident population count": "pop_count_by_religious_affiliation",
    # "Sex at birth - total census usually resident population count": "pop_count_by_sex",
    # "Total personal income - total census usually resident population count aged 15 years and over": "pop_count_by_personal_income_15plus",
    # "Work and labour force status - total census usually resident population count aged 15 years and over": "pop_count_by_labour_force_status_15plus",
    # "Highest qualification - total census usually resident population count aged 15 years and over": "pop_count_by_highest_qualification_15plus",
    # "Hours worked in employment per week - total employed census usually resident population count aged 15 years and over": "employed_count_by_hours_worked_15plus",
    # "Ethnicity (total responses) - total census usually resident population count": "pop_count_by_ethnicity",
    # "Birthplace (NZ born/overseas born) - total census usually resident population count": "pop_count_by_birthplace",
    # "Gender - total census usually resident population count": "pop_count_by_gender",
    # "Māori descent indicator - total census usually resident population count": "pop_count_by_maori_descent",
}


df = pd.read_csv("data/demographic_data.csv")
print(df.columns.tolist())  # sanity check

area_id_col = "CEN23_TBT_GEO_006"
year_col    = "Census year"
var_col     = "Variable codes"
value_col   = "OBS_VALUE"

df_long = df[[area_id_col, year_col, var_col, value_col]].rename(
    columns={
        area_id_col: "area_code",
        year_col: "census_year",
        var_col: "variable_name",
        value_col: "variable_value",
    }
)

# keep only variables we've deliberately mapped, and translate their names to your snake_case aliases
df_long = df_long[df_long["variable_name"].isin(COLUMN_NAME_MAP)].copy()
df_long["variable_name"] = df_long["variable_name"].map(COLUMN_NAME_MAP)

all_variable_names = pd.Series(df_long["variable_name"].unique())
all_variable_names.to_csv("data/all_variable_names.csv", index=False, header=False)

df_long.to_csv("data/demographic_data_long.csv", index=False)