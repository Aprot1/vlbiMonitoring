#!/home/oper/.venv/bin/python3

"""
This will define the home tab layout
"""
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from dash import (
    dcc,
    dash_table,
    html,
)
from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')
empty_pie = go.Pie()

label = 'Home'

###################
# HOME TAB LAYOUT #
###################

layout = (
    dcc.Interval(
        id='home-interval',
        interval=(3600 * 1000),
        n_intervals=0
    ),
    html.Div([
        html.Div([
            html.Div([
                dbc.Label('Next sessions'),
                dbc.Table(id='sessions-table'),
                ], className='vstack gap-2',
            ),
        ], className='hstack',
        ),
        html.Div(children=[
            html.Div(dcc.Loading(
                    type='circle',
                    children=dcc.Graph(id='nn-fx-usage',
                                       figure=empty_pie,
                                       style={'height': '350px'}))),
            html.Div(dcc.Loading(
                    type='circle',
                    children=dcc.Graph(id='ns-fx-usage',
                                       figure=empty_pie,
                                       style={'height': '350px'}))),
        ], className='hstack gap-3'
        ),
    ], className='vstack gap-3'),
    html.Div(id='last-home-update', className='position-relative float-end small'),
)
