import unittest
import sys

from src.power import GoGriddyPriceChecker
from src.generics import PowerPriceChangedEvent
from src.events import Event, EventBus, EventBusMember
from src.services import ServiceProvider
from src.settings import Settings


class Test_GoGriddyInterface(unittest.TestCase):

    class DummyEventBusMember(EventBusMember):
        def __init__(self):
            self.lastPrice = None
            self.netUpdate = None

        def setServiceProvider(self, provider: ServiceProvider):
            super()._installEventHandler(
                PowerPriceChangedEvent, self._powerPriceChangedEvent)

        def _powerPriceChangedEvent(self, event: PowerPriceChangedEvent):
            self.lastPrice = event.price
            self.nextUpdate = event.nextUpdate

    def setup_method(self, method):
        self.serviceProvider = ServiceProvider()
        self.eventBus = EventBus()
        self.serviceProvider.installService(EventBus, self.eventBus)
        self.settings = Settings()
        self.settings.setServiceProvider(self.serviceProvider)
        self.serviceProvider.installService(Settings, self.settings)

        self.dummyEventBusMember = \
            Test_GoGriddyInterface.DummyEventBusMember()
        self.dummyEventBusMember.setServiceProvider(self.serviceProvider)
        self.priceChecker = GoGriddyPriceChecker()
        self.priceChecker.setServiceProvider(self.serviceProvider)

    # def test_data(self):
    #     self.eventBus.exec(2)

    #     self.assertIsNotNone(self.dummyEventBusMember.nextUpdate)
    #     self.assertIsNotNone(self.dummyEventBusMember.lastPrice)
