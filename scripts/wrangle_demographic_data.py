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

# sanity check — confirm the exact column names before pivoting
print(df.columns.tolist())

area_col  = "Area" 
area_id_col = "CEN23_TBT_GEO_006"    
year_col  = "Census year" 
var_col   = "Variable codes" 
value_col = "OBS_VALUE"

wide = df.pivot_table(
    index=[area_col, area_id_col, year_col],
    columns=var_col,
    values=value_col,
    aggfunc="first"   # see note below
).reset_index()

wide.columns.name = None   # tidy up the column index name pandas adds

cols_to_keep = [c for c in wide.columns if c in COLUMN_NAME_MAP]  # only mapped originals
wide = wide[cols_to_keep].rename(columns=COLUMN_NAME_MAP)

wide.to_csv("data/demographic_data_formatted.csv", index=False)