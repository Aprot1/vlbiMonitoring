#!/home/oper/.venv/bin/python3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import influx_methods
import utils.functions as utils
from datetime import datetime
import numpy as np
from dash import (
    callback,
    Input,
    no_update,
    Output,
    set_props,
    State,
)
from dash.exceptions import PreventUpdate

wnd = ['windSpeed', 'windDir', 'windMax', 'windMin']
stations = ['brandal', 'rabben']


def build_wind_graphs(time):
    wind_graphs = {}
    ### Get wind data in one DF
    if isinstance(time, int):
        wind = influx_methods.get_hours('weather', 'windSpeed', 'brandal', time).drop(columns=['_value'])
    else:
        wind = influx_methods.get_range('weather', 'windSpeed', 'brandal', time).drop(columns=['_value', 'result', 'table'])
    wind.rename(columns={'valueMean': 'windSpeed'}, inplace=True)
    for i in wnd[1:]:
        if isinstance(time, int):
            df = influx_methods.get_hours('weather', i, 'brandal', time).drop(columns=['_value'])
        else:
            df = influx_methods.get_range('weather', i, 'brandal', time).drop(columns=['_value'])

        wind = wind.merge(df, how='left', on='_time')
        wind.rename(columns={'valueMean': i}, inplace=True)

    ### Plot the wind speed graph and legend tweaking
    wind_graphs['speed'] = go.Figure()

    # Wind max (upper of envelope)
    wind_graphs['speed'].add_trace(go.Scatter(
        x=wind['_time'],
        y=wind['windMax'],
        mode='lines',
        line={'shape': 'spline', 'width': 0},
        name='Wind gust and lull',
        legendgroup='wind',
        showlegend=False
    ))

    # Wind min (lower of envelope)
    wind_graphs['speed'].add_trace(go.Scatter(
        x=wind['_time'],
        y=wind['windMin'],
        mode='lines',
        line={'shape': 'spline', 'width': 0},
        fill='tonexty',
        fillcolor='rgba(31,119,180,0.25)',
        name='Wind gust and lull',
        legendgroup='wind',
    ))

    # Average plot
    wind_graphs['speed'].add_trace(go.Scatter(
        x=wind['_time'],
        y=wind['windSpeed'],
        mode='lines',
        line={'shape': 'spline', 'color': 'blue', 'width': 2},
        name='Wind average',
        legendgroup='wind'
    ))

    wind_graphs['speed'].update_layout(
        title=f'Wind Speed Brandal',
        yaxis={'title': f'Speed [m/s]'},
        hovermode='x unified',
    )

    #### WIND DIRECTION ####
    ### creating an averaging of the direction to have a "smoother" plot
    wind.set_index('_time', inplace=True)
    wind['cos'] = np.cos(np.deg2rad(wind['windDir']))
    wind['sin'] = np.sin(np.deg2rad(wind['windDir']))
    wind['cos_smooth'] = wind['cos'].rolling('15min', center=True, min_periods=1).mean()
    wind['sin_smooth'] = wind['sin'].rolling('15min', center=True, min_periods=1).mean()
    wind['dir_averaged'] = (np.degrees(np.arctan2(wind['sin_smooth'], wind['cos_smooth'])) + 360) % 360

    wind_graphs['direction'] = px.line(wind, y='dir_averaged')

    wind_graphs['direction'].update_layout(
        title=f'Wind direction Brandal',
        yaxis={'title': f'Direction (azimuth)'},
    )

    return {
        'wind-graph': wind_graphs['speed'],
        'wind-dir-graph': wind_graphs['direction']
    }


