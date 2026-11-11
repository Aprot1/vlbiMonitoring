#!/home/oper/.venv/bin/python3
"""
This will define the ycmc tab layout
"""

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import (
    dcc,
    html,
)
from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')

label = 'YCMC'

layout = html.Iframe(
    src='http://10.0.109.133/ycmc-web/system/',
    style={'width': '100%', 'height': '85vh', 'border': 'none'},
)