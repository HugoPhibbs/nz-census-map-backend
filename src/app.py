import os

from flask import Flask, redirect, request
from flask_cors import CORS
from waitress import serve
from src.utils import get_db_connection_pool
from psycopg.rows import dict_row
from pypika import Query, Table
from google.cloud import storage
from datetime import timedelta
import google.auth
import google.auth.transport.requests

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", os.getenv("FRONTEND_DOMAIN")])


@app.before_request
def check_auth():
    if request.path.startswith('/pmtiles/'):
        return
    if request.headers.get('Authorization') != f"Bearer {os.getenv('BEARER_TOKEN')}":
        return {"error": "Unauthorized"}, 401


@app.route("/hello-world")
def hello_world():
    return {"message": "Hello, World!"}, 200


@app.route("/area")
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


@app.route("/stats/variable/ids/to-unit")
def get_variable_ids_to_unit():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT variable_id, variable_unit FROM demographic_variables")
            result = cur.fetchall()
            return {row[0]: row[1] for row in result}, 200


@app.route("/stats/variable/ids/to-name")
def get_variable_ids_to_name():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT variable_id, plain_name FROM demographic_variables")
            result = cur.fetchall()
            return {row[0]: row[1] for row in result}, 200


@app.route("/stats/variable/ids")
def get_all_variables():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT variable_id FROM demographic_variables")
            result = cur.fetchall()
            names = [row[0] for row in result]
            return names, 200


@app.route("/stats/variable/<variable_id>/<census_year>")
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


@app.route("/pmtiles/<file_name>")
def get_signed_url(file_name):
    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())
    
    storage_client = storage.Client()
    blob = storage_client.bucket(os.getenv("BUCKET_NAME")).blob(file_name)
    url = blob.generate_signed_url(
        expiration=timedelta(minutes=15),
        # Tell service account to use its own credentials to sign the URL
        service_account_email=credentials.service_account_email, 
        access_token=credentials.token,
    )

    return redirect(url, code=302)


if __name__ == '__main__':
    print("Running a production server at http://localhost:5000")
    serve(app, host='0.0.0.0', port=5000, threads=4)
