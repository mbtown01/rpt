from enum import Enum

from .GenericLcdDisplay import GenericLcdDisplay
from .GenericRgbLed import GenericRgbLed
from frosti.logging import log
from frosti.core import ServiceConsumer, ServiceProvider, EventBus, Event
from frosti.services import ThermostatService, OrmManagementService
from frosti.core.events import ThermostatStateChangedEvent, \
    SensorDataChangedEvent, PowerPriceChangedEvent, \
    SettingsChangedEvent


class GenericUserInterface(ServiceConsumer):

    class Button(Enum):
        UP = 1
        DOWN = 2
        MODE = 3
        NEXT = 4

    class ButtonPressedEvent(Event):
        def __init__(self, button):
            super().__init__(data={'button': button})

        @property
        def button(self):
            return super().data['button']

    def __init__(self,
                 lcd: GenericLcdDisplay,
                 rgbLeds: list = []):
        self.__lcd = lcd
        self.__rgbLeds = rgbLeds
        self.__lcd.setBacklight(True)
        self.__lastTemperature = 0.0
        self.__rowTwoOffset = 0
        self.__ledColorIndex = 0

        self.__rowTwoEntries = [
            "Target:             ",
            "State:              ",
            "Price:              ",
            "Program:            ",
        ]

        self.__ledColorList = []

    def setServiceProvider(self, provider: ServiceProvider):
        super().setServiceProvider(provider)

        ormManagementService = self._getService(OrmManagementService)
        self.__backlightTimeoutDuration = \
            ormManagementService.getConfigInt('ui.backlightTimeout')

        eventBus = self._getService(EventBus)
        self.__backlightTimeoutInvoker = eventBus.installTimer(
            frequency=self.__backlightTimeoutDuration,
            handler=self.__backlightTimeout, oneShot=True)
        self.__redrawAndRotateInvoker = eventBus.installTimer(
            frequency=5.0, handler=self.__redrawAndRotate)
        self.__ledAnimateInvoker = eventBus.installTimer(
            frequency=0.5, handler=self.__ledAnimate)
        self.__ledAnimateInvoker.disable()

        eventBus.installEventHandler(
            SettingsChangedEvent, self.__settingsChanged)
        eventBus.installEventHandler(
            SensorDataChangedEvent, self.__sensorDataChanged)
        eventBus.installEventHandler(
            ThermostatStateChangedEvent, self.__stateChanged)
        eventBus.installEventHandler(
            PowerPriceChangedEvent, self.__powerPriceChanged)
        eventBus.installEventHandler(
            GenericUserInterface.ButtonPressedEvent,
            self.__buttonPressedHandler)

        thermostat = self._getService(ThermostatService)
        self.__stateChanged(ThermostatStateChangedEvent(thermostat.state))

        self.__lcd.setBacklight(True)

    def backlightReset(self):
        if not self.__backlightTimeoutInvoker.isQueued:
            self.__lcd.setBacklight(True)
            self.__lcd.commit()
        self.__backlightTimeoutInvoker.reset()

    def __ledAnimate(self):
        listSize = len(self.__ledColorList)
        for rgbLed in self.__rgbLeds:
            rgbLed.setColor(self.__ledColorList[self.__ledColorIndex])
            # index = (index+1) % listSize
        self.__ledColorIndex = \
            (self.__ledColorIndex + 1) % listSize

    def __backlightTimeout(self):
        self.__lcd.setBacklight(False)

    def __sensorDataChanged(self, event: SensorDataChangedEvent):
        self.__lastTemperature = event.temperature
        self.redraw()

    def __buttonPressedHandler(self, event: ButtonPressedEvent):
        if self.__lcd.backlightStatus:
            # eventBus = self._getService(EventBus)
            thermostatService = self._getService(ThermostatService)
            self.backlightReset()

            if event.button == GenericUserInterface.Button.UP:
                thermostatService.modifyComfortSettings(1)
            elif event.button == GenericUserInterface.Button.DOWN:
                thermostatService.modifyComfortSettings(-1)
            elif event.button == GenericUserInterface.Button.MODE:
                thermostatService.nextMode()
            elif event.button == GenericUserInterface.Button.NEXT:
                self.__redrawAndRotate()
                self.__redrawAndRotateInvoker.reset()
        else:
            self.backlightReset()
            self.__lcd.hardReset()
            self.__lcd.clear()
            self.redraw()

    def __settingsChanged(self, event: SettingsChangedEvent):
        thermostatService = self._getService(ThermostatService)
        if thermostatService.isInPriceOverride:
            self.__ledColorList = [
                GenericRgbLed.Color.BLUE,
                GenericRgbLed.Color.CYAN,
                GenericRgbLed.Color.GREEN,
                GenericRgbLed.Color.YELLOW,
                GenericRgbLed.Color.RED,
                GenericRgbLed.Color.MAGENTA,
            ]
            self.__ledAnimateInvoker.reset()
        else:
            self.__ledAnimateInvoker.disable()
            for rgbLed in self.__rgbLeds:
                rgbLed.setColor(GenericRgbLed.Color.BLACK)

        heat = thermostatService.comfortMin
        cool = thermostatService.comfortMax
        name = thermostatService.currentProgramName
        mode = thermostatService.mode
        log.debug(f"[{name}] mode={mode} {heat:<3.0f}/{cool:>3.0f}")

        self.__rowTwoEntries[0] = f'Target:      {heat:<3.0f}/{cool:>3.0f}'
        self.__rowTwoEntries[3] = f'Program: {name:>11s}'
        self.__rowTwoOffset = 0
        self.__redrawAndRotateInvoker.reset()
        self.redraw()

    def __stateChanged(self, event: ThermostatStateChangedEvent):
        self.__rowTwoEntries[1] = f'State: {event.state:>13s}'
        self.__rowTwoOffset = 1
        self.__redrawAndRotateInvoker.reset()
        self.redraw()

    def __powerPriceChanged(self, event: PowerPriceChangedEvent):
        self.__rowTwoEntries[2] = f'Price:  ${event.price:.4f}/kW*h'
        self.__rowTwoOffset = 2
        self.__redrawAndRotateInvoker.reset()
        self.redraw()

    def __redrawAndRotate(self):
        self.redraw()
        self.__rowTwoOffset = (self.__rowTwoOffset + 1) % \
            len(self.__rowTwoEntries)

    def redraw(self):
        thermostatService = self._getService(ThermostatService)

        now = self.__lastTemperature
        mode = thermostatService.mode
        self.__lcd.update(0, 0, f'Now: {now:<5.1f}    {mode:>6s}')
        self.__lcd.update(1, 0, self.__rowTwoEntries[self.__rowTwoOffset])
        self.__lcd.update(3, 0, r'UP  DOWN  MODE  NEXT')
        self.__lcd.commit()