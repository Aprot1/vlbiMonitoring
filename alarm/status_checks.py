#!/home/oper/.venv/bin/python3

import os
import json
import subprocess
from filelock import FileLock
import influxdb_client
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import alarm_limits as lm
import radio_alarm


monitoring_path = '/home/oper/Antoine/monitoring/dashApp'
antennas = ['nn', 'ns']
items = ['acs', 'servos', 'fmout', 'fs', 'cryo']
cryo_list = ['tint', 'tlna', 'tfeed', 'tcold', 'pressure']
json_alarm_file = os.path.join(os.path.dirname(__file__), 'alarms_status.json')
lock_path = os.path.join(os.path.dirname(__file__), 'alarms_status.json.lock')
alarm_log_file = os.path.join(os.path.dirname(__file__), 'alarms.log')
lock = FileLock(lock_path)
alarm_logger = logging.getLogger('ALARM')
warning_logger = logging.getLogger('WARNING')
logging.basicConfig(filename=alarm_log_file, level=logging.INFO)

# Influx DB parameters
TOKEN = 'Vh6U1Q2HWdxJi9fm2NwfA5lIz3GmU6EPyoEqy5qEXohcewUt1zEA_TaexRGegKyTQ58J23HbBtqXeu2FwXWa-w=='
ORG = 'nyal'
URL = 'http://10.0.109.133:8086'


#-------------------
# Execute influxDB query
#-------------------
def execute_query(query):
    try:
        client = influxdb_client.InfluxDBClient(url=URL, token=TOKEN, org=ORG)
        query_api = client.query_api()
        df = query_api.query(query)
        client.close()
    except Exception:
        df = None

    return df


#-------------------
# Get the last data
#-------------------
def get_last(bucket, measurement, field, tag=''):
    if tag != '':
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: 0)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> filter(fn: (r) => r["antenna"] == "{tag}")
              |> last()
            '''
    else:
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: 0)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> last()
            '''

    tables = execute_query(query)

    if tables:
        if len(tables) > 0:
            for table in tables:
                for record in table.records:
                    time = record.get_time()
                    value = record.get_value()
        else:
            time, value = None, None

    return time, value


#-------------------
# Check the last values if they are equal
#-------------------
def last_equals(bucket, measurement, field, tag=''):
    if tag != '':
        query = f'''
                    from(bucket: "{bucket}")
                      |> range(start: -1d)
                      |> filter(fn: (r) => r._measurement == "{measurement}")
                      |> filter(fn: (r) => r._field == "{field}")
                      |> filter(fn: (r) => r["antenna"] == "{tag}")
                      |> tail(n: 3)
                    '''
    else:
        query = f'''
                    from(bucket: "{bucket}")
                      |> range(start: -1h)
                      |> filter(fn: (r) => r._measurement == "{measurement}")
                      |> filter(fn: (r) => r._field == "{field}")
                      |> tail(n: 3)
                    '''

    tables = execute_query(query)

    value = []
    equal = False
    if tables:
        if len(tables) > 0:
            for table in tables:
                for record in table.records:
                    time = record.get_time()
                    value.append(record.get_value())
        else:
            pass

    if len(value) > 1:
        if value[0] == value[1]:
            equal = True

    return equal


#--------------
# Write a specific bash command and return the outputs
#--------------
def get_ssh_command(cmd):
    stdout, stderr = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    return stdout.decode(), stderr.decode()


#--------------
# Get the ACS status
#--------------
def get_acs_status():
    cmd = 'ssh nymgr@10.0.109.10 ps afx | grep acscommandcenter'
    out, err = get_ssh_command(cmd)
    now = datetime.now().strftime('%H:%M:%S')
    if not err:
        if 'acscommandcenter' not in out:
            status = 'alarm'
            issue = 'acs software not running'
        else:
            status = 'ok'
            issue = None
    else:
        status = 'alarm'
        issue = 'acs computer not reachable'

    output = {
        'date': now,
        'status': status,
        'issue': issue,
    }

    return output


#--------------
# Get the fmout status/value
#--------------
def get_fmout_status(antenna):
    cmd = 'ssh nymgr@10.0.109.10 ps afx | grep fmout'
    out, err = get_ssh_command(cmd)
    to_check = 'fmout-gps-' + antenna

    time = datetime.now().strftime('%H:%M:%S')
    if not err:
        if to_check in out:
            equal = last_equals('maser', 'fmout2gps', 'tic', tag=antenna)
            if equal:
                status = 'alarm'
                issue = 'Last fmout values are equal'
            else:
                status = 'ok'
                issue = None
        else:
            status = 'alarm'
            issue = 'fmout not running'
    else:
        status = 'alarm'
        issue = 'Couldn\'t reach ACS computer'

    output = {
        'date': time,
        'status': status,
        'issue': issue,
    }

    return output


