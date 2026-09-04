import subprocess
import os
import argparse

def fetch_basemap():
    data_dir = os.path.join(os.getcwd(), "data")
    subprocess.run(f'docker run --rm -v "{data_dir}:/data" protomaps/go-pmtiles extract https://build.protomaps.com/20260901.pmtiles /data/nz_basemap.pmtiles --bbox=165.673828,-47.338823,178.857422,-34.016242 --maxzoom=12', shell=True)
    subprocess.run(f'docker run --rm -v "{data_dir}:/data" protomaps/go-pmtiles extract https://build.protomaps.com/20260901.pmtiles /data/chatham_basemap.pmtiles --bbox=182.458497,-44.489317,184.315186,-43.501412 --maxzoom=12', shell=True)
    
    
def merge_geojson_to_pmtiles():
    data_dir = os.path.join(os.getcwd(), "data")
    subprocess.run(
        f'docker run --rm -v "{data_dir}:/data" -w /data ubuntu:24.04 bash -c '
        '"apt update && apt install -y tippecanoe && '
        'tippecanoe -f -o ./area_boundaries.pmtiles -z12 --drop-densest-as-needed '
        '--extend-zooms-if-still-dropping --coalesce-densest-as-needed '
        '-L ta:./geojson/territorial-authority-2023-clipped-generalised-adjusted.json '
        '-L sa3:./geojson/statistical-area-3-2023-clipped-generalised-adjusted.json '
        '-L sa2:./geojson/statistical-area-2-2023-clipped-generalised-adjusted.json '
        '-L coastline:./geojson/nz-coastlines-and-islands-polygons-topo-1250k.json"',
        shell=True,
    )
    
def merge_boundary_with_base_pmtiles():
    data_dir = os.path.join(os.getcwd(), "data")
    subprocess.run(
        f'docker run --rm -v "{data_dir}:/data" -w /data ubuntu:24.04 bash -c '
        '"apt update && apt install -y tippecanoe && '
        'mkdir -p /tmp/work && '
        'cp ./area_boundaries.pmtiles ./nz_basemap.pmtiles ./chatham_basemap.pmtiles /tmp/work/ && '
        'cd /tmp/work && '
        'tile-join -o combined.pmtiles area_boundaries.pmtiles nz_basemap.pmtiles chatham_basemap.pmtiles && '
        'cp combined.pmtiles /data/combined.pmtiles"',
        shell=True,
    )
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build PMTiles for NZ Census Map")
    parser.add_argument("--fetch-basemap", "-fb", action="store_true", help="Fetch the basemap PMTiles")
    parser.add_argument("--merge-geojson", "-mg", action="store_true", help="Build the boundary PMTiles")
    parser.add_argument("--merge-pmtiles", "-mp", action="store_true", help="Merge boundary and basemap PMTiles")
    parser.add_argument("--all", "-a", action="store_true", help="Run all steps")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        exit(1)
    
    if args.merge_geojson or args.all:
        merge_geojson_to_pmtiles()
        print("merging geojson done")
    
    if args.fetch_basemap or args.all:
        fetch_basemap()
        print("fetching basemap done")
    
    if args.merge_pmtiles or args.all:
        merge_boundary_with_base_pmtiles()
        print("merging pmtiles done")