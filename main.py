#!/usr/bin/env python3
import logging
import os
import signal
import Devices
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.loader import Loader as Loader



logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

persist_file = 'devices.state'

loader = Loader(path_char='CharacteristicDefinition.json',path_service='ServiceDefinition.json')

def get_bridge(driver):
    bridge = Bridge(driver, 'MacServer')
    # mixed Devices
    Panel = Devices.Panel(driver, 'PVA Panel')
    Feed = Devices.Feed(driver, 'PVA Feed')
    Grid = Devices.Grid(driver, 'PVA Grid')
    Consume = Devices.Consume(driver, 'PVA Consume')
    Battery = Devices.Battery(driver, 'PVA Battery')
    bridge.add_accessory(Panel)
    bridge.add_accessory(Feed)
    bridge.add_accessory(Grid)
    bridge.add_accessory(Consume)
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

    
