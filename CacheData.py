#!/usr/bin/env python3
import logging
import sqlite3 as sql
import threading
from sqlite3 import Error
import requests, json
from requests.exceptions import ConnectTimeout
import config
RTC_DBNAME = config.RTC_DBNAME
logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

RFM69_CACHE = {}

RTC_CACHE = {
    'PanelCurrentConsumption': 0,
    'PanelHistory':0,
    'PanelTotalConsumption': 0,
    'FeedCurrentConsumption': 0,
    'FeedHistory': 0,
    'FeedTotalConsumption': 0,
    'GridCurrentConsumption': 0,
    'GridHistory': 0,
    'GridTotalConsumption': 0,
    'HouseholdCurrentConsumption': 0,
    'HouseholdHistory': 0,
    'HouseholdTotalConsumption': 0,
    'BatteryCurrentConsumption': 0,
    'BatteryHistory': 0,
    'BatteryTotalConsumption': 0,
    'BatteryPercentage': 0,
    'BatteryState': 0 
}

def call_repeatedly(interval, func):
        stopped = threading.Event()
        def loop():
            while not stopped.wait(stopped.wait(interval)): # the first call is in `interval` secs
                #func(*args)
                func()
        threading.Thread(target=loop, daemon=True).start()    
        return stopped.set

class RTCData():
    def __init__(self):
        self.dbName = RTC_DBNAME
        self.syncCache() # initial

    def connect(self, db):
        try:
            #conn = sql.connect(db, uri=True, detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
            conn = sql.connect(db, uri=True)
        except Error as e:
            logging.info('**** Failed to Connect to : {0} '.format(e))
        return conn

    def fetchone(self, cmd, value=None):
        self.cmd = cmd
        with self.connect(self.dbName) as conn:
            cursor = conn.cursor()
            if value == None: 
                records = cursor.execute(self.cmd).fetchone()
            else:
                records = cursor.execute(self.cmd, value).fetchone()
        cursor.close()
        return records[0]


    def TotalWh(self, column):
        cmd = "SELECT MAX({0}) FROM RTC WHERE date(time,'unixepoch') > date('now', 'start of year');".format(column)
        actualyear =round(self.fetchone(cmd) / 1000, 2)
        cmd = "SELECT IFNULL(MAX({0}),0) FROM RTC WHERE date(time,'unixepoch') < date('now', 'start of year');".format(column)
        if self.fetchone(cmd) == None:
            lastyear = 0
        else:
            lastyear =round(self.fetchone(cmd) / 1000, 2)
        return round(actualyear - lastyear, 2)  # type: ignore

    def ActualValue(self, column):
        cmd = "SELECT {0} FROM RTC WHERE id = (SELECT MAX(id) FROM RTC);".format(column)
        return int(self.fetchone(cmd))  # type: ignore

    def AverageWh(self, column):
        cmd = "SELECT ROUND(AVG({0}),2) FROM (SELECT {1} FROM RTC ORDER BY id DESC LIMIT 12);".format(column, column)
        '''
        The Eve App multiply the Power by 10. Eve.app will assume that the same power is drawn for all the sampling time (10 minutes), 
        so it will show a point with an energy consumption equal to this value divided by 60. Example. 
        Your appliance is consuming 1000W, which means a total energy of 1kWh if run for 1 hour. 
        The value reported is 1000 x 10. The value shown is 1000 x 10 / 60 = 166Wh, which is correct because this sample covers 10min, 
        i.e. 1/6 of an hour. At the end of the hour, Eve.app will show 6 samples at 166Wh, totalizing 1kWh.'''
        return int(self.fetchone(cmd))


    def syncCache(self):
        cmd = 'SELECT MAX(id) FROM RTC;'
        try:
            maxId = self.fetchone(cmd)
        except Exception as e:
            logging.info('sql error while writing: {0} \n'.format(e))
            maxId = 0
        if maxId > 11: # we want the last hour, the script runs every 5 minutes -> we need 12 values
            RTC_CACHE['PanelCurrentConsumption'] = self.ActualValue('PanelCurrentConsumption')
            RTC_CACHE['PanelHistory'] = self.AverageWh('PanelCurrentConsumption')
            RTC_CACHE['PanelTotalConsumption'] = self.TotalWh('PanelTotalConsumption')
            RTC_CACHE['FeedCurrentConsumption'] = self.ActualValue('FeedCurrentConsumption')
            RTC_CACHE['FeedHistory'] = self.AverageWh('FeedCurrentConsumption')
            RTC_CACHE['FeedTotalConsumption'] =  self.TotalWh('FeedTotalConsumption')
            RTC_CACHE['GridCurrentConsumption'] = self.ActualValue('GridCurrentConsumption')
            RTC_CACHE['GridHistory'] = self.AverageWh('GridCurrentConsumption')
            RTC_CACHE['GridTotalConsumption'] = self.TotalWh('GridTotalConsumption')
            RTC_CACHE['HouseholdCurrentConsumption'] = self.ActualValue('HouseholdCurrentConsumption')
            RTC_CACHE['HouseholdHistory'] = self.AverageWh('HouseholdCurrentConsumption')
            RTC_CACHE['HouseholdTotalConsumption'] = self.TotalWh('HouseholdTotalConsumption')
            RTC_CACHE['BatteryCurrentConsumption'] = self.ActualValue('BatteryCurrentConsumption')
            RTC_CACHE['BatteryHistory'] = self.AverageWh('BatteryCurrentConsumption')
            RTC_CACHE['BatteryTotalConsumption'] = self.TotalWh('BatteryTotalConsumption')
            RTC_CACHE['BatteryPercentage'] = self.ActualValue('BatteryPercentage')
            RTC_CACHE['BatteryState'] = self.ActualValue('BatteryState')
        else:
            RTC_CACHE['PanelCurrentConsumption'] = self.ActualValue('PanelCurrentConsumption')
            RTC_CACHE['PanelHistory'] = 0
            RTC_CACHE['PanelTotalConsumption'] = self.TotalWh('PanelTotalConsumption')
            RTC_CACHE['FeedCurrentConsumption'] = self.AverageWh('FeedCurrentConsumption')
            RTC_CACHE['FeedHistory'] = 0
            RTC_CACHE['FeedTotalConsumption'] =  self.TotalWh('FeedTotalConsumption')
            RTC_CACHE['GridCurrentConsumption'] = self.ActualValue('GridCurrentConsumption')
            RTC_CACHE['GridHistory'] = 0
            RTC_CACHE['GridTotalConsumption'] = self.TotalWh('GridTotalConsumption')
            RTC_CACHE['HouseholdCurrentConsumption'] = self.ActualValue('HouseholdCurrentConsumption')
            RTC_CACHE['HouseholdHistory'] = 0
            RTC_CACHE['HouseholdTotalConsumption'] = self.TotalWh('HouseholdTotalConsumption')
            RTC_CACHE['BatteryCurrentConsumption'] = self.ActualValue('BatteryCurrentConsumption')
            RTC_CACHE['BatteryHistory'] = 0
            RTC_CACHE['BatteryTotalConsumption'] = self.TotalWh('BatteryTotalConsumption')
            RTC_CACHE['BatteryPercentage'] = self.ActualValue('BatteryPercentage')
            RTC_CACHE['BatteryState'] = self.ActualValue('BatteryState')
    

