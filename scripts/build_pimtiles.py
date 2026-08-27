import subprocess
import os

def build_pmtiles():
    subprocess.run(
        f'docker run --rm -v "{os.getcwd()}:/data" -w /data ubuntu:24.04 bash -c '
        '"apt update && apt install -y tippecanoe && '
        'tippecanoe -f -o area-boundaries.pmtiles -zg --drop-densest-as-needed '
        '--extend-zooms-if-still-dropping --coalesce-densest-as-needed '
        '-L ta:territorial-authority-2023-clipped-generalised-adjusted.json '
        '-L sa3:statistical-area-3-2023-clipped-generalised-adjusted.json '
        '-L sa2:statistical-area-2-2023-clipped-generalised-adjusted.json '
        '-L coastline:nz-coastlines-and-islands-polygons-topo-1250k.json"',
        shell=True,
        cwd="./data",
    )

if __name__ == "__main__":
    build_pmtiles()