from typing import Literal
import time

from psycopg.rows import dict_row
from pypika import Order, Query, Table

from src.utils import get_db_connection_pool


def all_variable_info():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM demographic_variables")
            result = cur.fetchall()
            return result


def area_info(area_id: str):
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM areas WHERE area_id = %s",
                (area_id,),
            )
            result = cur.fetchone()

            return result


def area_stats(census_year: int, area_id: str):
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM demographic_data WHERE census_year = %s AND area_id = %s",
                (census_year, area_id),
            )
            result = cur.fetchall()

    return result


def variable_ids_to_unit():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT variable_id, variable_unit FROM demographic_variables")
            result = cur.fetchall()
            return {row[0]: row[1] for row in result}


def variable_averages(census_year: int):
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT variable_id, national_avg FROM NATIONAL_PERCENTAGE_AVERAGES WHERE census_year = %s",
                (census_year,),
            )
            result = cur.fetchall()
            return {row["variable_id"]: row["national_avg"] for row in result}


def variable_ids_to_name():
    with get_db_connection_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT variable_id, plain_name FROM demographic_variables")
        result = cur.fetchall()
        return {row[0]: row[1] for row in result}


def all_variable_ids():
    with get_db_connection_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT variable_id FROM demographic_variables")
        result = cur.fetchall()
        return [row[0] for row in result]


def variable_values_for_area(
    area_id: str, census_year: int, variable_ids_to_keep: list[str] | None = None
):
    t = Table("demographic_data")
    q = (
        Query.from_(t)
        .select(t.variable_id, t.variable_value)
        .where((t.area_id == area_id) & (t.census_year == census_year))
    )

    if variable_ids_to_keep is not None:
        q = q.where(t.variable_id.isin(variable_ids_to_keep))

    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q.get_sql())
            result = cur.fetchall()
            return {r["variable_id"]: r["variable_value"] for r in result}


def all_variable_stats(
    variable_id,
    census_year=2023,
    area_type=None,
    sort_order: Literal["asc", "desc"] | None = None,
    top_k: int | None = None,
):
    """
    Get all statistics for a specific demographic variable for a given census year.

    If top_k is provided, but sort_order is not, the top_k results will be returned only.
    """
    
    start = time.perf_counter()

    demographic_data = Table("demographic_data")

    q = (
        Query.from_(demographic_data)
        .select("variable_value", "area_id")
        .where(
            (demographic_data.variable_id == variable_id)
            & (demographic_data.census_year == census_year)
        )
    )

    if area_type:
        areas = Table("AREAS")
        q = (
            q.join(areas)
            .on(
                demographic_data.area_id == areas.area_id
            )
            .where(areas.area_type == area_type)
        )

    if top_k is not None and sort_order is None:
        sort_order = "desc"

    if sort_order:
        q = q.where(demographic_data.variable_value.notnull()).orderby(
            demographic_data.variable_value,
            order=Order.desc if sort_order == "desc" else Order.asc,
        )

    if top_k is not None:
        q = q.limit(top_k)

    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q.get_sql())
            res = cur.fetchall()
            print(f"Query took {(time.perf_counter() - start) * 1000:.2f} ms")
            return res

def map_stats(variable_id, census_year=2023):
    with get_db_connection_pool().connection() as conn:
        with conn.cursor() as cur:
            # Casting to float8 here allows for faster serialiation to JSON without going thru Python's Decimal type.
            cur.execute(
                "SELECT area_id, variable_value::float8 FROM demographic_data WHERE variable_id = %s AND census_year = %s",
                (variable_id, census_year),
            )
            return cur.fetchall()