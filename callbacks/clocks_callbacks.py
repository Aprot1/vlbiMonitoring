#!/home/oper/.venv/bin/python3


import plotly.express as px
import plotly.graph_objects as go
from utils import influx_methods
import utils.functions as utils
from datetime import datetime
from dash import (
    callback,
    Input,
    Output,
    no_update,
    set_props,
    State,
)
from dash.exceptions import PreventUpdate
import numpy as np


# ----------------------
# Get the data from influx database to create plots
# ----------------------
def build_clocks_graphs(time):
    antennas = ['nn', 'ns']
    # Get and plot tic values
    fmout = {}
    graphs = {}
    # get and plot the data for fmout2gps
    for ant in antennas:
        if isinstance(time, int):
            fmout[ant] = influx_methods.get_hours('maser', 'fmout2gps', 'tic', time, tag=ant)
        else:
            fmout[ant] = influx_methods.get_range('maser', 'fmout2gps', 'tic', time, tag=ant)

        if fmout[ant] is not None:  # there are data available for the period
            t = (fmout[ant]['_time'] - fmout[ant]['_time'].iloc[0]).dt.total_seconds() / 3600   # Convert time to hours
            try:
                slope, intercept = np.polyfit(t, fmout[ant]['_value'], 1)   # linear regression
            except:
                slope, intercept = np.nan, np.nan

            fmout[ant]['fit'] = slope * t + intercept
            graphs[ant] = px.line()
            graphs[ant].add_trace(go.Scatter(x=fmout[ant]['_time'], y=fmout[ant]['_value'],
                                             name='TIC',
                                             marker=dict(color='#316395')
                                             ))
            graphs[ant].add_trace(go.Scatter(x=fmout[ant]['_time'], y=fmout[ant]['fit'],
                                             name=f'Drift = {slope * 1e9:.2f} ns.hr⁻¹',
                                             marker=dict(color='red')
                                             ))
            graphs[ant].update_layout(
                title=f'fmout2gps {ant}',
                xaxis={'title': ''},
                yaxis={'title': 'TIC [s]', 'exponentformat': 'e', 'showexponent': 'all'},
                hovermode='x unified',
            )
        else:   # no data for the period asked
            graphs[ant] = utils.no_data_graph(f'fmout2gps {ant}')

    # get and plot the data for maser2gps
    if isinstance(time, int):
        tic_t4 = influx_methods.get_hours('maser', 'gps2maser', 'tic', time, tag='t4')
    else:
        tic_t4 = influx_methods.get_range('maser', 'gps2maser', 'tic', time, tag='t4')

    if tic_t4 is not None:  # there are data available for the period
        t = (tic_t4['_time'] - tic_t4['_time'].iloc[0]).dt.total_seconds() / 3600  # Convert time to hours
        try:
            slope, intercept = np.polyfit(t, tic_t4['_value'], 1)  # linear regression
        except:
            slope, intercept = np.nan, np.nan

        tic_t4['fit'] = slope * t + intercept
        graphs['t4'] = px.line()
        graphs['t4'].add_trace(go.Scatter(x=tic_t4['_time'], y=tic_t4['_value'],
                                         name='TIC',
                                         marker=dict(color='#316395')
                                         ))
        graphs['t4'].add_trace(go.Scatter(x=tic_t4['_time'], y=tic_t4['fit'],
                                         name=f'Drift = {slope * 1e9:.2f} ns.hr⁻¹',
                                         marker=dict(color='red')
                                         ))
        graphs['t4'].update_layout(
            title=f'gps2maser t4',
            xaxis={'title': ''},
            yaxis={'title': 'TIC [s]', 'exponentformat': 'e', 'showexponent': 'all'},
            hovermode='x unified',
        )
    else:  # no data for the period asked
        graphs['t4'] = utils.no_data_graph(f'gps2maser t4')

    return {
        'fmout-nn-graph': graphs['nn'],
        'fmout-ns-graph': graphs['ns'],
        'tic-t4-graph': graphs['t4'],
    }


# ----------------------
# Update the tab (on loading and interval timer)
# ----------------------
@callback(
    Output(component_id='last-clocks-update', component_property='children'),
    Output(component_id='fmout-nn-graph', component_property='figure'),
    Output(component_id='fmout-ns-graph', component_property='figure'),
    Output(component_id='tic-t4-graph', component_property='figure'),
    Input(component_id='tabs', component_property='active_tab'),
    Input(component_id='clocks-interval', component_property='n_intervals'),
)
def create_timing_graph(active_tab, n):
    # print(f'Callback triggered in TIMING, tab = {active_tab}')
    if active_tab != 'clocks-tab':
        return no_update, no_update, no_update, no_update
    # print('Creating masers graph')
    print('Updating Clocks-tab')
    figs = build_clocks_graphs(24)
    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')

    return (last_update,
            figs['fmout-nn-graph'],
            figs['fmout-ns-graph'],
            figs['tic-t4-graph'],)


# ----------------------
# when a specific time is asked
# ----------------------
@callback(
    Output(component_id='clocks-interval', component_property='disabled'),
    Input(component_id='clocks-go-button', component_property='n_clicks'),
    Input(component_id='clocks-period-input', component_property='n_submit'),
    State(component_id='clocks-period-input', component_property='value'),
    State(component_id='clocks-start-date-input', component_property='value'),
    State(component_id='clocks-end-date-input', component_property='value'),
    prevent_initial_call=True,
)
def on_go_button(n, e, period, start, end):
    if period:
        figs = build_clocks_graphs(int(period))
        utils.update_graphs(figs)
        set_props('clocks-period-input', {'value': None})
    elif start and end:
        figs = build_clocks_graphs([start, end])
        utils.update_graphs(figs)
        set_props('clocks-start-date-input', {'value': None})
        set_props('clocks-end-date-input', {'value': None})
    else:
        raise PreventUpdate

    return True


# ----------------------
# back to live
# ----------------------
@callback(
    Input(component_id='clocks-back-to-live-button', component_property='n_clicks'),
    prevent_initial_call=True,
)
def back_to_live(n):
    figs = build_clocks_graphs(24)
    utils.update_graphs(figs)
    set_props('clocks-period-input', {'value': None})
    set_props('clocks-start-date-input', {'value': None})
    set_props('clocks-end-date-input', {'value': None})
    set_props('last-clocks-update', {'children': 'Last update: ' + datetime.now().strftime('%H:%M:%S')})
    set_props('clocks-interval', {'disabled': False})
