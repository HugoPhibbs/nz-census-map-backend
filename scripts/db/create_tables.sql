CREATE TABLE IF NOT EXISTS AREAS(
    area_id TEXT PRIMARY KEY,
    area_name TEXT,
    area_type TEXT
);

CREATE TABLE IF NOT EXISTS DEMOGRAPHIC_VARIABLES(
    variable_id TEXT PRIMARY KEY,
    variable_unit TEXT,
    plain_name TEXT,
    available_years INTEGER[],
    description TEXT
);

/*
For the area code, see:
https://www.stats.govt.nz/assets/Methods/Statistical-standard-for-geographic-areas-2023/statistical-standard-for-geographic-areas-2023-updated-december-2023.pdf
*/

CREATE TABLE IF NOT EXISTS DEMOGRAPHIC_DATA(
    area_id TEXT,
    census_year INTEGER,
    variable_id TEXT,
    variable_value NUMERIC,
    PRIMARY KEY (area_id, census_year, variable_id),
    FOREIGN KEY (area_id) REFERENCES AREAS(area_id) ON DELETE RESTRICT,
    FOREIGN KEY (variable_id) REFERENCES DEMOGRAPHIC_VARIABLES(variable_id) ON DELETE RESTRICT
);

-- This gives an index for fetching variable data for the frontend UI
CREATE INDEX IF NOT EXISTS idx_demographic_var_year
ON demographic_data (variable_id, census_year) INCLUDE (area_id, variable_value);

-- CREATE MATERIALIZED VIEW IF NOT EXISTS NATIONAL_PERCENTAGE_AVERAGES AS
--                 SELECT pct.variable_id, pct.census_year,
--                     ROUND(SUM(pct.variable_value * pop.variable_value) / SUM(pop.variable_value), 2) AS national_avg
--                 FROM DEMOGRAPHIC_DATA pct
--                 JOIN DEMOGRAPHIC_DATA pop
--                 ON pop.area_id = pct.area_id
--                 AND pop.census_year = pct.census_year
--                 AND pop.variable_id = 'pop_resident_usual'
--                 WHERE SUBSTR(pct.variable_id, 1, 5) = 'perc_' AND LENGTH(pct.area_id) = 3
--                 GROUP BY pct.variable_id, pct.census_year

CREATE MATERIALIZED VIEW IF NOT EXISTS NATIONAL_PERCENTAGE_AVERAGES AS
                SELECT pct.variable_id, pct.census_year,
                    ROUND(SUM(pct.variable_value * pop.variable_value) / SUM(pop.variable_value), 2) AS national_avg
                FROM DEMOGRAPHIC_DATA pct
                JOIN DEMOGRAPHIC_DATA pop
                ON pop.area_id = pct.area_id
                AND pop.census_year = pct.census_year
                AND pop.variable_id = 'pop_resident_usual'
                WHERE SUBSTR(pct.variable_id, 1, 5) = 'perc_' AND LENGTH(pct.area_id) = 3
                GROUP BY pct.variable_id, pct.census_year LIMIT 100