class RFM69Data():
    def __init__(self):
        self.GardenNodes = {k :str(v) for k, v in config.NODES_GARDEN.items()} # switch node number to string, because of easier json handling
        self.HouseNodes = {k :str(v) for k, v in config.NODES_HOUSE.items()} # switch node number to string, because of easier json handling
        self.GardenUrl = config.RFM69Garden_SYNC
        self.HouseUrl = config.RFM69House_SYNC
        self.GardenControlUrl = config.RFM69Garden_CONTROL
        self.RadioUrl = config.RADIO_URL
        self.syncCache() # inital

    def syncCache(self):
        global RFM69_CACHE
        #my_dictionary = {k :str(v) for k, v in self.HouseNodes.items()}
        #logging.info("dict: {0}".format(my_dictionary))
        try:

            dict = requests.get(self.HouseUrl, timeout=2).json()
            for node in self.HouseNodes.values():
                if node in dict:
                    RFM69_CACHE[node] = dict[node]
                else:
                    RFM69_CACHE[node] = None
        except ConnectTimeout as e:
            logging.info('**** request to {0} timed out: {1}'.format(self.HouseUrl, e)) 
            for node in self.HouseNodes.values():
                RFM69_CACHE[node] = None   
        try:
            dict = requests.get(self.GardenUrl, timeout = 2).json()
            for node in self.GardenNodes.values():
                if node in dict:
                    RFM69_CACHE[node] = dict[node]
                else:
                    RFM69_CACHE[node] = None
        except ConnectTimeout as e:
            logging.info('**** request to {0} timed out: {1}'.format(self.GardenUrl, e))
            for node in self.GardenNodes.values():
                RFM69_CACHE[node] = None
        logging.info('**** Cache refreshed with data from Nodes {0} ****'.format(list(RFM69_CACHE.keys())))

    def controlrfm(self, bridge, node, cmd):
        global RFM69_CACHE
        httpsend = {node: cmd}
        try:
            RFM69_CACHE[node] = requests.get(bridge, json=json.dumps(httpsend), timeout= 2).json()[node]
            #rfm return with json {'node':None} if request failed
            #NODE_CACHE[node] = answer[node]
        except ConnectTimeout as e:
            logging.info('**** request to {0} timed out: {1}'.format(bridge, e)) 
            RFM69_CACHE[node] = None
    
    def forwarder(self, data):
        try:
            requests.post(self.RadioUrl, json=json.dumps(data))
            logging.info('**** post Temp to Radio {0}'.format(data))
        except requests.exceptions.ConnectionError as e:
            logging.info('**** request.post to {0} got exception {1}'.format(self.RadioUrl,e))

