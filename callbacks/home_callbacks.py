#!/home/oper/.venv/bin/python3

import pandas as pd
import os
from utils import functions
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from dash import (
    callback,
    Input,
    Output,
    no_update,
    set_props,
)


# ----------------------
# fill the schedule table
# ----------------------
def find_schedule():
    year = datetime.now().year
    session_file = os.path.join(os.path.dirname(__file__), f'../utils/session_list_{year}.csv')
    with open(session_file, 'r') as f:
        session_list = pd.read_csv(f)

    current_time = datetime.now()
    ten_days = datetime.now() + timedelta(days=10)
    session_list['Start (UTC)'] = pd.to_datetime(session_list['Start (UTC)'])
    session_list['End (UTC)'] = pd.to_datetime(session_list['End (UTC)'])
    df = session_list[session_list['Start (UTC)'].between(current_time, ten_days)]  # Keep only the next ten days of session

    df.loc[:, 'Status'] = 'Planned'

    # Check if a session is running
    current_ses = session_list[(session_list['Start (UTC)'] <= current_time) & (session_list['End (UTC)'] >= current_time)]
    if not current_ses.empty:
        current_ses.loc[:, 'Status'] = 'Running'
        df = pd.concat([current_ses, df])

    df['Start (UTC)'] = df['Start (UTC)'].dt.strftime('%Y-%m-%d %H:%M')
    df['End (UTC)'] = df['End (UTC)'].dt.strftime('%Y-%m-%d %H:%M')

    upcoming_ses = dbc.Table.from_dataframe(df.drop(columns='Status'), bordered=False, color='dark', hover=True, responsive=True, striped=True)

    tbody = upcoming_ses.children[1]
    for row, status in zip(tbody.children, df['Status']):
        if status == 'Running':
            for cell in row.children:
                cell.style = {'backgroundColor': '#00bc8c', 'color': 'white', 'boxShadow': 'none'}

    return upcoming_ses


# ----------------------
# Update the tab (on loading and interval timer)
# ----------------------
@callback(
Output(component_id='last-home-update', component_property='children'),
    Output(component_id='nn-fx-usage', component_property='figure'),
    Output(component_id='ns-fx-usage', component_property='figure'),
    Input(component_id='tabs', component_property='active_tab'),
    Input(component_id='home-interval', component_property='n_intervals')
)
def build_home_tab(active_tab, n):
    # print(f'Callback triggered in HOME, tab = {active_tab}')
    if active_tab != 'home-tab':
        return no_update, no_update, no_update

    print('Updating Home-tab')

    try:
        upcoming = find_schedule()
        set_props('sessions-table', {'children': upcoming})

    except Exception:
        pass

    last_update = 'Last update: ' + datetime.now().strftime('%H:%M:%S')

    return (last_update,
            functions.disk_usage_donut('nn'),
            functions.disk_usage_donut('ns'))
