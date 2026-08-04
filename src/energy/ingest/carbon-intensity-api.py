import requests

headers = {
    'Accept': 'application/json'
}

r  = requests.get('https://api.carbonintensity.org.uk/intensity', params={}, headers = headers)

print(r.json())