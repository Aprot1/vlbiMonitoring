#!/home/oper/.venv/bin/python3

import json
import os
from utils import influx_methods
from datetime import datetime
from filelock import FileLock

from influxdb_client.rest import ApiException


antennas = ['nn', 'ns']
cryo_list = ['tint', 'tlna', 'tfeed', 'tcold', 'pressure']
json_alarm_file = os.path.join(os.path.dirname(__file__), 'alarms_status.json')
lock_path = os.path.join(os.path.dirname(__file__), 'alarms_status.json.lock')
lock = FileLock(lock_path)

# Influx DB parameters
TOKEN = 'Vh6U1Q2HWdxJi9fm2NwfA5lIz3GmU6EPyoEqy5qEXohcewUt1zEA_TaexRGegKyTQ58J23HbBtqXeu2FwXWa-w=='
ORG = 'nyal'
URL = 'http://10.0.109.133:8086'


#--------------
# Open and return the json file containing the statuses
#--------------
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



if __name__ == '__main__':
    run_checks()
