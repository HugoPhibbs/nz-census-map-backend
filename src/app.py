from flask import Flask, request
from flask_cors import CORS
from flask import send_file
from waitress import serve
from scripts.db_setup import get_db_connection_pool
from psycopg.rows import dict_row
from pypika import Query, Table

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


@app.route("/stats/region/<region_id>")
def get_region_stats(region_id):
    pass

@app.route("/stats/variable/names")
def get_all_variables():
    with get_db_connection_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT variable_name FROM demographic_variables")
            result = cur.fetchall()
            names = [row[0] for row in result]
            return names, 200

@app.route("/stats/variable/<variable>/<census_year>")
def get_all_regions_stats(variable, census_year):
    demographic_data = Table('demographic_data')

    q = Query.from_(demographic_data).select('*').where(
        demographic_data.variable_name == variable and demographic_data.census_year == census_year)

    if area_type := request.args.get('area_type'):
        areas = Table('areas')
        q = q.join(areas).on(
            (demographic_data.area_code == areas.area_code) &
            (demographic_data.census_year == areas.census_year)
        ).where(areas.area_type == area_type)

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
