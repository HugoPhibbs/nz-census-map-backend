CREATE TABLE IF NOT EXISTS AREAS(
    area_code TEXT,
    area_name TEXT,
    area_type TEXT,
    census_year INTEGER,
    PRIMARY KEY (area_code, census_year)
);

CREATE TABLE IF NOT EXISTS DEMOGRAPHIC_VARIABLES(
    variable_id TEXT PRIMARY KEY,
    variable_unit TEXT,
    plain_name TEXT
);

/*
For the area code, see:
https://www.stats.govt.nz/assets/Methods/Statistical-standard-for-geographic-areas-2023/statistical-standard-for-geographic-areas-2023-updated-december-2023.pdf
*/

CREATE TABLE IF NOT EXISTS DEMOGRAPHIC_DATA(
    area_code TEXT,
    census_year INTEGER,
    variable_id TEXT,
    variable_value NUMERIC,
    PRIMARY KEY (area_code, census_year, variable_id),
    FOREIGN KEY (area_code, census_year) REFERENCES AREAS(area_code, census_year) ON DELETE RESTRICT,
    FOREIGN KEY (variable_id) REFERENCES DEMOGRAPHIC_VARIABLES(variable_id) ON DELETE RESTRICT
);

CREATE MATERIALIZED VIEW NATIONAL_PERCENTAGE_AVERAGES AS
                SELECT pct.variable_id, pct.census_year,
                    ROUND(SUM(pct.variable_value * pop.variable_value) / SUM(pop.variable_value), 2) AS national_avg
                FROM DEMOGRAPHIC_DATA pct
                JOIN DEMOGRAPHIC_DATA pop
                ON pop.area_code = pct.area_code
                AND pop.census_year = pct.census_year
                AND pop.variable_id = 'pop_resident_usual'
                WHERE SUBSTR(pct.variable_id, 1, 5) = 'perc_' AND LENGTH(pct.area_code) = 3
                GROUP BY pct.variable_id, pct.census_year LIMIT 100