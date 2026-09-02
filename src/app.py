from flask import Flask, request
from flask_cors import CORS
from flask import send_file
from waitress import serve
from scripts.db_setup import get_db_connection_pool
from psycopg.rows import dict_row
from pypika import Query, Table

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

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
            cur.execute("SELECT variable_id, variable_unit FROM demographic_variables")
            result = cur.fetchall()
            return {row[0]: row[1] for row in result}, 200
        
@app.route("/stats/variable/ids/to-name")
def get_variable_ids_to_name():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT variable_id, plain_name FROM demographic_variables")
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
    drop_pop_data = request.args.get('drop_pop_data', 'false').lower() == 'true'
    
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


@app.route('/area-boundaries.pmtiles')
def map():
    return send_file(
        "../data/area-boundaries.pmtiles",
        mimetype='application/octet-stream',
        conditional=True
    )


if __name__ == '__main__':
    # app.run(debug=True, threaded=True)

    print("Running a production server at http://localhost:5000")
    serve(app, host='0.0.0.0', port=5000, threads=4)
    