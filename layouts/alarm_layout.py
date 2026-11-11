#!/home/oper/.venv/bin/python3
"""
This will define the alarm tab layout
"""

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import (
    dash_table,
    dcc,
    html,
)
from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')

label = 'Alarms Overview'

antennas = ['Nn', 'Ns']
# alarm_state = dict(clear='bg-success', warning='bg-warning', raised='bg-danger')
# component = ['acs', 'fsClient', 'fsNet', 'fmout', 'servos', 'cryo']


####################
# ALARM TAB LAYOUT #
####################
layout = (
    dcc.Interval(
        id='alarm-interval',
        interval=(300 * 1000),
        n_intervals=0
    ),

    html.Div([
        html.Div([
            dbc.Button('ACS', id='acs-button')
        ], className='hstack gap-2 mt-2'),
        html.Div([
            dbc.Button('fsClient nn', id='fs-nn-button'),
            dbc.Button('fsClient ns', id='fs-ns-button'),
        ], className='hstack gap-2'),
        html.Div([
            dbc.Button('fmout2gps nn', id='fmout-nn-button'),
            dbc.Button('fmout2gps ns', id='fmout-ns-button'),
        ], className='hstack gap-2'),
        html.Div([
            dbc.Button('Servos nn', id='servos-nn-button'),
            dbc.Button('Servos ns', id='servos-ns-button'),
        ], className='hstack gap-2'),
        html.Div([
            dbc.Button('Cryo nn', id='cryo-nn-button'),
            dbc.Button('Cryo ns', id='cryo-ns-button'),
        ], className='hstack gap-2'),
        html.H2('Last alarms'),
    ], className='vstack gap-2'),
    html.Div([
        html.Div([
            dbc.Table(id='nn-alarm-table'),
            dbc.Button('Acknowledge alarms', id='nn-acknowledge-button', style={'width': '200px'}),
        ], className='vstack gap-2'),
        html.Div([
            dbc.Table(id='ns-alarm-table'),
            dbc.Button('Acknowledge alarms', id='ns-acknowledge-button', style={'width': '200px'}),
        ], className='vstack gap-2'),
    ], className='hstack gap-2 mt-2 align-items-start'),
    html.Div(id='last-alarms-update', className='position-relative float-end small'),
)