def build_others(time):
    temperatures = []
    pressures = []
    humidity = []
    for sta in stations:
        if isinstance(time, int):
            data = influx_methods.get_hours('weather', 'temperature', sta, time).drop(columns=['_value'])
        else:
            data = influx_methods.get_range('weather', 'temperature', sta, time).drop(columns=['_value'])
        data.set_index('_time', inplace=True)
        data['station'] = sta.capitalize()
        temperatures.append(data)
        if isinstance(time, int):
            data = influx_methods.get_hours('weather', 'pressure', sta, time).drop(columns=['_value'])
        else:
            data = influx_methods.get_range('weather', 'pressure', sta, time).drop(columns=['_value'])
        data.set_index('_time', inplace=True)
        data['station'] = sta.capitalize()
        pressures.append(data)
        if isinstance(time, int):
            data = influx_methods.get_hours('weather', 'humidity', sta, time).drop(columns=['_value'])
        else:
            data = influx_methods.get_range('weather', 'humidity', sta, time).drop(columns=['_value'])
        data.set_index('_time', inplace=True)
        data['station'] = sta.capitalize()
        humidity.append(data)

    temp = pd.concat(temperatures)
    pressure = pd.concat(pressures)
    humidity = pd.concat(humidity)

    to_plot = {'temperature': temp, 'pressure': pressure, 'humidity': humidity}
    graphs = {}
    for item, value in to_plot.items():
        graphs[item] = px.line(value, color='station')

    legends = {'temperature': 'Temperature [\u00B0C]',
               'pressure': 'Atmospheric Pressure [mbar]',
               'humidity': 'Relative Humidity [%]'}

    for item, value in graphs.items():
        value.update_layout(
            title=f'{item.capitalize()}',
            xaxis={'title': ''},
            yaxis={'title': f'{legends[item]}'},
            hovermode='x unified',
        )

    return {
        'temp-graph': graphs['temperature'],
        'atm-press-graph': graphs['pressure'],
        'rh-graph': graphs['humidity'],
    }

# ----------------------
# Update the tab (on loading and interval timer)
# ----------------------
@callback(
    Output(component_id='last-weather-update', component_property='children'),
    Output(component_id='wind-graph', component_property='figure'),
    Output(component_id='wind-dir-graph', component_property='figure'),
    Output(component_id='temp-graph', component_property='figure'),
    Output(component_id='atm-press-graph', component_property='figure'),
    Output(component_id='rh-graph', component_property='figure'),
    Input(component_id='tabs', component_property='active_tab'),
    Input(component_id='weather-interval', component_property='n_intervals'),
)
def create_graphs(active_tab, n):
    # print(f'Callback triggered in WEATHER, tab = {active_tab}')
    if active_tab != 'weather-tab':
        return no_update

    # print('Creating masers graph')
    print('Updating Weather-tab')
    wind_plots = build_wind_graphs(24)
    graphs = build_others(24)
    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')

    return (last_update,
            wind_plots['wind-graph'],
            wind_plots['wind-dir-graph'],
            graphs['temp-graph'],
            graphs['atm-press-graph'],
            graphs['rh-graph'])


# ----------------------
# when a specific time is asked
# ----------------------
@callback(
    Output(component_id='weather-interval', component_property='disabled'),
    Input(component_id='weather-go-button', component_property='n_clicks'),
    Input(component_id='weather-period-input', component_property='n_submit'),
    State(component_id='weather-period-input', component_property='value'),
    State(component_id='weather-start-date-input', component_property='value'),
    State(component_id='weather-end-date-input', component_property='value'),
    prevent_initial_call=True,
)
def on_go_button(n, e, period, start, end):
    if period:
        wind_plots = build_wind_graphs(int(period))
        graphs = build_others(int(period))
        utils.update_graphs(wind_plots)
        utils.update_graphs(graphs)
        set_props('weather-period-input', {'value': None})
    elif start and end:
        wind_plots = build_wind_graphs([start, end])
        graphs = build_others([start, end])
        utils.update_graphs(wind_plots)
        utils.update_graphs(graphs)
        set_props('weather-start-date-input', {'value': None})
        set_props('weather-end-date-input', {'value': None})
    else:
        raise PreventUpdate

    return True


# ----------------------
# back to live
# ----------------------
@callback(
    Input(component_id='weather-back-to-live-button', component_property='n_clicks'),
    prevent_initial_call=True,
)
def back_to_live(n):
    wind_plots = build_wind_graphs(24)
    graphs = build_others(24)
    utils.update_graphs(wind_plots)
    utils.update_graphs(graphs)
    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')
    set_props('weather-period-input', {'value': None})
    set_props('weather-start-date-input', {'value': None})
    set_props('weather-end-date-input', {'value': None})
    set_props('last-weather-update', {'children': last_update})
    set_props('weather-interval', {'disabled': False})