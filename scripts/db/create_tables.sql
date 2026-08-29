CREATE TABLE IF NOT EXISTS AREAS(
    area_code TEXT,
    area_name TEXT,
    area_type TEXT,
    census_year INTEGER,
    PRIMARY KEY (area_code, census_year)
);

CREATE TABLE IF NOT EXISTS DEMOGRAPHIC_VARIABLES(
    variable_name TEXT PRIMARY KEY,
    variable_description TEXT,
    variable_unit TEXT
);

/*
For the area code, see:
https://www.stats.govt.nz/assets/Methods/Statistical-standard-for-geographic-areas-2023/statistical-standard-for-geographic-areas-2023-updated-december-2023.pdf
*/

CREATE TABLE IF NOT EXISTS DEMOGRAPHIC_VARIABLES(
    variable_name TEXT PRIMARY KEY,
    variable_description TEXT,
    variable_unit TEXT
);

CREATE TABLE IF NOT EXISTS DEMOGRAPHIC_DATA(
    area_code TEXT,
    census_year INTEGER,
    variable_name TEXT,
    variable_value NUMERIC,
    PRIMARY KEY (area_code, census_year, variable_name),
    FOREIGN KEY (area_code, census_year) REFERENCES AREAS(area_code, census_year) ON DELETE RESTRICT,
    FOREIGN KEY (variable_name) REFERENCES DEMOGRAPHIC_VARIABLES(variable_name) ON DELETE RESTRICT
);


