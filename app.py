#!/home/oper/.venv/bin/python3

"""
This is the main app script to start for the application
"""
import importlib
from pathlib import Path
from collections import OrderedDict
from utils import influx_methods
from datetime import datetime
from zoneinfo import ZoneInfo
from alarm import alarm_methods

import asyncio
import dash_bootstrap_components as dbc
from dash import (
    callback,
    ctx,
    Dash,
    dcc,
    html,
    Input,
    Output,
    set_props,
)
from dash_bootstrap_templates import load_figure_template

antennas = ['nn', 'ns']
button_color = dict(green='btn-success', red='btn-primary')
year = datetime.now().year

# Influxdb parameters
token = 'Vh6U1Q2HWdxJi9fm2NwfA5lIz3GmU6EPyoEqy5qEXohcewUt1zEA_TaexRGegKyTQ58J23HbBtqXeu2FwXWa-w=='
org = 'nyal'
url = 'http://10.0.109.133:8086'


load_figure_template('darkly')

app = Dash(external_stylesheets=[dbc.themes.DARKLY], backend='fastapi')

### Automated layouts imports and creation of tabs dictionary (one tab per layout)
layouts_folder = Path(__file__).parent / 'layouts'
tab_layouts = OrderedDict()
tab_labels = {}

for layout_file in layouts_folder.glob('*_layout.py'):
    module_name = f'layouts.{layout_file.stem}'
    module = importlib.import_module(module_name)

    tab_id = layout_file.stem.replace('_layout', '').lower() + '-tab'
    tab_layouts[tab_id] = getattr(module, 'layout')
    tab_labels[tab_id] = getattr(module, 'label', tab_id)  # fallback if label missing

tab_layouts.move_to_end('home-tab', last=False)
tab_layouts.move_to_end('custom-tab', last=True)
tab_layouts.move_to_end('alarm-tab', last=True)

### Automated callbacks import
callbacks_folder = Path(__file__).parent / 'callbacks'
for callback_file in callbacks_folder.glob('*_callbacks.py'):
    module_name = f'callbacks.{callback_file.stem}'
    module = importlib.import_module(module_name)


###########
# SIDEBAR #
###########
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '16rem',
    'padding': '2rem 1rem',
    'background-color': '#4f4e4d',
}

kart_logo = app.get_asset_url('kart_logo.png')
sidebar = html.Div(
    [
        dcc.Markdown(f'''
        <dccLink href='/'>
            <img src='{kart_logo}' width='100%' />       
        </dccLink> 
        ''',
        dangerously_allow_html=True
        ),
        html.Hr(),
        html.Div([
            html.Div(id='utc-time'),
            html.Div(id='local-time'),
        ]),
        html.Hr(),
        html.Div([
            html.Div(dbc.Switch(id='nn-alarm-switch')),
            html.Div('NN Alarm', className='lead'),
        ], className='hstack gap-2'),
        html.Div([
            html.Div(dbc.Switch(id='ns-alarm-switch')),
            html.Div('NS Alarm', className='lead'),
        ], className='hstack gap-2'),
        html.Hr(),
        dcc.Markdown(f'''
        External Links
        * [IVS 24h sessions] (https://ivscc.gsfc.nasa.gov/sessions/{year}/)
        * [IVS Intensive Sessions] (https://ivscc.gsfc.nasa.gov/sessions/intensive/{year}/)
        * [Live session] (https://ivslive.astrophy.u-bordeaux.fr/)
        * [SD System] (https://10.0.108.200/)
        ''',
        link_target="_blank"),
    ],
    style=SIDEBAR_STYLE,
)


###########
# CONTENT #
###########
CONTENT_STYLE = {
    'margin-left': '18rem',
    'margin-right': '2rem',
    'padding': '2rem 1rem',
}

tabs = [
    dbc.Tab(
        tab_id=tab_id,  # consistent tab_id naming
        label=tab_labels[tab_id],
    )
    for tab_id in tab_layouts
    if tab_id != 'custom-tab'
]

content = html.Div(
    [
        dbc.Row(
            [
                dbc.Tabs(
                    tabs,
                    id='tabs',
                    active_tab='home-tab'
                ),
                html.Div(id='tab-content'),
            ]
        )
    ], style=CONTENT_STYLE,
)


##################
# GENERAL LAYOUT #
##################
app.layout =(
    html.Div([
        sidebar,
        content,
    ]))


#--------------------
# Change the content displayed in the tabs
#--------------------
@callback(
    Output(component_id='tab-content', component_property='children'),
    Input(component_id='tabs', component_property='active_tab'),
)
def switch_tab(active_tab):
    print(active_tab)
    return tab_layouts[active_tab]


# ----------------------
# Change alarm state on button click
# ----------------------
@callback(
    Input(component_id='nn-alarm-switch', component_property='value'),
    Input(component_id='ns-alarm-switch', component_property='value'),
    prevent_initial_call=True,
)
def change_alarm_state(nn_switch, ns_switch):
    antenna = ctx.triggered_id.split('-')[0]
    status = nn_switch if antenna == 'nn' else ns_switch

    color = 'bg-success' if status else 'bg-light'
    set_props(f'{antenna}-alarm-switch', {'input_class_name': color})

    try:
        last = influx_methods.get_last('alarms', 'status', antenna)
        last = last.loc[0, '_value']
    except Exception:
        last = False

    if last == status:
        return

    print(f'{antenna} recording {status}')
    alarm_methods.record_status(status, antenna)


#--------------------
# Check the alarm status (on/off) and change the button accordingly
#--------------------
@callback(persistent=True,
          websocket=True)
async def check_alarm_status():
    ws = ctx.websocket
    last = {}
    for i in antennas:
        try:
            initial_status = influx_methods.get_last('alarms', 'status', i)
            if initial_status.empty:
                initial_status = False
            else:
                initial_status = initial_status.loc[0, '_value']
        except Exception:
            initial_status = False
            print(f'{i} recording {initial_status}')
            alarm_methods.record_status(initial_status, i)
            print('ok')

        last[i] = initial_status
        color = 'bg-success' if initial_status else 'bg-light'
        set_props(f'{i}-alarm-switch', {'value': initial_status})
        set_props(f'{i}-alarm-switch', {'input_class_name': color})

    while not ws.is_shutdown:
        for i in antennas:
            try:
                status = influx_methods.get_last('alarms', 'status', i)
                status = status.loc[0, '_value']
            except Exception:
                status = last[i]

            if status != last[i]:
                last[i] = status
                color = 'bg-success' if status else 'bg-light'
                set_props(f'{i}-alarm-switch', {'value': status})
                set_props(f'{i}-alarm-switch', {'input_class_name': color})
        await asyncio.sleep(2)


#--------------------
# Displays and change the clocks
#--------------------
@callback(
    persistent=True,
    websocket=True,
)
async def display_clocks():
    display = '%Y-%m-%d %H:%M:%S'
    clock_ws = ctx.websocket
    while not clock_ws.is_shutdown:
        time = datetime.now()
        utc = time.astimezone(ZoneInfo('UTC')).strftime(display)
        local = time.astimezone(ZoneInfo('Europe/Oslo')).strftime(display)
        set_props('utc-time', {'children': f'{utc} (UTC)'})
        set_props('local-time', {'children': f'{local} (Local)'})
        await asyncio.sleep(1)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
