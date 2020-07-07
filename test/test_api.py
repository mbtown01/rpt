import unittest
import requests
import json
import yaml
from time import sleep, strptime, mktime

from src.services import ApiDataBrokerService
from src.core import EventBus, ServiceProvider
from src.services import ThermostatService, OrmManagementService
from src.core.events import SensorDataChangedEvent

yamlText = """
config:
    thermostat.delta: 1.0
    thermostat.fanRunoutDuration: 30
    ui.backlightTimeout: 10
"""


class Test_ApiDataBroker(unittest.TestCase):

    def setup_method(self, method):
        self.serviceProvider = ServiceProvider()
        testTime = strptime('01/01/19 08:01:00', '%m/%d/%y %H:%M:%S')
        self.eventBus = EventBus(now=mktime(testTime))
        self.serviceProvider.installService(EventBus, self.eventBus)
        self.ormManagementService = OrmManagementService(isTestInstance=True)
        self.ormManagementService.setServiceProvider(self.serviceProvider)
        self.ormManagementService.importFromDict(yaml.load(yamlText))
        self.serviceProvider.installService(
            OrmManagementService, self.ormManagementService)
        self.thermostat = ThermostatService()
        self.thermostat.setServiceProvider(self.serviceProvider)
        self.serviceProvider.installService(
            ThermostatService, self.thermostat)
        self.thermostat.comfortMin = 68.0
        self.thermostat.comfortMax = 75.0

        apiDataBroker = ApiDataBrokerService()
        apiDataBroker.setServiceProvider(self.serviceProvider)
        sleep(0.1)

        self.testValueTemperature = 72.5
        self.testValuePressure = 1015.2
        self.testValueHumidity = 42.4
        self.eventBus.fireEvent(SensorDataChangedEvent(
            temperature=self.testValueTemperature,
            pressure=self.testValuePressure,
            humidity=self.testValueHumidity))
        self.eventBus.processEvents()

    def test_status(self):
        req = requests.get('http://localhost:5000/api/status')
        data = json.loads(req.text)
        self.assertTrue('version' in data)

    def test_settings(self):
        req = requests.get('http://localhost:5000/api/settings')
        data = json.loads(req.text)
        self.assertTrue('version' in data)
