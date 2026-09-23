import os
import hmac

from dotenv import load_dotenv
from flask import Flask, request
from flask_caching import Cache
from flask_cors import CORS
from psycopg.rows import dict_row
from pypika import Query, Table

from src.utils import get_db_connection_pool

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", os.getenv("FRONTEND_DOMAIN")])

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

BEARER_TOKEN = os.getenv('BEARER_TOKEN')
if not BEARER_TOKEN:
    raise ValueError("BEARER_TOKEN environment variable is not set. Please set it in your .env file.")

EXPECTED_AUTH = f"Bearer {os.getenv('BEARER_TOKEN')}".encode()

@app.before_request
def check_auth():
    if request.method == 'OPTIONS':
        return 

    provided_auth = request.headers.get('Authorization', '').encode()
    
    if not hmac.compare_digest(provided_auth, EXPECTED_AUTH):
        return {"error": "Unauthorized"}, 401

@app.route("/area")
@cache.cached(query_string=True)
def get_area_info():
    census_year = request.args.get('census_year')
    area_code = request.args.get('area_code')

    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM areas WHERE census_year = %s AND area_code = %s",
                (census_year, area_code)
            )
            result = cur.fetchone()
            if result is None:
                return {"error": "Area not found"}, 404
            return result, 200


@app.route("/stats/area")
@cache.cached(query_string=True)
def get_region_stats():
    census_year = request.args.get('census_year')
    area_code = request.args.get('area_code')

    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM demographic_data WHERE census_year = %s AND area_code = %s",
                (census_year, area_code)
            )
            result = cur.fetchall()
            return result, 200


@app.route("/stats/variable/avgs")
@cache.cached(timeout=3600)
def get_variable_avgs():
    census_year = request.args.get('census_year', 2023)
    
    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT variable_id, national_avg FROM NATIONAL_PERCENTAGE_AVERAGES WHERE census_year = %s",
                (census_year,)
            )
            result = cur.fetchall()
            return {row["variable_id"]: row["national_avg"] for row in result}, 200


@app.route("/stats/variable/ids/to-unit")
@cache.cached()
def get_variable_ids_to_unit():
    with get_db_connection_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT variable_id, variable_unit FROM demographic_variables"
        )
        result = cur.fetchall()
        return {row[0]: row[1] for row in result}, 200


@app.route("/stats/variable/ids/to-name")
@cache.cached()
def get_variable_ids_to_name():
    with get_db_connection_pool().connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT variable_id, plain_name FROM demographic_variables")
        result = cur.fetchall()
        return {row[0]: row[1] for row in result}, 200


@app.route("/stats/variable/ids")
@cache.cached()
def get_all_variables():
    with get_db_connection_pool().connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT variable_id FROM demographic_variables")
        result = cur.fetchall()
        names = [row[0] for row in result]
        return names, 200


@app.route("/stats/variable/<variable_id>/<census_year>")
@cache.cached(query_string=True)
def get_all_regions_stats(variable_id, census_year):
    drop_pop_data = request.args.get(
        'drop_pop_data', 'false').lower() == 'true'

    demographic_data = Table('demographic_data')

    q = Query.from_(demographic_data).select('*').where(
        (demographic_data.variable_id == variable_id)
        & (demographic_data.census_year == census_year))

    if area_type := request.args.get('area_type'):
        areas = Table('areas')
        q = q.join(areas).on(
            (demographic_data.area_code == areas.area_code) &
            (demographic_data.census_year == areas.census_year)
        ).where(areas.area_type == area_type)

    if drop_pop_data:
        q = q.where(~demographic_data.variable_id.like("pop_%"))

    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q.get_sql())
            result = cur.fetchall()
            return result, 200

if __name__ == '__main__':
    print("Running a production server at http://localhost:5000")
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000, threads=4)
