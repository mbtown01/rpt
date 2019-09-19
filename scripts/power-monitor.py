#!/usr/bin/python3

import json
import sys

from time import sleep
from xml.etree import ElementTree

# pylint: disable=import-error
from influxdb import InfluxDBClient
import serial
from os.path import dirname
sys.path.append(dirname(__file__)+'/../')
from src.config import config
# pylint: enable=import-error


# <InstantaneousDemand>
#   <DeviceMacId>0xd8d5b9000000054e</DeviceMacId>
#   <MeterMacId>0x00078100011a4c66</MeterMacId>
#   <TimeStamp>0x25117e9f</TimeStamp>
#   <Demand>0x001540</Demand>
#   <Multiplier>0x00000001</Multiplier>
#   <Divisor>0x000003e8</Divisor>
#   <DigitsRight>0x03</DigitsRight>
#   <DigitsLeft>0x06</DigitsLeft>
#   <SuppressLeadingZero>Y</SuppressLeadingZero>
# </InstantaneousDemand>


def parseBlock(lines, elementName, attrName):
    xml_text = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<data>\n"
    for line in lines:
        xml_text += str(line)
    xml_text += "</data>"

    parser = ElementTree.XMLParser(encoding="utf-8")
    root = ElementTree.fromstring(xml_text, parser=parser)
    element = root.find(elementName)

    value = int(element.find(attrName).text, 16)
    multiplier = max(1, int(element.find("Multiplier").text, 16))
    divisor = max(1, int(element.find("Divisor").text, 16))
    return value * multiplier / float(divisor)


def sendCommand(ser, command: str, refresh: str=None):
    ser.write(b"<Command><Name>" + command.encode('utf-8') + b"</Name>")
    if refresh is not None:
        ser.write(b"<Refresh>" + refresh.encode('utf-8') + b"</Refresh>")
    ser.write(b"</Command>")


# Connect and reuse the serial interface until complete
ser = serial.Serial('/dev/ttyUSB1', 115200, timeout=1)

sendCommand(ser, 'set_schedule_default')
sendCommand(ser, 'get_instantaneous_demand', 'Y')
sendCommand(ser, 'get_current_summation_delivered', 'Y')
ser.flush()

lines = []
while True:
    for line in ser.readlines():
        line = line.decode('ascii').strip()
        print('FOOBAR ', line)
        lines.append(line)

    if len(lines) and lines[0].startswith("<InstantaneousDemand>"):
        cmdLines = []
        while not lines[0].startswith("</InstantaneousDemand>"):
            cmdLines.append(lines.pop(0))
        cmdLines.append(lines.pop(0))
        result = parseBlock(cmdLines, 'InstantaneousDemand', 'Demand')
        print(f'Demand={result}')

    if len(lines) and lines[0].startswith("<CurrentSummationDelivered>"):
        cmdLines = []
        while not lines[0].startswith("</CurrentSummationDelivered>"):
            cmdLines.append(lines.pop(0))
        cmdLines.append(lines.pop(0))
        result = parseBlock(
            cmdLines, 'CurrentSummationDelivered', 'SummationDelivered')
        print(f'SummationDelivered={result}')


# if config.influxdb_enabled:
#     client = InfluxDBClient(
#         host=config.influxdb_host, port=config.influxdb_port)
#     client.switch_database(config.influxdb_dbName)

    # <Command><Name>get_current_summation_delivered</Name><Refresh>N</Refresh></Command>
    # <Command><Name>get_instantaneous_demand</Name><Refresh>N</Refresh></Command>
    # <Command><Name>get_schedule</Name></Command>

    # influxdb_entry = \
    #     f'electric_cost,price_date={j["now"]["date_local_tz"]},' + \
    #     f'future_date={j["forecast"][0]["date_local_tz"]} ' + \
    #     f'future_price={j["forecast"][0]["price_ckwh"]},' + \
    #     f'current_price={j["now"]["price_ckwh"]},' + \
    #     f'value_score={j["now"]["value_score"]},' + \
    #     f'future_value_score={j["forecast"][0]["value_score"]},' + \
    #     f'wstd_dev_ckwh={j["now"]["std_dev_ckwh"]},' + \
    #     f'future_wstd_dev_ckwh={j["forecast"][0]["std_dev_ckwh"]},' + \
    #     f'seconds_until_refresh={j["seconds_until_refresh"]},' + \
    #     f'demand={demand},' + \
    #     f'meter={meter}'

    # # print(influxdb_entry)
    # client.write_points(influxdb_entry, protocol=config.influxdb_protocol)