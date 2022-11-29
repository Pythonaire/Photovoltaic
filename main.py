#!/usr/bin/env python3
#import atexit
import logging
import os
import signal
import config
import Devices
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.loader import Loader as Loader

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

persist_file = 'devices.state'

"""
The bridge mixed up normal devices reached by Wifi, Devices connect through databases and RFM69 based devices connected through 433 MHz network.
RFM69 devices:
    Node numbers of RFM69 devices are stored in the config.py Class.
    example:
    NODES = {"Pumpe":11,"Weather":12}
The the dictionary key must refer to the device class, the value is the RFM69 node number to reach the 433MHz connected device.
While loading/importing Devices, classes and Nodes will be binded 
"""
loader = Loader(path_char='CharacteristicDefinition.json',path_service='ServiceDefinition.json')

#def exit_handler():
#    CallRTCDevice.set()
#    logging.info('****** terminate setInterval ********')


#atexit.register(exit_handler)

def get_bridge(driver):
    bridge = Bridge(driver, 'MacServer')
    # mixed Devices
    for item in config.NODES_GARDEN:
        DeviceClass = getattr(Devices,item)
        NodeNumber = config.NODES_GARDEN[item]
        bridge.add_accessory(DeviceClass(NodeNumber, driver, item))
        logging.info('****** add RFM69 Accessory: {0}, Number: {1} *****'.format(item, NodeNumber))
    for item in config.NODES_HOUSE:
        DeviceClass = getattr(Devices,item)
        NodeNumber = config.NODES_HOUSE[item]
        bridge.add_accessory(DeviceClass(NodeNumber, driver, item))
        logging.info('****** add RFM69 Accessory: {0}, Number: {1} *****'.format(item, NodeNumber))
    Soil = Devices.Moisture(12, driver, 'Soil Moisture') # needed to be separated because of new eve app
    bridge.add_accessory(Soil)
    # directly connected devices
    Panel = Devices.Panel(driver, 'RTC Panel')
    bridge.add_accessory(Panel)
    Feed = Devices.Feed(driver, 'RTC Feed')
    bridge.add_accessory(Feed)
    Grid = Devices.Grid(driver, 'RTC Grid')
    bridge.add_accessory(Grid)
    Consume = Devices.Consume(driver, 'RTC Consume')
    bridge.add_accessory(Consume)
    Battery = Devices.Battery(driver, 'RTC Battery')
    bridge.add_accessory(Battery)
    return bridge

try:
    driver = AccessoryDriver(port=51826, persist_file= persist_file, loader=loader)
    driver.add_accessory(accessory=get_bridge(driver))
    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
except Exception as e:
    logging.info('**** Could connect HAP Service: {0}'.format(e))
    os.kill(os.getpid(), signal.SIGKILL)