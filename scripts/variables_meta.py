from dataclasses import dataclass
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
    census_code: str
    variable_id: str
    variable_unit: VariableUnit = None
    plain_name: str = None
    keep: bool = True  # Whether to keep this variable in the final dataset, otherwise it's used for calculating percentages or other derived variables
    # If this variable is part of a group of variables that can be aggregated, this is the name of the group
    aggregate_group_id: str = None


@dataclass
class VariablePercentageMeta:
    base_variable_id: str
    variable_id: str
    plain_name: str = None
    variable_unit: VariableUnit = VariableUnit.PERCENTAGE


@dataclass
class VariableAggregateGroupMeta:
    group_id: str
    plain_name: str
    variable_unit: VariableUnit = VariableUnit.COUNT


VARIABLES = [
    VariableMeta(
        "ge3",
        "pop_another_gender",
        VariableUnit.COUNT,
        "Another gender population",
    ),
    VariableMeta(
        "eg4",
        "pop_ethnicity_asian",
        VariableUnit.COUNT,
        "Asian population",
    ),
    VariableMeta(
        "hwmea",
        "avg_hours_worked_per_week",
        VariableUnit.HOUR,
        "Average hours worked per week",
    ),
    VariableMeta(
        "cbmea",
        "avg_children_born",
        VariableUnit.RATE,
        "Average children born per woman",
    ),
    VariableMeta(
        "yumea",
        "avg_years_at_usual_residence",
        VariableUnit.YEAR,
        "Average years at usual residence",
    ),
    VariableMeta(
        "yamea",
        "avg_years_since_arrival_nz",
        VariableUnit.YEAR,
        "Average years since arrival in NZ",
    ),
    VariableMeta(
        "rc",
        "pop_resident_usual",
        VariableUnit.COUNT,
        "Usually resident population",
    ),
    VariableMeta(
        "eg1",
        "pop_ethnicity_european",
        VariableUnit.COUNT,
        "European population",
    ),
    VariableMeta(
        "ge2",
        "pop_gender_female",
        VariableUnit.COUNT,
        "Female (gender) population",
    ),
    VariableMeta(
        "sb22",
        "pop_sex_female",
        VariableUnit.COUNT,
        "Female (sex) population",
    ),
    VariableMeta(
        "ge1",
        "pop_gender_male",
        VariableUnit.COUNT,
        "Male (gender) population",
    ),
    VariableMeta(
        "sb11",
        "pop_sex_male",
        VariableUnit.COUNT,
        "Male (sex) population",
    ),
    VariableMeta(
        "ibmed",
        "median_personal_income",
        VariableUnit.NZD,
        "Median personal income",
    ),
    VariableMeta(
        "asMed",
        "median_age",
        VariableUnit.YEAR,
        "Median age",
    ),
    VariableMeta(
        "eg5",
        "pop_ethnicity_mela",
        VariableUnit.COUNT,
        "Middle Eastern/Latin American/African population",
    ),
    VariableMeta(
        "eg2",
        "pop_ethnicity_maori",
        VariableUnit.COUNT,
        "Māori population",
    ),
    VariableMeta(
        "md01",
        "pop_maori_descent",
        VariableUnit.COUNT,
        "Māori descent population",
    ),
    VariableMeta(
        "bi0",
        "pop_birthplace_nz",
        VariableUnit.COUNT,
        "NZ-born population",
    ),
    VariableMeta(
        "eg6",
        "pop_ethnicity_other",
        VariableUnit.COUNT,
        "Other ethnicity population",
    ),
    VariableMeta(
        "bi1",
        "pop_birthplace_overseas",
        VariableUnit.COUNT,
        "Overseas-born population",
    ),
    VariableMeta(
        "eg3",
        "pop_ethnicity_pacific",
        VariableUnit.COUNT,
        "Pacific Peoples population",
    ),
    VariableMeta(
        "cs01",
        "pop_regular_smoker",
        VariableUnit.COUNT,
        "Regular smoker population",
    ),
    VariableMeta(
        "dc02",
        "pop_difficulty_communicating_some",
        keep=False,
        aggregate_group_id="communicating_difficulty",
    ),
    VariableMeta(
        "dc03",
        "pop_difficulty_communicating_alot",
        keep=False,
        aggregate_group_id="communicating_difficulty",
    ),
    VariableMeta(
        "dc04",
        "pop_difficulty_communicating_cannot",
        keep=False,
        aggregate_group_id="communicating_difficulty",
    ),
    VariableMeta(
        "dh02",
        "pop_difficulty_hearing_some",
        keep=False,
        aggregate_group_id="hearing_difficulty",
    ),
    VariableMeta(
        "dh03",
        "pop_difficulty_hearing_alot",
        keep=False,
        aggregate_group_id="hearing_difficulty",
    ),
    VariableMeta(
        "dh04",
        "pop_difficulty_hearing_cannot",
        keep=False,
        aggregate_group_id="hearing_difficulty",
    ),
    VariableMeta(
        "dr02",
        "pop_difficulty_remembering_concentrating_some",
        keep=False,
        aggregate_group_id="remembering_concentrating_difficulty",
    ),
    VariableMeta(
        "dr03",
        "pop_difficulty_remembering_concentrating_alot",
        keep=False,
        aggregate_group_id="remembering_concentrating_difficulty",
    ),
    VariableMeta(
        "dr04",
        "pop_difficulty_remembering_concentrating_cannot",
        keep=False,
        aggregate_group_id="remembering_concentrating_difficulty",
    ),
    VariableMeta(
        "dw02",
        "pop_difficulty_walking_some",
        keep=False,
        aggregate_group_id="walking_difficulty",
    ),
    VariableMeta(
        "dw03",
        "pop_difficulty_walking_alot",
        keep=False,
        aggregate_group_id="walking_difficulty",
    ),
    VariableMeta(
        "dw04",
        "pop_difficulty_walking_cannot",
        keep=False,
        aggregate_group_id="walking_difficulty",
    ),
    VariableMeta(
        "dd02",
        "pop_difficulty_washing_some",
        keep=False,
        aggregate_group_id="washing_difficulty",
    ),
    VariableMeta(
        "dd03",
        "pop_difficulty_washing_alot",
        keep=False,
        aggregate_group_id="washing_difficulty",
    ),
    VariableMeta(
        "dd04",
        "pop_difficulty_washing_cannot",
        keep=False,
        aggregate_group_id="washing_difficulty",
    ),
    VariableMeta(
        "ds02",
        "pop_difficulty_seeing_some",
        keep=False,
        aggregate_group_id="seeing_difficulty",
    ),
    VariableMeta(
        "ds03",
        "pop_difficulty_seeing_alot",
        keep=False,
        aggregate_group_id="seeing_difficulty",
    ),
    VariableMeta(
        "ds04",
        "pop_difficulty_seeing_cannot",
        keep=False,
        aggregate_group_id="seeing_difficulty",
    ),
]

