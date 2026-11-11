#!/home/oper/.venv/bin/python3

import subprocess
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import (
    html,
    dcc,
    set_props,
)
from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')
empty_fig = px.line()


def create_time_buttons_bar(page):
    layout = html.Div([
        html.Span('Display the last '),
        dbc.Input(id=f'{page}-period-input', style={'width': '50px'}),
        html.Span('Hrs, or a specific period: '),
        dbc.Input(id=f'{page}-start-date-input', type='date', style={'width': '160px'}),
        html.Span('→'),
        dbc.Input(id=f'{page}-end-date-input', type='date', style={'width': '160px'}),
        dbc.Button('GO', id=f'{page}-go-button', n_clicks=0),
        dbc.Button('Back to live', id=f'{page}-back-to-live-button', className='position-absolute end-0'),
    ], className='d-flex align-items-center gap-2 mt-2 mb-2')

    return layout


# ----------------------
# "Loading" logo to display while the graph is creating
# ----------------------
def create_graph(id, display='block'):
    layout = dcc.Loading(
        type='circle',
        parent_style={'height': '100%', 'width': '100%'},
        style={'height': '100%', 'width': '100%'},
        children=dcc.Graph(id=id, figure=empty_fig, style={'height': '100%', 'width': '100%'}))

    return layout


# ----------------------
# Update figs according to given dictionary : {fig: to_display}
# ----------------------
def update_graphs(figs):
    for fig, traces in figs.items():
        set_props(fig, {'figure': traces})


# ----------------------
# To display if no data were found when displaying graph
# ----------------------
def no_data_graph(item):
    fig = go.Figure()
    fig.add_annotation(
        text=f'NO DATA FOR {item.upper()}',
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=20, color="gray")
    )

    fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


# ----------------------
# Send a given shell command and get the answer
# ----------------------
def get_ssh_command(cmd):
    stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    return stdout.decode(), stderr.decode()


def flexbuff_sessions(ant):
    ips = {'nn': '10.0.109.34', 'ns': '10.0.109.33'}

    cmd = f'ssh oper@{ips[ant]} vbs_ls -lhrT'
    print(cmd)
    stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    lines = stdout.decode('utf-8').splitlines()
    for i, l in enumerate(lines):
        lines[i] = l.split()
    df = pd.DataFrame(lines)
    df.columns = df.iloc[0] # use first line as column names
    df.drop(df.index[0], inplace=True)  # Remove first line
    
    return df


# ----------------------
# Send a command to a given flexbuff to get the memory usage
# ----------------------
def flexbuff_usage(ant):
    ips = {'nn': '10.0.109.34', 'ns': '10.0.109.33'}

    cmd = f'ssh oper@{ips[ant]} df -h'
    stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    lines = stdout.decode('utf-8').splitlines()
    for i, l in enumerate(lines):
        lines[i] = l.split()
    df = pd.DataFrame(lines)
    df.columns = df.iloc[0] # use first line as column names
    df.drop(df.index[0], inplace=True)  # Remove first line
    df = df[df['Mounted'].str.contains(r'/mnt/disk', regex=True)]
    df.sort_values('Mounted', inplace=True)
    df['Mounted'] = df['Mounted'].str.extract(r'(\d\d)').astype(int)
    to_change = ['Avail', 'Used']
    for i in to_change:
        conditions = [df[i].str.contains('T'), df[i].str.contains('G')]
        choices = [df[i].str.extract(r'(\d.\d)').astype(float), df[i].str.extract(r'(\d*)').astype(float) / 1024]
        df[i] = np.select(conditions, choices)

    df.reset_index(inplace=True)

    # Check for missing disks in the mounting points (should go from 1 to 72)
    missing = []
    for i in range(df['Mounted'].index[0] + 1, df['Mounted'].index[-1]):
        if i not in df['Mounted']:
            missing.append(i)

    free = df['Avail'].sum().round(1)
    used = df['Used'].sum().round(1)

    return free, used, missing


# ----------------------
# Create the pie chart for flexbuff usage
# ----------------------
def disk_usage_donut(ant):
    try:
        free, used, missing = flexbuff_usage(ant)
        tot = used + free
        used_percent = used / tot * 100
        if used_percent < 70:
            color = '#2ECC71'   # Green
        elif used_percent < 85:
            color = '#F1C40F'   # Yellow
        else:
            color = '#E74C3C' # Red

        fig = go.Figure(data=[go.Pie(values=[used_percent, 100-used_percent],
                                     labels=[f'Used ({used} Tb)', f'Free ({free} Tb)'],
                                     hole=0.75,
                                     marker=dict(colors=[color, '#E5E5E5'])
                                     )
                              ]
                        )
        fig.update_layout(title=f'Disk Usage Flexbuff {ant}', font=dict(size=16))
    except:
        fig = no_data_graph(f'flexbuff {ant}')

    return fig


if __name__ == '__main__':
    flexbuff_usage('ns')