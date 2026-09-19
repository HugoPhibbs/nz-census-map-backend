import csv
import xml.etree.ElementTree as ET

META_DATA_FOLDER = "data/meta-data"
XML_PATH = "topics-sa1-2023.xml"
OUT_PATH = "variable_codes.csv"
CODELIST_ID = "CL_CEN23_TBT_IND_003"

NS = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

tree = ET.parse(f"{META_DATA_FOLDER}/{XML_PATH}")
root = tree.getroot()

codelist = root.find(f'.//structure:Codelist[@id="{CODELIST_ID}"]', NS)

# code_id -> name, for every code in the list
names = {}
for code in codelist.findall("structure:Code", NS):
    code_id = code.get("id")
    name = code.find("common:Name", NS).text
    names[code_id] = name

# write one row per code, using its direct parent's name as group_name
with open(f"{META_DATA_FOLDER}/{OUT_PATH}", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["variable_code", "group_name", "variable_name"])
    for code in codelist.findall("structure:Code", NS):
        code_id = code.get("id")
        variable_name = names[code_id]
        parent = code.find("structure:Parent/Ref", NS)
        group_name = names[parent.get("id")] if parent is not None else ""
        
        if group_name == "":
            if code_id not in ["rc", "pc"]: # Usual/night resident population doesn't have a group
                continue
            
            group_name = "N/A"
        
        writer.writerow([code_id, group_name, variable_name])

print(f"Wrote {OUT_PATH}")