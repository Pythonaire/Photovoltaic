#!/usr/bin/env python3
"""App configuration."""
"""Set configuration vars from .env file."""
RFM69GardenURL = 'RFMGarden.local'
RFM69HouseURL = 'RFMHouse.local'
RFM69Garden_CONTROL = 'http://'+ RFM69GardenURL + ':8001/manageState'
RFM69Garden_CACHE = 'http://' + RFM69GardenURL + ':8001/cached'
RFM69Garden_SYNC = 'http://' + RFM69GardenURL + ':8001/sync'
RFM69House_CONTROL = 'http://'+ RFM69HouseURL + ':8001/manageState'
RFM69House_CACHE = 'http://' + RFM69HouseURL + ':8001/cached'
RFM69House_SYNC = 'http://' + RFM69HouseURL + ':8001/sync'
RADIO_URL = 'http://PiRadio.local:8001/postjson'
NODES = {"Pumpe": 11, "Weather": 12 , "RoomOne": 13, "RoomTwo": 14}
NODES_GARDEN = {"Pumpe": 11, "Weather": 12, "RoomTwo": 14 }
NODES_HOUSE = {"RoomOne": 13}
#conf for RTC Access
RTCDEVICE = '192.168.0.143'
RTC_DBNAME = '/home/pwiechmann/database/Photovoltaic.db'
