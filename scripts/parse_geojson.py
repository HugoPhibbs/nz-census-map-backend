import json

files = [
    {"name": "statistical-area-2-2023-clipped-generalised.json", "id_prefix": "2023S-S2", "existing_id_key": "SA22023__1"},
    {"name": "statistical-area-3-2023-clipped-generalised.json", "id_prefix": "2023S-S3", "existing_id_key": "SA32023__1"},
    {"name": "territorial-authority-2023-clipped-generalised.json", "id_prefix": "2023-TA", "existing_id_key": "TA2023_V_1"}
]

def parse_all_files():
    for file in files:
        with open(f"./data/{file['name']}", "r", encoding="utf-8") as f:
            geojson = json.load(f)

        adjust_properties(geojson, file["id_prefix"], file["existing_id_key"])

        with open(f"./data/{file['name'].split('.')[0]}-adjusted.json", "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)


def adjust_properties(geojson, id_prefix, existing_id_key):
    for feature in geojson["features"]:
        old_properties = feature["properties"]
        new_properties = {
            "area_id": f"{id_prefix}-{old_properties[existing_id_key]}",
            "name": old_properties[existing_id_key]
        }
        feature["properties"] = new_properties

if __name__ == "__main__":
    parse_all_files()
