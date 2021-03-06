from .OrmManagementService import OrmManagementService
from frosti.core import ServiceConsumer, ServiceProvider, EventBus
from frosti.core.events import SensorDataChangedEvent, SettingsChangedEvent


class EnvironmentSamplingService(ServiceConsumer):
    """ Holds a GenericEnvironmentSensor and at a specified frequency
    takes a sampling and fires a SensorDataChangedEvent """

    def setServiceProvider(self, provider: ServiceProvider):
        super().setServiceProvider(provider)

        ormManagementService = self._getService(OrmManagementService)
        self.__temperatureScale = ormManagementService.getConfigFloat(
            'environment.temperature.scale')
        self.__temperatureTranslate = ormManagementService.getConfigFloat(
            'environment.temperature.translate')
        self.__pressureScale = ormManagementService.getConfigFloat(
            'environment.pressure.scale')
        self.__pressureTranslate = ormManagementService.getConfigFloat(
            'environment.pressure.translate')
        self.__humidityScale = ormManagementService.getConfigFloat(
            'environment.humidity.scale')
        self.__humidityTranslate = ormManagementService.getConfigFloat(
            'environment.humidity.translate')

        eventBus = self._getService(EventBus)
        eventBus.installEventHandler(
            SettingsChangedEvent, self.__settingsChanged)
        self.__sampleSensorsInvoker = eventBus.installTimer(
            frequency=5.0, handler=self.__sampleSensors)
        self.__sampleSensors()

    @property
    def temperature(self):
        return self._getRawTemperature() * self.__temperatureScale + \
            self.__temperatureTranslate

    @property
    def pressure(self):
        return self._getRawPressure() * self.__pressureScale + \
            self.__pressureTranslate

    @property
    def humidity(self):
        return self._getRawHumidity() * self.__humidityScale + \
            self.__humidityTranslate

    def _getRawTemperature(self):
        raise NotImplementedError()

    def _getRawPressure(self):
        raise NotImplementedError()

    def _getRawHumidity(self):
        raise NotImplementedError()

    def __settingsChanged(self, event: SettingsChangedEvent):
        """ If any settings have changed, wait the full time before getting
        another reading from the sensors.  This prevents a user quickly
        changing settings from causing the thermostat to change states """
        self.__sampleSensorsInvoker.reset()

    def __sampleSensors(self):
        eventBus = self._getService(EventBus)
        eventBus.fireEvent(SensorDataChangedEvent(
            temperature=self.temperature,
            pressure=self.pressure,
            humidity=self.humidity,
        ))
