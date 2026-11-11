#!/home/oper/.venv/bin/python3

import dash_bootstrap_components as dbc
import plotly.express as px
from utils.functions import create_graph, create_time_buttons_bar
from dash import (
    dcc,
    html,
)
from dash_bootstrap_templates import load_figure_template

"""
This will define the clocks tab layout
"""

load_figure_template('darkly')
empty_fig = px.line()   # create empty fig for initialization

label = 'Clocks'

#####################
# TIMING TAB LAYOUT #
#####################

layout = (
    dcc.Interval(
        id='clocks-interval',
        interval=(600 * 1000),
        n_intervals=0
    ),
    create_time_buttons_bar('clocks'),
    html.Div(children=[
        html.Div([
            html.Div([
                html.Div(create_graph('fmout-nn-graph'), className='col'),
                html.Div(create_graph('fmout-ns-graph'), className='col'),
            ], className='hstack gap-2'),
            html.Div([
                html.Div(create_graph('tic-t4-graph'), className='col', style={'width': '50%'}),
            ])
        ], className='vstack gap-2'),
    html.Div(id='last-clocks-update', className='position-relative float-end small'),
    ])
)
