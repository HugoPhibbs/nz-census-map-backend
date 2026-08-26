from flask import Flask
from flask_cors import CORS
import json
from flask import send_file
from waitress import serve

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

@app.route('/region/info/<region_id>')
def index(region_id):
    return f'Hello, World! Region ID: {region_id}'

@app.route('/area-boundaries.pmtiles')
def map():
    return send_file(
        "../data/area-boundaries.pmtiles", 
        mimetype='application/octet-stream',
        conditional =True
    )

if __name__ == '__main__':
    # app.run(debug=True, threaded=True)

    print("Running a production server...")
    serve(app, host='0.0.0.0', port=5000, threads = 4)