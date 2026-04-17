import json

config_path = "/home/carson/.openclaw/workspace/napcat/config/onebot11.json"
try:
    with open(config_path, "r") as f:
        data = json.load(f)
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
