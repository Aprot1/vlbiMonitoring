#!/home/oper/.venv/bin/python3

import mysql.connector
import pandas as pd
import plotly.express as px
import influxdb_client
from datetime import datetime
import warnings
from influxdb_client.client.warnings import MissingPivotFunction

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


# def make_df(tables):
#     time = []
#     values = []
#     for table in tables:
#         for record in table.records:
#             time.append(record.get_time())
#             values.append(record.get_value())
#
#     df = pd.DataFrame({'time': time, 'value': values})
#     df['valueMean'] = df['value'].rolling(10, center=True, min_periods=1).mean()
#
#     return df


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

    # if tables:
    #     if len(tables) > 0:
    #         for table in tables:
    #             for record in table.records:
    #                 time = record.get_time()
    #                 value = record.get_value()
    #     else:
    #         time, value = None, None
    # else:
    #     time, value = None, None

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

    # if tables:
    #     if len(tables) > 0:
    #         df = make_df(tables)
    #     else:
    #         df = None
    # else:
    #     df = None

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

    # if tables:
    #     if len(tables) > 0:
    #         df = make_df(tables)
    #     else:
    #         df = None
    # else:
    #     df = None

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


def date_to_mjd(date):
    """
    Convert a date into "Modified Julian Date" that is used in the database
    Input must be pandas timestamp type
    """
    # First convert to Julian Date using pandas built-in function
    jd = date.to_julian_date()
    # then Julian Day to Modified Julian Date
    mjd = jd - 2400000.5

    return mjd

if __name__ == '__main__':
    data = get_period('maser', 'fmout2gps', 'tic', '12')
    graph = px.line(data, x='time', y='value')
    graph.show()