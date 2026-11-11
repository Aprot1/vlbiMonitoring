#!/home/oper/.venv/bin/python3


import mysql.connector
from datetime import datetime


def get_data(database, query):
    """
    Connect to the mysql database on the NyMitra
    Return the data received by the query in a dataframe
    """
    conn = mysql.connector.connect(
        host='10.0.109.10',
        user='oper',
        password='NyalesunD',
        database=database
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # data = pd.DataFrame(data, columns=columns)
    # pd.set_option('display.float_format', '{:.2E}'.format)
    # data.set_index('date', inplace=True)

    return data


def get_current_session():
    today = datetime.today().strftime('%Y-%m-%d')
    query = 'SELECT DateObs,Id,UT,Source,Az,El FROM nyinfo_2 ORDER BY Id DESC LIMIT 1'
    data = get_data('observations', query)[0]
    if today == str(data['DateObs']):
        return data
    return None


if __name__ == '__main__':
    get_current_session()