#--------------
# Get the fs status
#--------------
def get_fs_status(antenna):
    if antenna == 'nn':
        ip = '10.0.109.39'
    else:
        ip = '10.0.109.38'

    cmd = f'ssh oper@{ip} ps afx | grep fsclient'
    out, err = get_ssh_command(cmd)

    if not err:
        if 'fsclient' not in out:
            status = 'alarm'
            issue = 'fsclient is not running'
        else:
            status = 'ok'
            issue = None
    else:
        status = 'alarm'
        issue = 'fs computer not reachable'

    output = {
        'date': datetime.now().strftime('%H:%M:%S'),
        'status': status,
        'issue': issue,
    }

    return output


#--------------
# Get the servos status
#--------------
def get_servos_status(antenna):
    cmd = f'ssh nymgr@10.0.109.10 python check_servosystem.py {antenna}'
    out, err = get_ssh_command(cmd)

    if not err:
        if 'ERROR' in out:
            status = 'alarm'
            out = out.split('\n')
            issue = ''
            for i in out:
                if 'ERROR' in i:
                    text = i.split(':')[1].lstrip()
                    issue += f'{i}' if issue == '' else f'_{i}'
        else:
            status = 'ok'
            issue = None
    else:
        status = 'alarm'
        issue = 'Couldn\'t reach servosystem on the ACS'

    output = {
        'date': datetime.now().strftime('%H:%M:%S'),
        'status': status,
        'issue': issue,
    }

    return output


#--------------
# Get the receivers cryo status
#--------------
def get_cryo_status(antenna):
    status = 'ok'
    issue = ''
    for i in cryo_list:
        time, value = get_last('cryo', i, antenna)
        if value >= float(lm.cryo[i]):
            status = 'alarm'
            issue += f'{i} too high' if issue == '' else f'_{i} too high'

    if status == 'ok':
        issue = None

    output = {
        'date': datetime.now().strftime('%H:%M:%S'),
        'status': status,
        'issue': issue,
    }

    return output


#--------------
# Run checks on all different items to be monitored and write the status inside a Json file
#--------------
def run_checks():
    statuses = {}
    for ant in antennas:
        statuses[f'acs_{ant}'] = get_acs_status()
        statuses[f'fs_{ant}'] = get_fs_status(ant)
        statuses[f'fmout_{ant}'] = get_fmout_status(ant)
        statuses[f'servos_{ant}'] = get_servos_status(ant)
        statuses[f'cryo_{ant}'] = get_cryo_status(ant)

    write_json(json_alarm_file, statuses)


#-------------------
# Open and return a json file
#-------------------
def read_json(file):
    with lock:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                f.close()
            return data
        except(FileNotFoundError, json.JSONDecodeError):
            print('JSON file not found or couldn\'t be read')
            return None


#-------------------
# Read the JSON file and return the part needed
#-------------------
def read_json_partial(file, item):
    with lock:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                f.close()
            return data[item]
        except(FileNotFoundError, json.JSONDecodeError):
            print('JSON file not found or couldn\'t be read')
            return None


#-------------------
# Create/modify the JSON file
#-------------------
def write_json(file, data):
    with lock:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            f.close()


#-------------------
# check the json file for alarms
#-------------------
def check_alarm():
    alarm_list = {'nn': [], 'ns': []}
    data = read_json(json_alarm_file)  # read the json file to check for alarms
    if data is not None:
        print('Checking values')
        for item, values in data.items():
            if values['status'] == 'alarm':  # There is an alarm
                component = item.split('_')[0]
                if len(item.split('_')) > 1:
                    antenna = item.split('_')[1]
                    alarm_list[antenna].append(component)
                else:
                    for i in antennas:
                        alarm_list[i].append(component)
    return alarm_list


#-------------------
# Main part of the script
#-------------------
run_checks()    # Check all the different statuses and write them into the json file


alarm_active = {}
for ant in antennas:  # Checking the ON/OFF alarm status for each antenna
    alarm_active[ant] = {}
    for item in items:
        query = f'''
            from(bucket: "alarms")
              |> range(start: 0)
              |> filter(fn: (r) => r._measurement == "{ant}")
              |> filter(fn: (r) => r._field == "{item}")
              |> last()
            '''

        tables = execute_query(query)

        if len(tables) > 0:
            for table in tables:
                for record in table.records:
                    time = record.get_time()
                    status = record.get_value()

        alarm_active[ant][item] = status

print(alarm_active)
alarm_to_send = False
alarm_list = check_alarm()
print(alarm_list)

for ant, items in alarm_list.items():
    if alarm_active[ant]:
        for item in items:
            if alarm_active[ant][item]:
                data = read_json_partial(json_alarm_file, f'{item}_{ant}')
                issue = data['issue']
                time = datetime.now()
                utc = time.astimezone(ZoneInfo('UTC')).strftime('%Y%m%d:%H%M%S')
                alarm_logger.info(f'{utc}:{ant}:{item}:{issue}')
                print(f'logged {utc}:{ant}:{item}:{issue}')

                if not alarm_to_send:
                    alarm_to_send = True

# Sending the alarm if needed
if alarm_to_send:
    radio_alarm.send_alarm()
    # print(f'Sending alarm')
    alarm_to_send = False
