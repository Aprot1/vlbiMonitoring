#!/home/oper/.venv/bin/python3

import mysql.connector
import pandas as pd
import plotly.express as px
from datetime import datetime
import warnings
from influxdb_client.client.warnings import MissingPivotFunction
import influxdb_client
from influxdb_client import Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

warnings.simplefilter("ignore", MissingPivotFunction)

TOKEN = 'Vh6U1Q2HWdxJi9fm2NwfA5lIz3GmU6EPyoEqy5qEXohcewUt1zEA_TaexRGegKyTQ58J23HbBtqXeu2FwXWa-w=='
ORG = 'nyal'
URL = 'http://10.0.109.133:8086'


tag_field = dict(t4='maser', nn='antenna', ns='antenna')

# Execute influxDB query
def execute_query(query):
    try:
        client = influxdb_client.InfluxDBClient(url=URL, token=TOKEN, org=ORG)
        query_api = client.query_api()
        df = query_api.query_data_frame(query)
        client.close()
    except Exception:
        df = None

    return df


# Get the last data
def get_last(bucket, measurement, field, tag=''):
    if tag != '':
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: 0)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> filter(fn: (r) => r["{tag_field[tag]}"] == "{tag}")
              |> last()
              |> keep(columns: ["_time", "_value"])
            '''
    else:
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: 0)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> last()
              |> keep(columns: ["_time", "_value"])
            '''

    df = execute_query(query).drop(columns=['result', 'table'])

    return df



# Get the last PERIOD hours of data
def get_hours(bucket, measurement, field, hours, tag=''):
    if tag != '':
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: -{hours}h)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> filter(fn: (r) => r["{tag_field[tag]}"] == "{tag}")
              |> keep(columns: ["_time", "_value"])
            '''
    else:
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: -{hours}h)
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> keep(columns: ["_time", "_value"])
            '''

    df = execute_query(query).drop(columns=['result', 'table'])
    df['valueMean'] = df['_value'].rolling(10, center=True, min_periods=1).mean()

    return df


# Get data according to the range (start and stop on the calendar widget)
def get_range(bucket, measurement, field, time, tag=''):
    start = datetime.strptime(time[0], '%Y-%m-%d').isoformat() + 'Z'
    stop = datetime.strptime(time[1], '%Y-%m-%d').isoformat() + 'Z'
    if tag != '':
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start}, stop: {stop})
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> filter(fn: (r) => r["{tag_field[tag]}"] == "{tag}")
              |> keep(columns: ["_time", "_value"])
            '''
    else:
        query = f'''
            from(bucket: "{bucket}")
              |> range(start: {start}, stop: {stop})
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> filter(fn: (r) => r._field == "{field}")
              |> keep(columns: ["_time", "_value"])
            '''

    df = execute_query(query).drop(columns=['result', 'table'])
    df['valueMean'] = df['_value'].rolling(10, center=True, min_periods=1).mean()

    return df


# get data from the ACS database (SQL query)
def get_acs_data(database, query):
    """
    Connect to the ACS database and return the connection ID
    """
    conn = mysql.connector.connect(
        host='10.0.109.10',
        user='oper',
        password='NyalesunD',
        database=database
    )
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    return data


#--------------
# Record the status (ON/OFF) of the alarm in the influxdb
#--------------
def record_status(antenna, item, status):
    client = influxdb_client.InfluxDBClient(url=URL, token=TOKEN, org=ORG)
    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = (Point(antenna)
                 .time(datetime.now(), write_precision=WritePrecision.S)
                 .field(item, status))
        write_api.write(bucket='alarms', record=point)
    except ApiException as e:
        print('Influx API error:', e.status, e.reason, e.body)
    except Exception as e:
        print('Other error:', type(e).__name__, e)
    finally:
        client.close()


if __name__ == '__main__':
    data = get_period('maser', 'fmout2gps', 'tic', '12')
    graph = px.line(data, x='time', y='value')
    graph.show()
