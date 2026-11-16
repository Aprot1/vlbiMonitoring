#!/home/oper/.venv/bin/python3


import os

from alarm import alarm_methods
from alarm import alarm_limits as al
from utils import influx_methods
from datetime import datetime
import pandas as pd
import dash_bootstrap_components as dbc
from dash import (
    callback,
    ctx,
    Input,
    no_update,
    Output,
    set_props,
)

from dash_bootstrap_templates import load_figure_template

load_figure_template('darkly')
json_alarm_path = os.path.join(os.path.dirname(__file__), '../alarm/alarms_status.json')
alarm_log_file = os.path.join(os.path.dirname(__file__), '../alarm/alarms.log')
json_ack_file = os.path.join(os.path.dirname(__file__), '../alarm/alarms_ack.json')
antennas = ['nn', 'ns']
colors = dict(ok='bg-success',
              warning='bg-warning',
              alarm='bg-danger')
items_list = ['acs', 'servos', 'fmout', 'fs', 'cryo']


#-----------------------
# Fill the tables with the last 10 alarms for each antenna
#-----------------------
def fill_alarm_table():
    df = pd.read_csv(alarm_log_file, sep=':', header=None, dtype=str, names=['INFO', 'ALARM', 'date', 'time', 'Antenna', 'Item', 'Issue'])
    df['date&time'] = pd.to_datetime(df['date'] + df['time'], format='%Y%m%d%H%M%S')


    for ant in antennas:
        alarm_log = df[df['Antenna'] == ant].sort_values('date&time', ascending=False)
        alarm_log.drop(['INFO', 'ALARM', 'date', 'time'], inplace=True, axis=1)
        alarm_log = alarm_log.head(10)
        try:
            alarms_log['Issue'] = alarms_log['Issue'].str.replace('_', '\n', regex=False)
        except Exception:
            pass

        try:
            last_ack = alarm_methods.read_json_partial(json_ack_file, ant)
            last_ack['date'] = datetime.strptime(last_ack['date'], '%Y%m%d%H%M%S')
            alarm_log = alarm_log[alarm_log['date&time'] >= last_ack['date']]
        except:
            pass

        alarm_log['date&time'] = alarm_log['date&time'].dt.strftime('%Y-%m-%d %H:%M')
        table = dbc.Table.from_dataframe(alarm_log, bordered=False, color='dark',
                                         hover=True,
                                         responsive=True,
                                         striped=True,
                                         style={'whiteSpace': 'pre-line'})

        set_props(f'{ant}-alarm-table', {'children': table})


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
    if item == 'acs':
        data = alarm_methods.read_json_partial(json_alarm_path, 'acs')
        if data is not None:
            set_props(f'acs-button', {'className': colors[data['status']]})
    else:
        for ant in antennas:
            data = alarm_methods.read_json_partial(json_alarm_path, f'{item}_{ant}')
            if data is not None:
                set_props(f'{item}-{ant}-button', {'className': colors[data['status']]})


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
    for item in items_list:
        change_color(item)

    fill_alarm_table()

    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')
    return last_update
