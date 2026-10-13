import argparse
import os
import subprocess

DATA_DIR_LOCAL = os.path.join(os.getcwd(), "data")

# Paths relative to /data, valid inside every container
format_pmtiles_path = lambda f: f"pmtiles/{f}.pmtiles"
format_geojson_path = lambda f: f"geojson/{f}.json"

BASEMAP_MAINLAND_PATH = format_pmtiles_path("nz_basemap_mainland")
BASEMAP_CHATHAM_PATH = format_pmtiles_path("nz_basemap_chatham")
COMBINED_BASEMAP_PATH = format_pmtiles_path("nz_basemap")

AREA_BOUNDARIES_SA1_PATH = format_pmtiles_path("area_boundaries_sa1")
AREA_BOUNDARIES_SA2_PATH = format_pmtiles_path("area_boundaries_sa2")
AREA_BOUNDARIES_SA3_PATH = format_pmtiles_path("area_boundaries_sa3")
AREA_BOUNDARIES_TA_PATH = format_pmtiles_path("area_boundaries_ta")

GEOJSON_TA_PATH = format_geojson_path("boundaries_ta")
GEOJSON_SA3_PATH = format_geojson_path("boundaries_sa3")
GEOJSON_SA2_PATH = format_geojson_path("boundaries_sa2")
GEOJSON_SA1_PATH = format_geojson_path("boundaries_sa1")

# See latest builds at: https://maps.protomaps.com/builds/, this may break, so you'll have to update the URL as needed
PROTOMAPS_BASEMAP_BUILD_URL = "https://build.protomaps.com/20261013.pmtiles"

BASEMAP_IGNORED_LAYERS = ["landuse", "pois", "buildings"]

TIPPECANOE_IMAGE = "nz-census-map-tippecanoe"

def run_with_docker(image: str, cmd: str):
    subprocess.run(
        f'docker run --rm -v "{DATA_DIR_LOCAL}:/data" -w /data {image} {cmd}',
        shell=True,
        check=True,
    )
    
def build_tippecanoe_image():
    map_files_dir = os.path.join("scripts", "map_files")
    subprocess.run(
        f"docker build -t {TIPPECANOE_IMAGE} -f {map_files_dir}/tippecanoe.Dockerfile {map_files_dir}",
        shell=True,
        check=True,
    )


def run_with_tippecanoe(cmd: str):
    run_with_docker(TIPPECANOE_IMAGE, f'bash -c "{cmd}"')


def fetch_basemap():
    def save_basemap(output_path: str, bbox: str):
        run_with_docker(
            "protomaps/go-pmtiles",
            f"extract {PROTOMAPS_BASEMAP_BUILD_URL} {output_path} --bbox={bbox} --maxzoom=12",
        )

    save_basemap(BASEMAP_MAINLAND_PATH, "165.673828,-47.338823,178.857422,-34.016242")
    save_basemap(BASEMAP_CHATHAM_PATH, "182.458497,-44.489317,184.315186,-43.501412")


def combine_and_filter_basemaps():
    exclude_args = " ".join(
        f"--exclude-layer={layer}" for layer in BASEMAP_IGNORED_LAYERS
    )
    run_with_tippecanoe(
        f"tile-join --no-tile-size-limit -f {exclude_args} "
        f"-o {COMBINED_BASEMAP_PATH} {BASEMAP_MAINLAND_PATH} {BASEMAP_CHATHAM_PATH}"
    )

def combine_geojson_to_pmtiles(
    output_path: str,
    geojson_paths: list[tuple[str, str]]
):
    geojson_paths_args = " ".join(
        [f"-L {layer}:{path}" for layer, path in geojson_paths]
    )

    run_with_tippecanoe(
        f"tippecanoe -f -o {output_path} -z12 --no-tile-size-limit --no-feature-limit "
        f"{geojson_paths_args}"
    )


def build_ta_pmtiles():
    combine_geojson_to_pmtiles(
        AREA_BOUNDARIES_TA_PATH,
        [
            ("ta", GEOJSON_TA_PATH),
        ],
    )
    
def build_sa3_pmtiles():
    combine_geojson_to_pmtiles(
        AREA_BOUNDARIES_SA3_PATH,
        [
            ("sa3", GEOJSON_SA3_PATH),
        ],
    )
    
def build_sa2_pmtiles():
    combine_geojson_to_pmtiles(
        AREA_BOUNDARIES_SA2_PATH,
        [
            ("sa2", GEOJSON_SA2_PATH),
        ],
    )


def build_sa1_pmtiles():
    # SA1 is kept in its own file, merging it with the other layers caused tiles to drop at random zoom levels
    combine_geojson_to_pmtiles(
        AREA_BOUNDARIES_SA1_PATH,
        [
            ("sa1", GEOJSON_SA1_PATH),
        ],
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build PMTiles for NZ Census Map")
    parser.add_argument(
        "--build-boundary-pmtiles",
        "-bp",
        action="store_true",
        help="Build the boundary PMTiles",
    )
    parser.add_argument(
        "--process-basemap-pmtiles",
        "-pb",
        action="store_true",
        help="Fetch and process the basemap PMTiles",
    )
    
    parser.add_argument("--all", "-a", action="store_true", help="Run all steps")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        exit(1)

    if args.build_boundary_pmtiles or args.all:
        print("Building boundary pmtiles")
        
        print("Building TA pmtiles")
        build_ta_pmtiles()
        print("Building SA3 pmtiles")
        build_sa3_pmtiles()
        print("Building SA2 pmtiles")
        build_sa2_pmtiles()
        print("Building SA1 pmtiles")
        build_sa1_pmtiles()
        
        print("Building boundary pmtiles done")

    if args.process_basemap_pmtiles or args.all:
        fetch_basemap()
        combine_and_filter_basemaps()
        print("fetching basemap done")