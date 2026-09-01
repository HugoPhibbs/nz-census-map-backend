import subprocess
import os

def build_pmtiles():
    data_dir = os.path.join(os.getcwd(), "data")
    subprocess.run(
        f'docker run --rm -v "{data_dir}:/data" -w /data ubuntu:24.04 bash -c '
        '"apt update && apt install -y tippecanoe && '
        'tippecanoe -f -o ./area-boundaries.pmtiles -zg --drop-densest-as-needed '
        '--extend-zooms-if-still-dropping --coalesce-densest-as-needed '
        '-L ta:./geojson/territorial-authority-2023-clipped-generalised-adjusted.json '
        '-L sa3:./geojson/statistical-area-3-2023-clipped-generalised-adjusted.json '
        '-L sa2:./geojson/statistical-area-2-2023-clipped-generalised-adjusted.json '
        '-L coastline:./geojson/nz-coastlines-and-islands-polygons-topo-1250k.json"',
        shell=True,
    )

if __name__ == "__main__":
    build_pmtiles()