AGGREGATE_GROUPS = {
    "communicating_difficulty": VariableAggregateGroupMeta("pop_difficulty_communicating", plain_name="Difficulty communicating"),
    "hearing_difficulty": VariableAggregateGroupMeta("pop_difficulty_hearing", plain_name="Hearing difficulty"),
    "remembering_concentrating_difficulty": VariableAggregateGroupMeta("pop_difficulty_remembering_concentrating", plain_name="Remembering and concentrating difficulty"),
    "walking_difficulty": VariableAggregateGroupMeta("pop_difficulty_walking", plain_name="Walking difficulty"),
    "washing_difficulty": VariableAggregateGroupMeta("pop_difficulty_washing", plain_name="Washing difficulty"),
    "seeing_difficulty": VariableAggregateGroupMeta("pop_difficulty_seeing", plain_name="Seeing difficulty"),
}

# Percentage variables, derived from (observation count / resident population)
VARIABLES_PERCENTAGE = [
    VariablePercentageMeta(
        "pop_regular_smoker",
        "perc_regular_smoker",
        "Regular smoker (%)",
    ),
    VariablePercentageMeta(
        "pop_difficulty_communicating",
        "perc_difficulty_communicating",
        "Difficulty communicating (%)",
    ),
    VariablePercentageMeta(
        "pop_difficulty_hearing",
        "perc_difficulty_hearing",
        "Difficulty hearing (%)",
    ),
    VariablePercentageMeta(
        "pop_difficulty_remembering_concentrating",
        "perc_difficulty_remembering_concentrating",
        "Difficulty remembering and concentrating (%)",
    ),
    VariablePercentageMeta(
        "pop_difficulty_walking",
        "perc_difficulty_walking",
        "Difficulty walking (%)",
    ),
    VariablePercentageMeta(
        "pop_difficulty_washing",
        "perc_difficulty_washing",
        "Difficulty washing (%)",
    ),
    VariablePercentageMeta(
        "pop_difficulty_seeing",
        "perc_difficulty_seeing",
        "Difficulty seeing (%)",
    ),
    VariablePercentageMeta(
        "pop_maori_descent",
        "perc_maori_descent",
        "Maori descent (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_maori",
        "perc_ethnicity_maori",
        "Māori ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_pacific",
        "perc_ethnicity_pacific",
        "Pacific Peoples ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_other",
        "perc_ethnicity_other",
        "Other ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_another_gender",
        "perc_another_gender",
        "Another gender (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_asian",
        "perc_ethnicity_asian",
        "Asian ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_european",
        "perc_ethnicity_european",
        "European ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_gender_female",
        "perc_gender_female",
        "Female gender (%)",
    ),
    VariablePercentageMeta(
        "pop_sex_female",
        "perc_sex_female",
        "Female sex (%)",
    ),
    VariablePercentageMeta(
        "pop_gender_male",
        "perc_gender_male",
        "Male gender (%)",
    ),
    VariablePercentageMeta(
        "pop_sex_male",
        "perc_sex_male",
        "Male sex (%)",
    ),
    VariablePercentageMeta(
        "pop_ethnicity_mela",
        "perc_ethnicity_mela",
        "Middle Eastern/Latin American/African ethnicity (%)",
    ),
    VariablePercentageMeta(
        "pop_birthplace_nz",
        "perc_birthplace_nz",
        "NZ born (%)",
    ),
    VariablePercentageMeta(
        "pop_birthplace_overseas",
        "perc_birthplace_overseas",
        "Overseas born (%)",
    ),
]
