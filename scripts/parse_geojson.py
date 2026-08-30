import json
import pandas as pd

files = [
    {"name": "statistical-area-2-2023-clipped-generalised.json", "name_key": "SA22023__1", "id_key": "SA22023_V1", "area_type": "SA2"},
    {"name": "statistical-area-3-2023-clipped-generalised.json", "name_key": "SA32023__1", "id_key": "SA32023_V1", "area_type": "SA3"},
    {"name": "territorial-authority-2023-clipped-generalised.json", "name_key": "TA2023_V_1", "id_key": "TA2023_V1_", "area_type": "TA"}
]

def parse_all_files():
    all_properties = []
    for file in files:
        with open(f"./data/geojson/{file['name']}", "r", encoding="utf-8") as f:
            geojson = json.load(f)

        adjust_properties(geojson, file["name_key"], file["id_key"], file["area_type"], all_properties)

        with open(f"./data/geojson/{file['name'].split('.')[0]}-adjusted.json", "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)

    return all_properties

def adjust_properties(geojson, name_key, id_key, area_type, all_properties):
    for feature in geojson["features"]:
        old_properties = feature["properties"]
        new_properties = {
            "area_name": old_properties[name_key],
            "area_code": old_properties[id_key],
            "census_year": 2023,
            "area_type": area_type
        }
        
        all_properties.append(new_properties)
        feature["properties"] = new_properties

def save_all_properties(all_properties):
    df = pd.DataFrame(all_properties)
    df.to_csv("./data/db-tables/csv-debug/areas_table.csv", index=False, encoding="utf-8")
    df.to_parquet("./data/db-tables/areas_table.parquet", index=False)

if __name__ == "__main__":
    all_properties = parse_all_files()
    save_all_properties(all_properties)
