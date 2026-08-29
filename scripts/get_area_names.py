import json

def get_area_names_and_ids(geojson_path):
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    names = []

    for feature in data["features"]:
        area_id = feature["properties"]["area_id"]
        name = feature["properties"]["name"]
        census_area_id = feature["properties"]["census_area_id"]
        
        names.append({"area_id": area_id, "name": name, "census_area_id": census_area_id})

    return names

def get_all_names():
    sa2_names_and_ids = get_area_names_and_ids("data/statistical-area-2-2023-clipped-generalised-adjusted.json")
    sa3_names_and_ids = get_area_names_and_ids("data/statistical-area-3-2023-clipped-generalised-adjusted.json")
    ta_names_and_ids = get_area_names_and_ids("data/territorial-authority-2023-clipped-generalised-adjusted.json")

    names_dict = {
        "SA2": sa2_names_and_ids,
        "SA3": sa3_names_and_ids,
        "TA": ta_names_and_ids
    }

    with open("data/area_names.json", "w", encoding="utf-8") as f:
        json.dump(names_dict, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    get_all_names()