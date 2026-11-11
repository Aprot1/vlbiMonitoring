#!/home/oper/.venv/bin/python3

import pandas as pd
import requests
from datetime import datetime, timedelta
import re
import json
import os


# ----------------------
# Scan the session file in parameter to gather the sessions where nn and/or ns are participating
# ----------------------
def check_for_session(file):
    session_list = pd.DataFrame(columns=['Session', 'Start (UTC)', 'End (UTC)', 'Antenna', 'Correlator'])
    session_block = False
    station_block = False
    our_session = False

    session_code = re.compile(r'session-id.+/([a-z]+\d+)/')
    station_id = re.compile(r'class="station-id ">')
    session_date_time = re.compile(r'class="start">(.+) (.+) <')
    correlator_re = re.compile(r'class="correlator(.+)>([A-Z]*)<')
    duration_re = re.compile(r'class="duration">(\d+:\d+)<')

    for line in file:  # Search for 24h sessions
        if not session_block:
            m = session_code.search(line)
            if m:
                session_block = True
                session = m.group(1)

        elif station_block: # find out if Nn/Ns are participating
            station_block = False
            sta = re.search(r'>(N[n|s])<', line)
            if sta:
                our_session = True
                sta = sta.group(1)
                if session_list[session_list['Session'] == session].empty:
                    session_list.loc[len(session_list)] = [session, start, end, sta, None]  # Add the session to the list
                else:   # if line already axists, just add the other antenna
                    session_list.loc[len(session_list)-1, ['Antenna']] =  session_list.loc[len(session_list)-1, ['Antenna']] + f'/{sta}'

        else:
            if 'analysis-center' in line:   # End of "session block"
                session_block = False
            else:
                dt = session_date_time.search(line) # get the session time
                dur = duration_re.search(line)
                if dt:
                    ses_date = dt.group(1)
                    ses_time = dt.group(2)
                    start = ses_date + ses_time
                    start = datetime.strptime(start, '%Y-%m-%d%H:%M')
                if dur:
                    found = dur.group(1).split(':')
                    # print(found)
                    end = start + timedelta(hours=int(found[0]))
                    # end = datetime.strptime(end, '%Y-%m-%d%H:%M')

                m = station_id.search(line)
                if m:
                    station_block = True

                cor = correlator_re.search(line)

                if cor and our_session: # get the correlator
                    our_session = False
                    cor = cor.group(2)
                    session_list.loc[len(session_list) - 1, 'Correlator'] = cor

    return session_list


# ----------------------
# add the operators from ivs session browser
# ----------------------
def add_operators(df):
    op_file = '/home/oper/.config/ivs-sessions-browser/operator_assignments.json'
    with open(op_file, 'r') as f:
        operators = json.load(f)

    operators = pd.DataFrame(operators)

    df['Session'] = df['Session'].str.upper()
    df2 = df.merge(operators, left_on='Session', right_index=True, how='left')
    df2['Session'] = df2['Session'].str.lower()
    df2.rename(columns={'assignments': 'Operator'}, inplace=True)
    return df2


######
# Main function
######
def get_schedule(year=datetime.now().year, op=False):
    url_24 = f'https://ivscc.gsfc.nasa.gov/sessions/{year}/'
    url_intensive = f'https://ivscc.gsfc.nasa.gov/sessions/intensive/{year}/'
    f_sessions = os.path.join(os.path.dirname(__file__), f'session_list_{year}.csv')

    r_24 = requests.get(url_24, verify=False)
    r_intensive = requests.get(url_intensive, verify=False)

    lines_24 = r_24.text.splitlines()
    lines_intensive = r_intensive.text.splitlines()

    sessions_24 = check_for_session(lines_24)
    sessions_int = check_for_session(lines_intensive)

    session_list = pd.concat([sessions_24, sessions_int], ignore_index=True)
    if op:
        session_list = add_operators(session_list)

    session_list.sort_values(['Start (UTC)'], ascending=True, inplace=True)

    session_list.to_csv(f_sessions, index=False)


if __name__ == '__main__':
    get_schedule(op=True)
