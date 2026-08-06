from pathlib import Path
import requests
import json
import datetime

date = datetime.date.today()
def file_path(dt):
    filename = f"{Path(__file__).stem}_{dt}.json"
    return filename


#Where do we want the raw data to go
#filepath = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "carbon.json"

#what do we want from the API
#header = {
#    "Accept": "application/json"
#}

#Make the request to the API
#response = requests.get("https://api.carbonintensity.org.uk/intensity/date", headers=header)

#Write the json response to a file in /data/raw
#with open(filepath, 'w', encoding='utf-8') as file:
#    json.dump(response.json(), file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    print(file_path(date))