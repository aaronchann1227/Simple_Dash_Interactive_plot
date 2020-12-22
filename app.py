import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv("flights.csv", low_memory=False)
airport = pd.read_csv("airports.csv")
airline = pd.read_csv("airlines.csv")
df = df.reindex(columns = ["AIRLINE","ORIGIN_AIRPORT","DESTINATION_AIRPORT"])
#add airline name to df
df = pd.merge(df, airline, left_on='AIRLINE', right_on='IATA_CODE', how = "left")
df.drop("IATA_CODE", axis = 1, inplace = True)
df.rename(columns={"AIRLINE_x":"airlineCode", "AIRLINE_y" : "airline"}, inplace = True)

# adding origin location to df
orginAirport = airport.copy()
orginAirport.rename(columns={"AIRPORT":"originAirport", "LATITUDE": "originLatitude", "LONGITUDE": "originLongitude"}, inplace = True)
df = pd.merge(df, orginAirport, left_on='ORIGIN_AIRPORT', right_on='IATA_CODE', how = "left")
df.drop("IATA_CODE", axis = 1, inplace = True)

#adding destination location to df
destinationAirport = airport.copy()
destinationAirport.drop(["CITY","STATE","COUNTRY"], axis = 1, inplace = True)
destinationAirport.rename(columns={"AIRPORT":"destinationAirport", "LATITUDE": "destinationLatitude", "LONGITUDE": "destinationLongitude"}, inplace = True)
df = pd.merge(df, destinationAirport, left_on='DESTINATION_AIRPORT', right_on='IATA_CODE', how = "left")
df.drop("IATA_CODE", axis = 1, inplace = True)

cleandf = df.reindex(columns = ["airlineCode","airline","ORIGIN_AIRPORT","originAirport","originLatitude","originLongitude","DESTINATION_AIRPORT","destinationAirport","destinationLatitude","destinationLongitude"])


####################################################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

####################################################

app.layout = html.Div([
    dcc.Dropdown(
        id="airline_option",
        options=[{'label': str(airline), 'value': str(airline)} for airline in cleandf["airline"].unique()], 
        value=cleandf["airline"].unique()[0]
    ),
    dcc.Graph(id='flight_graph', style={"height": 900})
])

@app.callback(
    Output('flight_graph', 'figure'),
    Input('airline_option', 'value'))
def update_figure(airline_option):
    #filter for airline
    newdf = cleandf.loc[cleandf["airline"] == airline_option]
    newdf.drop(["airlineCode", "airline"], axis = 1, inplace = True)
    newdf.dropna(inplace = True)

    #combine departure and arrival
    origindf = newdf.reindex(columns = ["ORIGIN_AIRPORT","originAirport","originLatitude","originLongitude"])
    origindf.rename(columns={"ORIGIN_AIRPORT":"airportCode", "originAirport" : "airport", "originLatitude":"lat", "originLongitude":"long"}, inplace = True)
    origindf.reset_index(inplace = True)

    destinationdf = newdf.reindex(columns = ["DESTINATION_AIRPORT", "destinationAirport", "destinationLatitude", "destinationLongitude"])
    destinationdf.rename(columns={"DESTINATION_AIRPORT":"airportCode", "destinationAirport" : "airport", "destinationLatitude":"lat", "destinationLongitude":"long"}, inplace = True)
    destinationdf.reset_index(inplace = True)

    finaldf = pd.concat([origindf, destinationdf], axis = 0)

    #groupby to get the count
    countdf = finaldf.groupby(["airportCode"])[["index"]].count()
    countdf = countdf.reset_index()
    countdf.rename(columns={"index":"count"}, inplace = True)

    finaldf.drop("index", axis = 1, inplace = True)
    finaldf.drop_duplicates(inplace = True)

    #merge finaldf with countdf to get the count
    finaldf = pd.merge(finaldf, countdf, on = "airportCode", how = "left" )
    finaldf['text'] = finaldf['airport'] + "; Total Air Traffic: " + finaldf['count'].astype(str)


    fig = go.Figure(data=go.Scattergeo(
            lon = finaldf['long'],
            lat = finaldf['lat'],
            text = finaldf['text'],
            mode = 'markers',
            marker = dict(
                size = 6,
                opacity = 1,
                reversescale = False,
                autocolorscale = False,
                symbol = 'circle',
                line = dict(
                    width=1,
                    color='rgba(102, 102, 102)'
                ),
                colorscale = 'Inferno',
                cmin = 0,
                color = finaldf['count'],
                cmax = finaldf['count'].max(),
                colorbar_title="Total Domestic Traffic (Arrivals + Departures) 2015"
            )))
    fig.update_layout(
            title = 'Total Domestic Air Traffic in US Cities by selected Airline in 2015<br>(Hover for airport names and total domestic air traffic)',
            geo = dict(
                scope='usa',
                projection_type='albers usa',
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(217, 217, 217)",
                countrycolor = "rgb(217, 217, 217)",
                countrywidth = 1.5,
                subunitwidth = 1.5
            ),
        )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)





















