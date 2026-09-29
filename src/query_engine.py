from typing import Literal

from psycopg.rows import dict_row
from pypika import Order, Query, Table

from src.utils import get_db_connection_pool


def all_variable_info():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM demographic_variables")
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


def variable_ids_to_unit():
    with get_db_connection_pool().connection() as conn, conn.cursor() as cur:
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
    area_code: str, census_year: int, variable_ids_to_keep: list[str] | None = None
):
    t = Table("demographic_data")
    q = (
        Query.from_(t)
        .select(t.variable_id, t.variable_value)
        .where((t.area_code == area_code) & (t.census_year == census_year))
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
    drop_pop_data: bool = False,
    sort_order: Literal["asc", "desc"] | None = None,
    top_k: int | None = None,
):
    """
    Get all statistics for a specific demographic variable for a given census year.

    If top_k is provided, but sort_order is not, the top_k results will be returned only.
    """

    demographic_data = Table("demographic_data")

    q = (
        Query.from_(demographic_data)
        .select("*")
        .where(
            (demographic_data.variable_id == variable_id)
            & (demographic_data.census_year == census_year)
        )
    )

    if area_type:
        areas = Table("areas")
        q = (
            q.join(areas)
            .on(
                (demographic_data.area_code == areas.area_code)
                & (demographic_data.census_year == areas.census_year)
            )
            .where(areas.area_type == area_type)
        )

    if drop_pop_data:
        q = q.where(~demographic_data.variable_id.like("pop_%"))

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
            return cur.fetchall()
