import requests
import json
from openai import OpenAI
client = OpenAI(api_key='')

def kenteken_co2(kenteken):
    url = "https://opendata.rdw.nl/resource/8ys7-d773.json"
    params = {"kenteken":kenteken}
    response = requests.get(url, params)

    if response.status_code == 200:
        data = json.loads(response.text)
        fuel_types = set()
        for entry in data:
            if 'brandstof_omschrijving' in entry:
                fuel_types.add(entry['brandstof_omschrijving'].upper())

        if "ELEKTRICITEIT" in fuel_types:
            print("Well done for being sustainable! You drive electric")
            co2_uitstoot = data[0].get('co2_uitstoot_gecombineerd', "0")
            print("The co2 emissions of your car are:", co2_uitstoot, "g/Km.")
        else:
            co2_uitstoot = data[0].get('co2_uitstoot_gecombineerd')
            if co2_uitstoot:
                print("The co2 emissions of your car are:", co2_uitstoot, "g/Km.")
            else:
                print("CO2 emission data is not available for this car.")
            km_week = int(input('How many kilometeres do you drive per week on average: '))
            co2_week = km_week * int(co2_uitstoot)
            print(co2_week)
        response = client.responses.create(
        model="o4-mini",
        input=f"Can you show me comparisons on emitting {co2_week} g of co2 per week from driving, as in what does that mean in terms of other things such as trees? Can you also provide ways in which I can offset this and become more carbon neutral? Please take into account we are in the netherlands"
        )
        print(response.output_text)

    else:
        print(f"Error: {response.status_code}")

def get_kenteken():
    print("Enter the details of your car:")
    make = input("Make: ").upper()
    model = input("Model: ").upper()
    year = input("Year: ")
    year_start = f"{year}0101"
    year_end = f"{year}1231"
    url = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"
    params = {
        "$where": f"merk='{make}' AND handelsbenaming='{model}' AND datum_eerste_toelating>='{year_start}' AND datum_eerste_toelating<='{year_end}'",
        "$limit": 5
    }
    response = requests.get(url, params=params)
    results = response.json()
    
    if results:
        kenteken = results[0]['kenteken']
        return kenteken
    else:
        print("No cars found with those details.")
        return None

choice = input("Do you wish to enter your license plate(y/n): ")

if choice == 'y':
    kenteken = input("What is your license plate:\n").upper()

else:
    kenteken = get_kenteken()

kenteken_co2(kenteken)