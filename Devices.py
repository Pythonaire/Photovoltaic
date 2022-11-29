#!/usr/bin/env python3
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_SPRINKLER, CATEGORY_OUTLET
import CacheData
import logging, time, threading
from history310 import FakeGatoHistory
import config
#import atexit
logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")
''' 
copy const.py to to /usr/local/lib/python3.x/dist-packages/pyhap to use newer CATEGORY and PERMISSIONS
'''

EPOCH_OFFSET = 978307200
RTCValues = CacheData.RTC_CACHE
RFM69Values = CacheData.RFM69_CACHE
RTCData= CacheData.RTCData()
cancel_future_calls =  CacheData.call_repeatedly(240,  RTCData.syncCache)

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
        self.HistoryPanel = FakeGatoHistory('energy', self)
        self.getValue()

    def getValue(self):
        self.Total = RTCValues['PanelTotalConsumption']
        self.CurrentConsumption.set_value(RTCValues['PanelCurrentConsumption'])
        self.TotalConsumption.set_value(RTCValues['PanelTotalConsumption'])
        self.HistoryPanel.addEntry({'time':int(time.time()),'power': RTCValues['PanelHistory']})
        
    @Accessory.run_at_interval(300)
    def run(self):
        self.getValue()

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
        self.HistoryGrid = FakeGatoHistory('energy', self)
        self.getValue()

    def getValue(self):
        self.CurrentConsumption.set_value( RTCValues['GridCurrentConsumption'])
        self.TotalConsumption.set_value(RTCValues['GridTotalConsumption'])
        self.HistoryGrid.addEntry({'time':int(time.time()),'power': RTCValues['GridHistory']})
    
    @Accessory.run_at_interval(300)
    def run(self):
        self.getValue()

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
        self.HistoryFeed = FakeGatoHistory('energy', self)
        self.getValue()

    def getValue(self):
        self.CurrentConsumption.set_value(RTCValues['FeedCurrentConsumption'])
        self.TotalConsumption.set_value(RTCValues['FeedTotalConsumption'])
        self.HistoryFeed.addEntry({'time':int(time.time()),'power': RTCValues['FeedHistory']})
        
    @Accessory.run_at_interval(300)
    def run(self):
        self.getValue()
    
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
        self.HistoryConsume = FakeGatoHistory('energy', self)
        self.getValue()

    def getValue(self):
        self.CurrentConsumption.set_value(RTCValues['HouseholdCurrentConsumption'])
        self.TotalConsumption.set_value(RTCValues['HouseholdTotalConsumption'])
        self.HistoryConsume.addEntry({'time':int(time.time()),'power': RTCValues['HouseholdHistory']})
        
    @Accessory.run_at_interval(300)
    def run(self):
        self.getValue()

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
        self.HistoryBattery = FakeGatoHistory('energy', self)
        self.getValue()


    def getValue(self):
        self.BatteryLevel.set_value(RTCValues['BatteryPercentage'])
        self.ChargingState.set_value(RTCValues['BatteryState'])
        self.CurrentConsumption.set_value(RTCValues['BatteryCurrentConsumption'])
        self.TotalConsumption.set_value(RTCValues['BatteryTotalConsumption'])
        self.HistoryBattery.addEntry({'time':int(time.time()),'power': RTCValues['BatteryHistory']})

    @Accessory.run_at_interval(300)
    def run(self):
        self.getValue()

    def stop(self):
        logging.info('Stopping accessory.')

