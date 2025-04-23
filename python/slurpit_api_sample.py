import requests
from rich import print

url = "http://slurpit-docker.clab.net:81/api/devices"
api_key = ''

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {api_key}"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(response.json())
else: 
    print(f"Error: {response.status_code}")
    print(response.text)