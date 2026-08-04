from pathlib import Path
import requests

header = {
    "Accept": "application/json"
}

response = requests.get("https://api.carbonintensity.org.uk/intensity/date", headers=header)

print(response.json())