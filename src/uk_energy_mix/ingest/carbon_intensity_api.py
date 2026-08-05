from pathlib import Path
import requests
import json

filepath = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "carbon.json"
header = {
    "Accept": "application/json"
}

response = requests.get("https://api.carbonintensity.org.uk/intensity/date", headers=header)

with open(filepath, 'w', encoding='utf-8') as file:
    json.dump(response.json(), file, ensure_ascii=False, indent=4)