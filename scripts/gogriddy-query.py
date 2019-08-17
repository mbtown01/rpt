#!/usr/bin/python3

import os
import configparser
import requests
import json
from influxdb import InfluxDBClient


dir_name = os.path.dirname(os.path.realpath(__file__))
conf = dir_name + '/../etc/gogriddy-config.conf'

config = configparser.ConfigParser()
config.read(conf)

meterID = config.get('default', 'meterID')
memberID = config.get('default', 'memberID')
settlement_point = config.get('default', 'settlement_point')
api_url = config.get('default', 'api_url')
influxdb_protocol = config.get('influxdb', 'protocol')
influxdb_host = config.get('influxdb', 'host')
influxdb_port = config.get('influxdb', 'port')
influxdb_dbname = config.get('influxdb', 'dbname')

client = InfluxDBClient(host=influxdb_host, port=influxdb_port)
client.switch_database(influxdb_dbname)

payload = {
    'meterID': meterID, 'memberID': memberID,
    'settlement_point': settlement_point
}

r = requests.post(api_url, data=json.dumps(payload))
j = json.loads(r.text)

price_date = j["now"]["date_local_tz"]
current_price = j["now"]["price_ckwh"]
value_score = j["now"]["value_score"]
wstd_dev_ckwh = j["now"]["std_dev_ckwh"]
seconds_until_refresh = j["seconds_until_refresh"]
future_date = j["forecast"][0]["date_local_tz"]
future_price = j["forecast"][0]["price_ckwh"]
future_wstd_dev_ckwh = j["forecast"][0]["std_dev_ckwh"]
future_value_score = j["forecast"][0]["value_score"]

influxdb_entry = \
    f'electric_cost,price_date={price_date},future_date={future_date} ' + \
    f'future_price={future_price},current_price={current_price},' + \
    f'value_score={value_score},future_value_score={future_value_score},' + \
    f'wstd_dev_ckwh={wstd_dev_ckwh},' + \
    f'future_wstd_dev_ckwh={future_wstd_dev_ckwh},' + \
    f'seconds_until_refresh={seconds_until_refresh}'

client.write_points(influxdb_entry, protocol=influxdb_protocol)
