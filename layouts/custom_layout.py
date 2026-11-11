#!/home/oper/.venv/bin/python3
"""
This will define the custom tab layout
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

label = 'Custom'

antennas = ['ns', 'nn', 'both']

#####################
# CUSTOM TAB LAYOUT #
#####################
backdrop_content = [
    html.Div(
        [
            html.Span('# of graphs'),
            dbc.ButtonGroup(
                [
                    dbc.Button(f'{n}', id=f'{n}-graphs', n_clicks=0, outline=True, color='primary') for n in range(1, 5)
                ],
            )
        ], className='hstack gap-2',
    ),
    html.Div(
        [
            dbc.Row(id='output-container'),
        ], className='vstack gap-2',
    )
]


graphs_backdrop = html.Div(
    [
        dbc.Offcanvas(
            backdrop_content,
            id='graph-config-backdrop',
            title='Graphs configuration',
            is_open=False,
            backdrop=False,
            style={'width': '18rem'},
        ),
        dbc.Button('Configure Graphs', id='graph-backdrop-button', n_clicks=0),
    ]
)


layout = (
    dcc.Interval(
        id='home-interval',
        interval=(600 * 1000),
        n_intervals=0
    ),
    html.Div(
        [
            graphs_backdrop,
            dbc.Row(
                [
                    dbc.Col(create_graph('custom-graph-1', display='none'), width=6, className='mt-2'),
                    dbc.Col(create_graph('custom-graph-2', display='none'), width=6, className='mt-2'),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(create_graph('custom-graph-3', display='none'), width=6, className='mt-2'),
                    dbc.Col(create_graph('custom-graph-4', display='none'), width=6, className='mt-2'),
                ]
            ),
        ],
        className='mt-2'
    )
)
