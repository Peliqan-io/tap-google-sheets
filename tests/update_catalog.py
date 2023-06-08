import json


file = open(f"catalog.json", "r+")
lines = json.loads(file.read())
for stream in lines["streams"]:
    for mdata in stream["metadata"]:
        if len(mdata["breadcrumb"]) == 0:
            mdata["metadata"]["selected"] = True
json_object = json.dumps(lines, indent=4)
with open(f"catalogIncludedTables.json", "w") as outfile:
    outfile.write(json_object)