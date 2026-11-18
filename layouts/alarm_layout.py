#!/home/oper/.venv/bin/python3
"""
This will define the alarm tab layout
"""

import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import (
    dcc,
    html,
)
from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')

label = 'Alarms Overview'

# alarm_state = dict(clear='bg-success', warning='bg-warning', raised='bg-danger')
items = ['acs', 'fs', 'fmout', 'servos', 'cryo']
antennas = ['nn', 'ns']

# Creating the table with the switches for the alarm
alarm_table = dbc.Table(
    [
        html.Thead(html.Tr([html.Th(''), html.Th('Nn'), html.Th('Ns'),])),
        html.Tbody([
            html.Tr([
                html.Td(item),
                *[
                    html.Td(html.Div(
                        [
                            dbc.Switch(id={'type': 'alarm-switch', 'item': item, 'antenna': ant}),
                            dbc.Badge(f'{item} {ant}', id={'type': 'alarm-badge', 'item': item, 'antenna': ant},
                                      style={'textAlign': 'center', 'fontSize': 15}),
                        ], className='hstack',
                    ))
                    for ant in antennas
                ],
            ]) for item in items
        ])
    ], style={'width': 'auto'},
)

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
        alarm_table,
    ]),
    html.Div([
        html.H2('Last alarms'),
        html.Div([
            html.Div([
                dbc.Table(id='nn-last-alarm-table'),
                dbc.Button('Acknowledge alarms', id='nn-acknowledge-button', style={'width': '200px'}),
            ], className='vstack gap-2'),
            html.Div([
                dbc.Table(id='ns-last-alarm-table'),
                dbc.Button('Acknowledge alarms', id='ns-acknowledge-button', style={'width': '200px'}),
            ], className='vstack gap-2'),
        ], className='hstack gap-2 mt-2 align-items-start'),
    ], className='vstack'),
    html.Div(id='last-alarms-update', className='position-relative float-end small'),
)
