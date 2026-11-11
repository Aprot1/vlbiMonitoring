#!/home/oper/.venv/bin/python3

import plotly.express as px
import plotly.graph_objects as go
from utils import influx_methods
import utils.functions as utils
from datetime import datetime
from dash import (
    callback,
    Input,
    no_update,
    Output,
    set_props,
    State,
)
from dash.exceptions import PreventUpdate


# ----------------------
# Get the data from influx database to create plots
# ----------------------
def build_receivers_graphs(time):
    temps = ['tcold', 'tfeed', 'tint', 'tlna']
    antennas = ['nn', 'ns']
    temp_graphs = {}
    press_graphs = {}
    for ant in antennas:    # Temperature figures
        temp_graphs[ant] = go.Figure()
        for t in temps:
            if isinstance(time, int):
                data = influx_methods.get_hours('cryo', t, ant, time)
            else:
                data = influx_methods.get_range('cryo', t, ant, time)

            if data is not None:
                temp_graphs[ant].add_trace(go.Scatter(x=data['_time'], y=data.valueMean, mode='lines', name=t))

                temp_graphs[ant].update_layout(
                    title=f'{ant.capitalize()} receiver Cryo',
                    yaxis={'title': 'Temperature [K]'},
                    hovermode='x unified',
                )
                temp_graphs[ant].update_xaxes(title_text='Time')
                temp_graphs[ant].update_yaxes(title_text='Temperature (K)')
            else:
                temp_graphs[ant] = utils.no_data_graph(f'cryo {ant}')


        # Pressure figures
        if isinstance(time, int):
            pressure = influx_methods.get_hours('cryo', 'pressure', ant, time)
        else:
            pressure = influx_methods.get_range('cryo', 'pressure', ant, time)

        if pressure is not None:
            press_graphs[ant] = px.line(x=pressure['_time'], y=pressure.valueMean, labels={'x': 'Time', 'y': 'Pressure (mbar)'})

            press_graphs[ant].update_layout(
                    title=f'{ant.capitalize()} receiver Pressure',
                    xaxis={'title': ''},
                    yaxis={'title': 'Pressure [mbar]', 'exponentformat': 'e', 'showexponent': 'all'},
                )
        else:
            press_graphs[ant] = utils.no_data_graph(f'Pressure {ant}')

    return {
        'nn-receiver-temp': temp_graphs['nn'],
        'ns-receiver-temp': temp_graphs['ns'],
        'nn-receiver-pressure': press_graphs['nn'],
        'ns-receiver-pressure': press_graphs['ns'],
    }


# ----------------------
# Update the tab (on loading and interval timer)
# ----------------------
@callback(
Output(component_id='last-receivers-update', component_property='children'),
    Output(component_id='nn-receiver-temp', component_property='figure'),
    Output(component_id='ns-receiver-temp', component_property='figure'),
    Output(component_id='nn-receiver-pressure', component_property='figure'),
    Output(component_id='ns-receiver-pressure', component_property='figure'),
    Input(component_id='tabs', component_property='active_tab'),
    Input(component_id='receivers-interval', component_property='n_intervals'),
)
def create_timing_graph(active_tab, n):
    # print(f'Callback triggered in TIMING, tab = {active_tab}')
    if active_tab != 'receivers-tab':
        # print('Creating receivers graph')
        return no_update, no_update, no_update, no_update, no_update

    print('Updating receivers-tab')
    figs = build_receivers_graphs(24)
    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')

    return (last_update,
            figs['nn-receiver-temp'],
            figs['ns-receiver-temp'],
            figs['nn-receiver-pressure'],
            figs['ns-receiver-pressure'])


# ----------------------
# when a specific time is asked
# ----------------------
@callback(
    Output(component_id='receivers-interval', component_property='disabled'),
    Input(component_id='receivers-go-button', component_property='n_clicks'),
    Input(component_id='receivers-period-input', component_property='n_submit'),
    State(component_id='receivers-period-input', component_property='value'),
    State(component_id='receivers-start-date-input', component_property='value'),
    State(component_id='receivers-end-date-input', component_property='value'),
    prevent_initial_call=True,
)
def on_go_button(n, e, period, start, end):
    if period:
        figs = build_receivers_graphs(int(period))
        utils.update_graphs(figs)
        set_props('receivers-period-input', {'value': None})
    elif start and end:
        figs = build_receivers_graphs([start, end])
        utils.update_graphs(figs)
        set_props('receivers-start-date-input', {'value': None})
        set_props('receivers-end-date-input', {'value': None})
    else:
        raise PreventUpdate

    return True


# ----------------------
# back to live
# ----------------------
@callback(
    Input(component_id='receivers-back-to-live-button', component_property='n_clicks'),
    prevent_initial_call=True,
)
def back_to_live(n):
    figs = build_receivers_graphs(24)
    utils.update_graphs(figs)
    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')
    set_props('receivers-period-input', {'value': None})
    set_props('receivers-start-date-input', {'value': None})
    set_props('receivers-end-date-input', {'value': None})
    set_props('last-receivers-update', {'children': last_update})
    set_props('receiver-interval', {'disabled': False})