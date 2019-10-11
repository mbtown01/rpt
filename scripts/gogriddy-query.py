#!/usr/bin/python3

import requests
import json
import sys

from xml.etree import ElementTree

# pylint: disable=import-error
from influxdb import InfluxDBClient
import serial
from os.path import dirname
sys.path.append(dirname(__file__)+'/../')
from src.config import Config
# pylint: enable=import-error

config = Config()
if not config.resolve("influxdb", "enabled", False):
    raise RuntimeError('InfluxDB is not configured')

client = InfluxDBClient(
    host=config.resolve("influxdb", "host"),
    port=config.resolve("influxdb", "port")
)
client.switch_database(config.resolve("influxdb", "dbName"))

payload = {
    'meterID': config.resolve("gogriddy", "meterId"),
    'memberID': config.resolve("gogriddy", "meterId"),
    'settlement_point': config.resolve("gogriddy", "settlementPoint")
}

r = requests.post(
    config.resolve("gogriddy", "apiUrl"), data=json.dumps(payload))
j = json.loads(r.text)

influxdb_entry = \
    f'electric_cost,price_date={j["now"]["date_local_tz"]},' + \
    f'future_date={j["forecast"][0]["date_local_tz"]} ' + \
    f'future_price={j["forecast"][0]["price_ckwh"]},' + \
    f'current_price={j["now"]["price_ckwh"]},' + \
    f'value_score={j["now"]["value_score"]},' + \
    f'future_value_score={j["forecast"][0]["value_score"]},' + \
    f'wstd_dev_ckwh={j["now"]["std_dev_ckwh"]},' + \
    f'future_wstd_dev_ckwh={j["forecast"][0]["std_dev_ckwh"]},' + \
    f'seconds_until_refresh={j["seconds_until_refresh"]}'

client.write_points(
    influxdb_entry, protocol=config.resolve("influxdb", "protocol"))
