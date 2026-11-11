#!/home/oper/.venv/bin/python3
"""
This will define the gravimeters tab layout
"""
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from utils.functions import create_graph
from dash import (
    dcc,
    html,
)
from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')
empty_fig = px.line()

label = 'Gravimeter'

##########################
# GRAVIMETERS TAB LAYOUT #
##########################
layout = html.Iframe(
    src='http://gravity.statkart.no/index.html',
    style={'width': '100%', 'height': '85vh', 'border': 'none'},
)