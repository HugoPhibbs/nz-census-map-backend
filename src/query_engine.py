from typing import Literal
import time

import psycopg
from psycopg.rows import dict_row, tuple_row
from pypika import Order, Query, Table

from src.utils import get_db_connection_pool

db_pool = get_db_connection_pool(autocommit=True)


def run_query(sql, params=None, *, as_dicts=False, fetch_one=False):
    """
    Runs a read query. If Neon has dropped the pool's connections (compute suspended), clears them and retries once.
    """
    def run():
        with db_pool.connection() as conn, conn.cursor(row_factory=dict_row if as_dicts else tuple_row) as cur:
            cur.execute(sql, params)
            return cur.fetchone() if fetch_one else cur.fetchall()

    try:
        start = time.perf_counter()
        res = run()
        print(f"Query took {(time.perf_counter() - start) * 1000:.2f} ms")
        return res
    except psycopg.OperationalError:
        # Catching OperationalError is a bit broad (includes PoolTimeout, QueryCanceled), but we can ignore for the scale of this project
        # At free tier, Neon drops connections after 5 minutes, so we need to account for this by retrying
        db_pool.check()
        return run()


def all_variable_info():
    return run_query("SELECT * FROM demographic_variables", as_dicts=True)

def area_info(area_id: str):
    return run_query(
        "SELECT * FROM areas WHERE area_id = %s", 
        (area_id,), 
        as_dicts=True, 
        fetch_one=True
        )


def area_stats(census_year: int, area_id: str):
    return run_query(
        "SELECT * FROM demographic_data WHERE census_year = %s AND area_id = %s",
        (census_year, area_id),
        as_dicts=True,
    )


def variable_ids_to_unit():
    return dict(run_query("SELECT variable_id, variable_unit FROM demographic_variables"))


def variable_averages(census_year: int):
    return dict(run_query(
        "SELECT variable_id, national_avg FROM NATIONAL_PERCENTAGE_AVERAGES WHERE census_year = %s",
        (census_year,),
    ))


def variable_ids_to_available_years():
    return dict(run_query("SELECT variable_id, available_years FROM demographic_variables"))


def variable_ids_to_name():
    return dict(run_query("SELECT variable_id, plain_name FROM demographic_variables"))

def area_bounding_box(area_id: str):
    bounding_box = run_query("SELECT bounding_box FROM areas WHERE area_id = %s", (area_id,), fetch_one=True)
    if bounding_box is None:
        return None
    return bounding_box[0]
    

def all_variable_ids():
    return [row[0] for row in run_query("SELECT variable_id FROM demographic_variables")]


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

    return dict(run_query(q.get_sql()))


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
            .on(demographic_data.area_id == areas.area_id)
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

    res = run_query(q.get_sql(), as_dicts=True)
    print(f"Query took {(time.perf_counter() - start) * 1000:.2f} ms")
    return res

def map_stats(variable_id, census_year=2023):
    return dict(run_query(
        """SELECT area_id, variable_value::float8
        FROM demographic_data
        WHERE variable_id = %s AND census_year = %s""",
        (variable_id, census_year),
    ))


def variable_compare(variable_id, year_from, year_to, method):
    if method == "delta":
        change_expr = "t.variable_value - f.variable_value"
    elif method == "perc":
        change_expr = "100.0 * (t.variable_value - f.variable_value) / NULLIF(f.variable_value, 0)"
    else:
        raise ValueError(f"Invalid method: {method}")
    
    return dict(run_query(
        f"""
        SELECT f.area_id, (ROUND({change_expr}, 2)::float8) AS change
        FROM demographic_data f
        JOIN demographic_data t
        ON t.area_id = f.area_id AND t.variable_id = f.variable_id
        WHERE f.variable_id = %s AND f.census_year = %s AND t.census_year = %s AND ({change_expr}) IS NOT NULL
        """,
        (variable_id, year_from, year_to),
    ))
