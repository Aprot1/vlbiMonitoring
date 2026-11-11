#!/home/oper/.venv/bin/python3

import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from utils import influx_methods
from datetime import datetime
from dash import (
    callback,
    callback_context,
    html,
    Input,
    Output,
    set_props,
    State,
)

from dash_bootstrap_templates import load_figure_template
values_to_plot = ['None', 'toto1', 'toto2', 'toto3', 'toto4', 'toto5', 'toto6']


# ----------------------
# Toggle on/off the left backdrop for graph configuration
# ----------------------
@callback(
    Output('graph-config-backdrop', 'is_open'),
    Input('graph-backdrop-button', 'n_clicks'),
    State('graph-config-backdrop', 'is_open'),
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


# ----------------------
# Update the backdrop depending on button clicked
# ----------------------
@callback(
    Output('output-container', 'children'),
    Input('1-graphs', 'n_clicks'),
    Input('2-graphs', 'n_clicks'),
    Input('3-graphs', 'n_clicks'),
    Input('4-graphs', 'n_clicks'),
    prevent_initial_call=True,
)
def update_input_group(b1, b2, b3, b4):
    ctx = callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == '1-graphs':
        n = 1
    elif button_id == '2-graphs':
        n = 2
    elif button_id == '3-graphs':
        n = 3
    elif button_id == '4-graphs':
        n = 4

    output = []
    for i in range(1, n+1):
        input_groups = html.Div(
            [
                html.Span(f'Graph {i}'),
                dbc.DropdownMenu(label='Traces',
                                 children=[dbc.DropdownMenuItem(t) for t in range(1,5)],
                                 id=f'traces-graph-{i}',
                                 className='mt-1'),
                dbc.DropdownMenu(
                    label='Data to plot',
                    children=[dbc.DropdownMenuItem(t) for t in values_to_plot],
                    id=f'select-graph-{i}',
                    className='mt-1'
                )
            ], className='mt-1'
        )
        output.append(input_groups)
    output.append(
        dbc.Button(
            'Update',
            color='primary',
            className='align-self-end mt-2'
        )
    )

    return output


# ----------------------
# Update graph element depending on # of traces
# ----------------------
@callback(
    Input('traces-graph-1', 'n_clicks'),
    Input('traces-graph-2', 'n_clicks'),
    Input('traces-graph-3', 'n_clicks'),
    Input('traces-graph-4', 'n_clicks'),
)
def update_traces_number(n1, n2, n3, n4):
    ctx = callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'traces-graph-1':
        print(n1)
    if button_id == 'traces-graph-2':
        print(n2)
    if button_id == 'traces-graph-3':
        print(n3)
    if button_id == 'traces-graph-4':
        print(n4)