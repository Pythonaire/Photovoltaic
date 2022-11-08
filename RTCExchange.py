#!/usr/bin/env python3
import logging
import sqlite3 as sql
import threading
from sqlite3 import Error


import config
RTC_DBNAME = config.Config.RTC_DBNAME
logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

RTCDict = {
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

def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()
            def loop(): # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)
            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator

class SQL():
    def __init__(self):
        self.dbName = RTC_DBNAME

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
        cmd = "SELECT MAX({0}) FROM RTC WHERE date(time,'unixepoch') < date('now', 'start of year');".format(column)
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


    @setInterval(600)
    def Exchange(self):
        cmd = 'SELECT MAX(id) FROM RTC;'
        try:
            maxId = self.fetchone(cmd)
        except Exception as e:
            logging.info('sql error while writing: {0} \n'.format(e))
            maxId = 0
        if maxId > 11: # we want the last hour, the script runs every 10 minutes -> we need 12 values
            RTCDict['PanelCurrentConsumption'] = self.AverageWh('PanelCurrentConsumption')
            RTCDict['PanelHistory'] = self.ActualValue('PanelCurrentConsumption')
            RTCDict['PanelTotalConsumption'] = self.TotalWh('PanelTotalConsumption')
            RTCDict['FeedCurrentConsumption'] = self.AverageWh('FeedCurrentConsumption')
            RTCDict['FeedHistory'] = self.ActualValue('FeedCurrentConsumption')
            RTCDict['FeedTotalConsumption'] =  self.TotalWh('FeedTotalConsumption')
            RTCDict['GridCurrentConsumption'] = self.AverageWh('GridCurrentConsumption')
            RTCDict['GridHistory'] = self.ActualValue('GridCurrentConsumption')
            RTCDict['GridTotalConsumption'] = self.TotalWh('GridTotalConsumption')
            RTCDict['HouseholdCurrentConsumption'] = self.AverageWh('HouseholdCurrentConsumption')
            RTCDict['HouseholdHistory'] = self.ActualValue('HouseholdCurrentConsumption')
            RTCDict['HouseholdTotalConsumption'] = self.TotalWh('HouseholdTotalConsumption')
            RTCDict['BatteryCurrentConsumption'] = self.AverageWh('BatteryCurrentConsumption')
            RTCDict['BatteryHistory'] = self.ActualValue('BatteryCurrentConsumption')
            RTCDict['BatteryTotalConsumption'] = self.TotalWh('BatteryTotalConsumption')
            RTCDict['BatteryPercentage'] = self.ActualValue('BatteryPercentage')
            RTCDict['BatteryState'] = self.ActualValue('BatteryState')
            