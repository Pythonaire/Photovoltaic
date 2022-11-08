#!/usr/bin/env python3
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_SPRINKLER, CATEGORY_OUTLET
import RTCExchange
import logging, requests, asyncio, json, time
from history import FakeGatoHistory
import config
#import atexit
logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")


NODES = config.Config.NODES
NODE_CACHE = config.Config.NODE_CACHE
EPOCH_OFFSET = 978307200

RTCSQL = RTCExchange.SQL()
DictSync = RTCSQL.Exchange()
RTCDict = RTCExchange.RTCDict


#def exit_handler():
#    DictSync.set()
#    logging.info('****** terminate setInterval ********')

#atexit.register(exit_handler)

class Panel(Accessory):
    category = CATEGORY_OUTLET
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.set_info_service(firmware_revision='0.0.1', manufacturer= 'Pythonaire', model='MacServerRTCPanel', serial_number="27102022_005")
        Panel = self.add_preload_service('PowerMeterPanel', chars = ["CurrentConsumption", "TotalConsumption", "Name", "ResetTotal"])
        Panel.configure_char('Name', value = 'Panel')
        Panel.configure_char("ResetTotal", value = time.time() - EPOCH_OFFSET)
        self.CurrentConsumption = Panel.configure_char('CurrentConsumption')
        self.TotalConsumption = Panel.configure_char('TotalConsumption')
        self.CurrentConsumption.set_value(RTCDict['PanelCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['PanelTotalConsumption'])
        self.HistoryPanel = FakeGatoHistory('energy', self)

    @Accessory.run_at_interval(600)
    def run(self):
        logging.info('Panel Current: {0}, Total: {1}, History {2}  '. format(RTCDict['PanelCurrentConsumption'], RTCDict['PanelTotalConsumption'], RTCDict['PanelHistory']))
        self.CurrentConsumption.set_value(RTCDict['PanelCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['PanelTotalConsumption'])
        self.HistoryPanel.addEntry({'time':int(time.time()),'power': RTCDict['PanelHistory']})

    def stop(self):
        logging.info('Stopping accessory.')


class Grid(Accessory):
    category = CATEGORY_OUTLET
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.set_info_service(firmware_revision='0.0.1', manufacturer= 'Pythonaire', model='MacServerRTCGrid', serial_number="27102022_004")
        Grid = self.add_preload_service('PowerMeterGrid', chars = ["CurrentConsumption", "TotalConsumption", "Name", "ResetTotal"])
        Grid.configure_char('Name', value = 'Grid')
        Grid.configure_char("ResetTotal", value = time.time() - EPOCH_OFFSET)
        self.CurrentConsumption = Grid.configure_char('CurrentConsumption')
        self.TotalConsumption = Grid.configure_char('TotalConsumption')
        self.CurrentConsumption.set_value(RTCDict['GridCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['GridTotalConsumption'])
        self.HistoryGrid = FakeGatoHistory('energy', self)
    
    @Accessory.run_at_interval(600)
    def run(self):
        self.CurrentConsumption.set_value(RTCDict['GridCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['GridTotalConsumption'])
        self.HistoryGrid.addEntry({'time':int(time.time()),'power': RTCDict['GridHistory']})

    def stop(self):
        logging.info('Stopping accessory.')


class Feed(Accessory):
    category = CATEGORY_OUTLET
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        # Feed negative values
        self.set_info_service(firmware_revision='0.0.1', manufacturer= 'Pythonaire', model='MacServerRTCFeed', serial_number="27102022_003")
        Feed = self.add_preload_service('PowerMeterFeed', chars = ["CurrentConsumption", "TotalConsumption", "Name", "ResetTotal"])
        Feed.configure_char('Name', value = 'Feed')
        Feed.configure_char("ResetTotal", value = time.time() - EPOCH_OFFSET)
        self.CurrentConsumption = Feed.configure_char('CurrentConsumption')
        self.TotalConsumption = Feed.configure_char('TotalConsumption')
        self.CurrentConsumption.set_value(RTCDict['FeedCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['FeedTotalConsumption'])
        self.HistoryFeed = FakeGatoHistory('energy', self)

    @Accessory.run_at_interval(600)
    def run(self):
        self.CurrentConsumption.set_value(RTCDict['FeedCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['FeedTotalConsumption'])
        self.HistoryFeed.addEntry({'time':int(time.time()),'power': RTCDict['FeedHistory']})
    
    def stop(self):
        logging.info('Stopping accessory.')

class Consume(Accessory):
    category = CATEGORY_OUTLET
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.set_info_service(firmware_revision='0.0.1', manufacturer= 'Pythonaire', model='MacServerRTCConsume', serial_number="27102022_002")
        Consume = self.add_preload_service('PowerMeterConsume', chars = ["CurrentConsumption", "TotalConsumption", "Name","ResetTotal"])
        Consume.configure_char('Name', value = 'Consume')
        Consume.configure_char("ResetTotal", value = time.time() - EPOCH_OFFSET)
        self.CurrentConsumption = Consume.configure_char('CurrentConsumption')
        self.TotalConsumption = Consume.configure_char('TotalConsumption')
        self.CurrentConsumption.set_value(RTCDict['HouseholdCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['HouseholdTotalConsumption'])
        self.HistoryConsume = FakeGatoHistory('energy', self)

    @Accessory.run_at_interval(600)
    def run(self):
        self.CurrentConsumption.set_value(RTCDict['HouseholdCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['HouseholdTotalConsumption'])
        self.HistoryConsume.addEntry({'time':int(time.time()),'power': RTCDict['HouseholdHistory']})

    def stop(self):
        logging.info('Stopping accessory.')
        

class Battery(Accessory):
    category = CATEGORY_OUTLET
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.set_info_service(firmware_revision='0.0.1', manufacturer= 'Pythonaire', model='MacServerRTCBattery', serial_number="27102022_001")
        Battery = self.add_preload_service('PowerMeterBattery', chars = ["CurrentConsumption", "TotalConsumption", "Name", "BatteryLevel", "ChargingState", "ResetTotal"])
        Battery.configure_char('Name', value = "Battery")
        self.BatteryLevel = Battery.configure_char('BatteryLevel')
        self.ChargingState = Battery.configure_char('ChargingState')
        self.ResetTotal = Battery.configure_char("ResetTotal", value = time.time() - EPOCH_OFFSET)
        self.CurrentConsumption = Battery.configure_char('CurrentConsumption')
        self.TotalConsumption = Battery.configure_char('TotalConsumption')
        self.BatteryLevel.set_value(RTCDict['BatteryPercentage'])
        self.ChargingState.set_value(RTCDict['BatteryState'])
        self.CurrentConsumption.set_value(RTCDict['BatteryCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['BatteryTotalConsumption'])
        self.HistoryBattery = FakeGatoHistory('energy', self)

    def CurrentW(self):
        batteryCurrentConsumption = RTCDict['BatteryCurrentConsumption']
        if batteryCurrentConsumption > 0: # battery in unload state
            batteryCurrentConsumption  = 0
        else:
            batteryCurrentConsumption  = abs(batteryCurrentConsumption)
        return batteryCurrentConsumption

    @Accessory.run_at_interval(600)
    def run(self):
        self.BatteryLevel.set_value(RTCDict['BatteryPercentage'])
        self.ChargingState.set_value(RTCDict['BatteryState'])
        self.CurrentConsumption.set_value(RTCDict['BatteryCurrentConsumption'])
        self.TotalConsumption.set_value(RTCDict['BatteryTotalConsumption'])
        self.HistoryBattery.addEntry({'time':int(time.time()),'power': RTCDict['BatteryHistory']})

    def stop(self):
        logging.info('Stopping accessory.')
