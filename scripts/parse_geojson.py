import json
import pandas as pd

files = [
    {"name": "statistical-area-1-2023-clipped-generalised.json",
        "name_key": "LANDWATER_", "id_key": "SA12023_V1", "area_type": "SA1"},
    {"name": "statistical-area-2-2023-clipped-generalised.json",
        "name_key": "SA22023__1", "id_key": "SA22023_V1", "area_type": "SA2"},
    {"name": "statistical-area-3-2023-clipped-generalised.json",
        "name_key": "SA32023__1", "id_key": "SA32023_V1", "area_type": "SA3"},
    {"name": "territorial-authority-2023-clipped-generalised.json",
        "name_key": "TA2023_V_1", "id_key": "TA2023_V1_", "area_type": "TA"}
]
CENSUS_YEAR = 2023


def parse_all_files():
    all_properties = []
    
    inland_water_area_ids = []
    
    for file in files:
        file_name = file["name"]
        name_key = file["name_key"]
        id_key = file["id_key"]
        
        with open(f"./data/geojson/{file_name}", "r", encoding="utf-8") as f:
            geojson = json.load(f)
        
        new_inland_water_area_ids = remove_inland_water_areas(geojson, name_key, id_key)
        inland_water_area_ids.extend(new_inland_water_area_ids)

        adjust_properties(
            geojson, name_key, id_key, file["area_type"], all_properties)

        with open(f"./data/geojson/{file_name.split('.')[0]}-adjusted.json", "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
            
    inland_water_area_ids_df = pd.DataFrame(inland_water_area_ids, columns=["area_code", "census_year"])
    inland_water_area_ids_df.to_csv("./data/db-tables/inland_water_areas.csv", index=False)

    return all_properties


def remove_inland_water_areas(geojson, name_key, id_key):
    ids = []
    
    new_features = []
    
    for feature in geojson["features"]:
        if feature["properties"][name_key].lower().startswith("inland water"):
            ids.append((feature["properties"][id_key], CENSUS_YEAR))
        else:
            new_features.append(feature)
    
    geojson["features"] = new_features
    return ids


def adjust_properties(geojson, name_key, id_key, area_type, all_properties):
    for feature in geojson["features"]:
        old_properties = feature["properties"]
        area_code = old_properties[id_key]
        census_year = 2023

        new_properties = {
            "area_name": old_properties[name_key],
            "area_code": area_code,
            "census_year": census_year,
            "area_type": area_type
        }
        
        if area_type == "SA1":
            del new_properties["area_name"] # SA1 areas don't have names, only codes, Using "LANDWATER_" is a hack to remove inland water!

        all_properties.append(new_properties)
        feature["properties"] = {**new_properties,
                                 "area_id": f"{census_year}-{area_code}"}


def save_all_properties(all_properties):
    df = pd.DataFrame(all_properties)
    df.to_csv("./data/db-tables/csv-debug/areas_table.csv",
              index=False, encoding="utf-8")
    df.to_parquet("./data/db-tables/areas_table.parquet", index=False)


if __name__ == "__main__":
    all_properties = parse_all_files()
    save_all_properties(all_properties)
