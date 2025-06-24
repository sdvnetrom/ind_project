import requests
import json

url = "https://opendata.rdw.nl/resource/8ys7-d773.json"

kenteken = input("What is your license plate:\n").upper()

params = {"kenteken":kenteken}

response = requests.get(url, params)

if response.status_code == 200:
    data = json.loads(response.text)
    print(data)
    co2_uitstoot_gecombineerd = data[0]['co2_uitstoot_gecombineerd']
    
    print("The co2 emissions of your car are:", co2_uitstoot_gecombineerd, "g/Km.")
else:
    print(f"Error: {response.status_code}")
