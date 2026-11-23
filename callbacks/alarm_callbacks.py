#!/home/oper/.venv/bin/python3


import os
import traceback
from alarm import alarm_methods
from alarm import alarm_limits as al
from utils import influx_methods
from datetime import datetime
import pandas as pd
import asyncio
import dash_bootstrap_components as dbc
from dash import (
    ALL,
    callback,
    ctx,
    Input,
    no_update,
    Output,
    set_props,
)
from dash.exceptions import PreventUpdate

from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')
json_alarm_path = os.path.join(os.path.dirname(__file__), '../alarm/alarms_status.json')
alarm_log_file = os.path.join(os.path.dirname(__file__), '../alarm/alarms.log')
json_ack_file = os.path.join(os.path.dirname(__file__), '../alarm/alarms_ack.json')
antennas = ['nn', 'ns']
colors = dict(ok='bg-success',
              warning='bg-warning',
              alarm='bg-danger')
items = ['acs', 'fs', 'fmout', 'servos', 'cryo']


#-----------------------
# Fill the tables with the last 10 alarms for each antenna
#-----------------------
def fill_alarm_table():
    df = pd.read_csv(alarm_log_file, sep=':', header=None, dtype=str, names=['INFO', 'ALARM', 'date', 'time', 'Antenna', 'Item', 'Issue'])
    df['date&time'] = pd.to_datetime(df['date'].astype(str) + df['time'].astype(str), format='%Y%m%d%H%M%S')

    for ant in antennas:
        alarm_log = df[df['Antenna'] == ant].sort_values('date&time', ascending=False)
        alarm_log.drop(['INFO', 'ALARM', 'date', 'time'], inplace=True, axis=1)
        alarm_log = alarm_log.head(10)
        try:
            alarm_log['Issue'] = alarm_log['Issue'].str.replace('_', '\n', regex=False)
        except Exception:
            traceback.print_exc()

        try:
            last_ack = alarm_methods.read_json_partial(json_ack_file, ant)
            last_ack['date'] = datetime.strptime(last_ack['date'], '%Y%m%d%H%M%S')
            alarm_log = alarm_log[alarm_log['date&time'] >= last_ack['date']]
        except:
            traceback.print_exc()

        alarm_log['date&time'] = alarm_log['date&time'].dt.strftime('%Y-%m-%d %H:%M')
        table = dbc.Table.from_dataframe(alarm_log, bordered=False, color='dark',
                                         hover=True,
                                         responsive=True,
                                         striped=True,
                                         style={'whiteSpace': 'pre-line'})

        set_props(f'{ant}-last-alarm-table', {'children': table})


#-----------------------
# Acknowledging Alarms to not display them in the last alarm list
#-----------------------
@callback(
    Input(component_id='nn-acknowledge-button', component_property='n_clicks'),
    Input(component_id='ns-acknowledge-button', component_property='n_clicks'),
    prevent_initial_call=True
)
def acknowledge_alarms(nn_button, ns_button):
    triggered = ctx.triggered_id
    if triggered is not None:
        antenna = ctx.triggered_id.split('-')[0]
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        try:
            data = alarm_methods.read_json(json_ack_file)
            data[antenna] = {'date': now}
            alarm_methods.write_json(json_ack_file, data)
        except:
            data = {'nn': {'date': now},
                    'ns': {'date': now}
                    }
        alarm_methods.write_json(json_ack_file, data)
        fill_alarm_table()


#-----------------------
# Update the item color according to alarm status
#-----------------------
def change_color(item):
    # if item == 'acs':
    #     data = alarm_methods.read_json_partial(json_alarm_path, 'acs')
    #     if data is not None:
    #         set_props(f'acs-button', {'className': colors[data['status']]})
    # else:
    for ant in antennas:
        data = alarm_methods.read_json_partial(json_alarm_path, f'{item}_{ant}')
        if data is not None:
            set_props({'type': 'alarm-badge', 'item': item, 'antenna': ant}, {'className': colors[data['status']]})


# ----------------------
# Update the tab (on loading and interval timer)
# ----------------------
@callback(
    Output(component_id='last-alarms-update', component_property='children'),
    Input(component_id='tabs', component_property='active_tab'),
    Input(component_id='alarm-interval', component_property='n_intervals'),
)
def on_timing_interval(active_tab, n):
    if active_tab != 'alarm-tab':
        return no_update, no_update

    print('Updating alarm-tab')
    try:
        for ant in antennas:
            for item in items:
                try:
                    initial_status = influx_methods.get_last('alarms', ant, item)
                    if initial_status.empty:
                        initial_status = False
                    else:
                        initial_status = initial_status.loc[0, '_value']
                except Exception:
                    initial_status = False
                    influx_methods.record_status(ant, item, initial_status)

                color = 'bg-success' if initial_status else 'bg-light'
                change_color(item)
                set_props({'type': 'alarm-switch', 'item': item, 'antenna': ant}, {'value': initial_status})
                set_props({'type': 'alarm-switch', 'item': item, 'antenna': ant}, {'input_class_name': color})
    except Exception:
        pass
    try:
        fill_alarm_table()
    except Exception:
        pass

    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')
    return last_update


# ----------------------
# Change alarm state on switch click
# ----------------------
@callback(
    Input(component_id={'type': 'alarm-switch', 'item': ALL, 'antenna': ALL}, component_property='value'),
    prevent_initial_call=True,
)
def record_switch(values):
    switch_id = ctx.triggered_id
    if switch_id:
        item, ant = switch_id['item'], switch_id['antenna']
        value = ctx.triggered[0]['value']
        try:
            last = influx_methods.get_last('alarms', ant, item)  # Check last recorded state
            last = last.loc[0, '_value']
        except Exception:
            last = None
        if last != value:
            influx_methods.record_status(ant, item, value)



#--------------------
# Check the alarm status for each component and change switch accordingly
#--------------------
@callback(persistent=True,
          websocket=True)
async def check_alarm_status():
    ws = ctx.websocket
    last = {}
    for ant in antennas:
        last[ant] = {}
        for item in items:
            try:
                initial_status = influx_methods.get_last('alarms', ant, item)
                if initial_status.empty:
                    initial_status = False
                else:
                    initial_status = initial_status.loc[0, '_value']
            except Exception:
                initial_status = False
                influx_methods.record_status(ant, item, initial_status)

            last[ant][item] = initial_status
            color = 'bg-success' if initial_status else 'bg-light'
            set_props({'type': 'alarm-switch', 'item': item, 'antenna': ant}, {'value': initial_status})
            set_props({'type': 'alarm-switch', 'item': item, 'antenna': ant}, {'input_class_name': color})

    while not ws.is_shutdown:
        for ant in antennas:
            for item in items:
                try:
                    status = influx_methods.get_last('alarms', ant, item)
                    status = status.loc[0, '_value']
                except Exception:
                    status = last[ant][item]

                if status != last[ant][item]:
                    last[ant][item] = status
                    color = 'bg-success' if status else 'bg-light'
                    set_props({'type': 'alarm-switch', 'item': item, 'antenna': ant}, {'value': status})
                    set_props({'type': 'alarm-switch', 'item': item, 'antenna': ant}, {'input_class_name': color})
        await asyncio.sleep(2)
