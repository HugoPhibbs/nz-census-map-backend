from psycopg.rows import dict_row

from src.utils import get_db_connection_pool

def all_variable_info():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM demographic_variables"
            )
            result = cur.fetchall()
            return result
    

def area_info(census_year: int, area_code: str):
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM areas WHERE census_year = %s AND area_code = %s",
                (census_year, area_code),
            )
            result = cur.fetchone()

            return result


def area_stats(census_year: int, area_code: str):
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM demographic_data WHERE census_year = %s AND area_code = %s",
                (census_year, area_code),
            )
            result = cur.fetchall()

    return result


def variable_averages(census_year: int):
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT variable_id, national_avg FROM NATIONAL_PERCENTAGE_AVERAGES WHERE census_year = %s",
                (census_year,),
            )
            result = cur.fetchall()
            return {row["variable_id"]: row["national_avg"] for row in result}
