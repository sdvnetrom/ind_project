import requests
from openai import OpenAI
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

client = OpenAI(api_key='-')
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])
app.layout = dbc.Container(
    dbc.Row(
        dbc.Col([
            html.H2("CO₂ Emissions Checker", className="mb-4 mt-2 text-center"),
            dbc.RadioItems(
                id='input-mode',
                options=[
                    {'label': 'I want to use my license plate', 'value': 'plate'},
                    {'label': 'I want to search by make/model/year', 'value': 'car'}
                ],
                value='plate',
                inline=True,
                className="mb-3 justify-content-center",
                style={"textAlign": "center"}
            ),
            html.Div([
                html.Div([
                    dbc.Label("License Plate:"),
                    dbc.Input(id='license-plate', placeholder="e.g. XX123X", type='text'),
                ], id='plate-group', className="mb-3"),
                html.Div([
                    dbc.Label("Make:"),
                    dbc.Input(id='make', placeholder="e.g. VOLKSWAGEN", type='text'),
                    dbc.Label("Model:", className="mt-2"),
                    dbc.Input(id='model', placeholder="e.g. GOLF", type='text'),
                    dbc.Label("Year:", className="mt-2"),
                    dbc.Input(id='year', placeholder="e.g. 2017", type='number'),
                ], id='car-group', className="mb-3"),
                html.Div([
                    dbc.Label("How many kilometers do you drive per week?"),
                    dbc.Input(id='km-week', placeholder="e.g. 200", type='number'),
                ], className="mb-3"),
                dbc.Button("Submit", id='submit-btn', color='primary', className="mt-3"),
            ], className="d-flex flex-column align-items-center"),
            dbc.Card([
                dbc.CardHeader("Result"),
                dbc.CardBody(html.Pre(id='result-area', style={"whiteSpace": "pre-wrap"}))
            ], className="mt-4"),
        ], width=8, className="mx-auto"),
        justify="center",
        className="align-items-center min-vh-100"
    ),
    fluid=True,
    style={"backgroundColor": "#f8f9fa"}
)


@app.callback(
    Output('plate-group', 'style'),
    Output('car-group', 'style'),
    Input('input-mode', 'value')
)
def toggle_input_groups(mode):
    if mode == 'plate':
        return {}, {"display": "none"}
    else:
        return {"display": "none"}, {}

@app.callback(
    Output('result-area', 'children'),
    Input('submit-btn', 'n_clicks'),
    State('input-mode', 'value'),
    State('license-plate', 'value'),
    State('make', 'value'),
    State('model', 'value'),
    State('year', 'value'),
    State('km-week', 'value'),
    prevent_initial_call=True
)
def process_request(n_clicks, mode, plate, make, model, year, km_week):
    if not km_week:
        return "Please enter how many kilometers you drive per week."
    if mode == 'plate':
        if not plate:
            return "Please enter your license plate."
        kenteken = plate.replace(' ', '').upper()
    else:
        if not (make and model and year):
            return "Please fill in make, model, and year."
        url = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"
        year_start = f"{int(year)}0101"
        year_end = f"{int(year)}1231"
        params = {
            "$where": f"merk='{make.upper()}' AND handelsbenaming='{model.upper()}' AND datum_eerste_toelating>='{year_start}' AND datum_eerste_toelating<='{year_end}'",
            "$limit": 1
        }
        response = requests.get(url, params=params)
        results = response.json()
        if results:
            kenteken = results[0]['kenteken']
        else:
            return "No cars found with those details."
    url = "https://opendata.rdw.nl/resource/8ys7-d773.json"
    params = {"kenteken": kenteken}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"RDW API Error: {response.status_code}"
    data = response.json()
    if not data:
        return "No emissions data found for this license plate."

    fuel_types = {entry['brandstof_omschrijving'].upper() for entry in data if 'brandstof_omschrijving' in entry}
    electric = "ELEKTRICITEIT" in fuel_types

    output = [f"License Plate: {kenteken}"]

    if electric:
        output.append("Well done for being sustainable! You drive electric.")
        co2_uitstoot = data[0].get('co2_uitstoot_gecombineerd', "0")
        output.append(f"CO₂ emissions: {co2_uitstoot} g/km (should be 0 for electric cars).")
        return "\n".join(output)
    else:
        co2_uitstoot = data[0].get('co2_uitstoot_gecombineerd')
        if co2_uitstoot:
            try:
                co2_uitstoot = float(co2_uitstoot)
                co2_week = float(km_week) * co2_uitstoot
                output.append(f"CO₂ emissions: {co2_uitstoot} g/km")
                output.append(f"Weekly CO₂ emissions: {int(co2_week):,} grams")
                ai_prompt = (
                    f"Can you show me comparisons on emitting {int(co2_week)} grams of CO₂ per week from driving, "
                    "as in what does that mean in terms of other things such as trees? Can you also provide ways in "
                    "which I can offset this and become more carbon neutral? Please take into account we are in the Netherlands."
                )
                ai_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": ai_prompt}]
                )
                output.append("\n Advice:\n" + ai_response.choices[0].message.content)
            except Exception as e:
                output.append(f"Error in calculation or AI call: {e}")
        else:
            output.append("CO₂ emission data is not available for this car.")
    return "\n".join(output)

if __name__ == '__main__':
    app.run(debug=True)