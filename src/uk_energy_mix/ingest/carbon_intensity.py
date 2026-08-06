from uk_energy_mix.ingest.config import ROOT_DIR
from pathlib import Path
import requests
import json
import datetime

SOURCE_NAME = "carbon_intensity"
SOURCE_URL = "https://api.carbonintensity.org.uk/"


def file_path(dt):
    filepath = ROOT_DIR / "data" / "raw" / SOURCE_NAME /f"{dt}.txt"
    return filepath

#make the api call, return txt data
def fetch():
    pass

#this needs looking at, raw should be txt not json!
def write(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data.json(), file, ensure_ascii=False, indent=4)

#what do we want from the API
#header = {
#    "Accept": "application/json"
#}

#Make the request to the API
#response = requests.get("https://api.carbonintensity.org.uk/intensity/date", headers=header)

if __name__ == "__main__":
    date = datetime.date.today()
    print(file_path(date))