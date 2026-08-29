import json

files = [
    {"name": "statistical-area-2-2023-clipped-generalised.json", "id_prefix": "2023-S2", "name_key": "SA22023__1", "id_key": "SA22023_V1"},
    {"name": "statistical-area-3-2023-clipped-generalised.json", "id_prefix": "2023-S3", "name_key": "SA32023__1", "id_key": "SA32023_V1"},
    {"name": "territorial-authority-2023-clipped-generalised.json", "id_prefix": "2023-TA", "name_key": "TA2023_V_1", "id_key": "TA2023_V_1"}
]

def parse_all_files():
    for file in files:
        with open(f"./data/{file['name']}", "r", encoding="utf-8") as f:
            geojson = json.load(f)

        adjust_properties(geojson, file["id_prefix"], file["name_key"], file["id_key"])

        with open(f"./data/{file['name'].split('.')[0]}-adjusted.json", "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)


def adjust_properties(geojson, id_prefix, name_key, id_key):
    for feature in geojson["features"]:
        old_properties = feature["properties"]
        census_area_id = old_properties[id_key]
        new_properties = {
            "area_id": f"{id_prefix}-{census_area_id}-{old_properties[name_key]}",
            "name": old_properties[name_key],
            "census_area_id": census_area_id
        }
        feature["properties"] = new_properties

if __name__ == "__main__":
    parse_all_files()
