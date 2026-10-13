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

def parse_all_files():
    all_properties = []
    
    inland_water_area_ids = []
    
    area_sq_kms = []
    
    bounding_boxes = []
    
    for file in files:
        file_name = file["name"]
        name_key = file["name_key"]
        id_key = file["id_key"]
        area_type = file["area_type"]
        
        with open(f"./data/geojson/{file_name}", "r", encoding="utf-8") as f:
            geojson = json.load(f)
        
        new_inland_water_area_ids = remove_inland_water_areas(geojson, name_key, id_key)
        inland_water_area_ids.extend(new_inland_water_area_ids)
        
        area_sq_kms.extend(get_area_squared_kms(geojson, id_key))

        adjust_properties(
            geojson, name_key, id_key, file["area_type"], all_properties
        )

        bounding_boxes.extend(save_bounding_boxes(geojson))
        
        with open(f"./data/geojson/boundaries_{area_type.lower()}.json", "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
            
        
    area_sq_kms_df = pd.DataFrame(area_sq_kms, columns=["area_id", "area_sq_km"])
    area_sq_kms_df.to_parquet("./data/pop-density/area_sq_kms.parquet", index=False)
    
    inland_water_area_ids_df = pd.Series(inland_water_area_ids)
    inland_water_area_ids_df.to_csv("./data/db-tables/inland_water_areas.csv", index=False, header=False)

    return all_properties, bounding_boxes


def remove_inland_water_areas(geojson, name_key, id_key):
    ids = []
    
    new_features = []
    
    for feature in geojson["features"]:
        if feature["properties"][name_key].lower().startswith("inland water"):
            ids.append(feature["properties"][id_key])
        else:
            new_features.append(feature)
    
    geojson["features"] = new_features
    return ids

def get_area_squared_kms(geojson, id_key):
    area_sq_kms = []
    
    for feature in geojson["features"]:
        area_sq_km = feature["properties"]["AREA_SQ_KM"]
        area_id = feature["properties"][id_key]
        
        area_sq_kms.append((area_id, area_sq_km))
    
    return area_sq_kms

def get_bounding_box(geojson_feature):
    geometry = geojson_feature["geometry"]
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"] # Handle MultiPolygon case: list of Polygons

    min_lng = float('inf')
    min_lat = float('inf')
    max_lng = float('-inf')
    max_lat = float('-inf')
    
    for polygon in polygons:
        for ring in polygon:
            for lng, lat in ring:
                min_lng = min(min_lng, lng)
                min_lat = min(min_lat, lat)
                max_lng = max(max_lng, lng)
                max_lat = max(max_lat, lat)

    round4dp = lambda x: round(x, 4)
    
    return [round4dp(min_lng), round4dp(min_lat), round4dp(max_lng), round4dp(max_lat)]

def save_bounding_boxes(geojson):
    bounding_boxes = []
    for feature in geojson["features"]:
        bounding_box = get_bounding_box(feature)
        area_id = feature["properties"]["area_id"]
        bounding_boxes.append((area_id, bounding_box))

    return bounding_boxes

def adjust_properties(geojson, name_key, id_key, area_type, all_properties):    
    for feature in geojson["features"]:
        old_properties = feature["properties"]
        area_id = old_properties[id_key]

        new_properties = {
            "area_name": old_properties[name_key],
            "area_id": area_id,
            "area_type": area_type,
        }
        
        if area_type == "SA1":
            del new_properties["area_name"] # SA1 areas don't have names, only codes, Using "LANDWATER_" is a hack to remove inland water!

        feature["properties"] = new_properties
        all_properties.append(new_properties)


def save_areas_table(all_properties, bounding_boxes):
    areas_df = pd.DataFrame(all_properties)
    bounding_boxes_df = pd.DataFrame(bounding_boxes, columns=["area_id", "bounding_box"])
    areas_df = areas_df.merge(bounding_boxes_df, on="area_id", how="left")
    
    areas_df.to_parquet("./data/db-tables/areas_table.parquet", index=False)


if __name__ == "__main__":
    all_properties, bounding_boxes = parse_all_files()
    save_areas_table(all_properties, bounding_boxes)
