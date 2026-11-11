#!/home/oper/.venv/bin/python3

"""
This will define the receivers tab layout
"""
import dash_bootstrap_components as dbc
import plotly.express as px
from utils.functions import create_graph, create_time_buttons_bar
from dash import (
    dcc,
    html,
)
from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')
empty_fig = px.line()

label = 'Receivers'

layout = (
    dcc.Interval(
        id='receivers-interval',
        interval=(600 * 1000),
        n_intervals=0
    ),
    create_time_buttons_bar('receivers'),
    html.Div(children=[
        html.Div([
            # First line: 2 graphs
            html.Div([
                html.Div(create_graph('nn-receiver-temp'), className='col'),
                html.Div(create_graph('ns-receiver-temp'), className='col'),
            ], className='hstack gap-2'),
            # Second line: 2 graphs
            html.Div([
                html.Div(create_graph('nn-receiver-pressure'), className='col'),
                html.Div(create_graph('ns-receiver-pressure'), className='col'),
            ], className='hstack gap-2')
        ], className='vstack gap-2'),
        html.Div(id='last-receivers-update', className='position-relative float-end small'),
    ])
)
