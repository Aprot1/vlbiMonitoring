#!/home/oper/.venv/bin/python3
"""
This will define the alarm tab layout
"""


import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from plotly.subplots import make_subplots
from dash import (
    dcc,
    html,
)
from utils.functions import create_graph, create_time_buttons_bar

load_figure_template('darkly')

label = 'Weather'


####################
# ALARM TAB LAYOUT #
####################
layout = (
    dcc.Interval(
        id='weather-interval',
        interval=(600 * 1000),
        n_intervals=0
    ),
    create_time_buttons_bar('weather'),
    html.Div([
        # Left: 2 graphs
        html.Div([
            html.Div(create_graph('wind-graph'), style={'flex': '1 1 0', 'minHeight': 0}),
            html.Div(create_graph('temp-graph'), style={'flex': '1 1 0', 'minHeight': 0}),
        ], className='d-flex flex-column gap-2', style={'flex': '5 1 0', 'minWidth': 0}),

        # Right: 3 graphs
        html.Div([
            html.Div(create_graph('wind-dir-graph'), style={'flex': '1 1 0', 'minHeight': 0}),
            html.Div(create_graph('atm-press-graph'), style={'flex': '1 1 0', 'minHeight': 0}),
            html.Div(create_graph('rh-graph'), style={'flex': '1 1 0', 'minHeight': 0}),
        ], className='d-flex flex-column gap-2', style={'flex': '4 1 0', 'minWidth': 0}),

    ], className='d-flex gap-2 w-100', style={'height': '90vh'}),
    html.Div(id='last-weather-update', className='position-relative float-end small'),
)
