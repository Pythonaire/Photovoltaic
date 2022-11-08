#!/usr/bin/env python3
import logging
import select
import socket
import sqlite3 as sql
import sys
import time
from datetime import datetime
from sqlite3 import Error

from rctclient.frame import ReceiveFrame, make_frame
from rctclient.registry import REGISTRY as R
from rctclient.types import Command
from rctclient.utils import decode_value

import config

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

RTCDEVICE = config.Config.RTCDEVICE
RTC_DBNAME = config.Config.RTC_DBNAME

def connect(db):
    try:
        #conn = sql.connect(db, uri=True, detect_types=sql.PARSE_DECLTYPES | sql.PARSE_COLNAMES)
        conn = sql.connect(db, uri=True)
    except Error as e:
        logging.info('**** Failed to Connect to : {0} '.format(e))
    return conn

def write(cmd, value=None):
    with connect(RTC_DBNAME) as conn:
        cursor = conn.cursor()
        if value == None:
            cursor.execute(cmd)
        else:
            cursor.execute(cmd, value)
    conn.commit()
    cursor.close()

def fetchone(cmd, value=None):
    cmd = cmd
    with connect(RTC_DBNAME) as conn:
        cursor = conn.cursor()
        if value == None: 
            records = cursor.execute(cmd).fetchone()
        else:
            records = cursor.execute(cmd, value).fetchone()
    cursor.close()
    return records[0]

def get_rtc_values(rtc_value):
    try:
    # open the socket and connect to the remote device:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((RTCDEVICE, 8899))
        # query information about an object ID (here: battery.soc):
        #object_info = R.get_by_name('battery.soc')
        object_info = R.get_by_name(rtc_value)
        # construct a byte stream that will send a read command for the object ID we want, and send it
        send_frame = make_frame(command=Command.READ, id=object_info.object_id)
        sock.send(send_frame)
        # loop until we got the entire response frame
        frame = ReceiveFrame()
        while True:
            ready_read, _, _ = select.select([sock], [], [], 2.0)
            if sock in ready_read:
            # receive content of the input buffer
                buf = sock.recv(256)
                # if there is content, let the frame consume it
                if len(buf) > 0:
                    frame.consume(buf)
                    # if the frame is complete, we're done
                    if frame.complete():
                        value = decode_value(object_info.response_data_type, frame.data)
                        break
                else:
                 # the socket was closed by the device, exit
                    #sys.exit(1)
                    value=0
                    sys.exit(1)
            # decode the frames payload    
    except Exception as e:
        logging.info("*** error to read from RTC DEVICE *** {0}".format(e))
        value = 0
    return value 

def collect_data():
    record = {}
    now = datetime.now()
    unix_timestamp = int(time.mktime(now.timetuple()))
    PanelCurrent = get_rtc_values('dc_conv.dc_conv_struct[0].p_dc') + get_rtc_values('dc_conv.dc_conv_struct[1].p_dc')
    PanelTotal = get_rtc_values('energy.e_dc_total[0]') + get_rtc_values('energy.e_dc_total[1]')
    Grid = get_rtc_values('g_sync.p_ac_grid_sum_lp')
    if Grid > 0:
        FeedCurrent = 0
        GridCurrent = Grid
    else:
        FeedCurrent = Grid
        GridCurrent = 0
    FeedTotal = get_rtc_values('energy.e_grid_feed_total')
    GridTotal = get_rtc_values('energy.e_grid_load_total')
    HouseholdCurrent = get_rtc_values('g_sync.p_ac_load_sum_lp')
    HouseholdTotal = get_rtc_values('energy.e_load_total')
    BatteryPower = get_rtc_values('g_sync.p_acc_lp') # negative if the battery is charging
    if BatteryPower < 0:
        LoadState = 1
        BatteryCurrent = abs(BatteryPower)
    else:
        LoadState = 0
        BatteryCurrent = 0
    BatteryPercentage = get_rtc_values('battery.soc')*100
    BatteryTotal = get_rtc_values('battery.stored_energy')

    record = {'time':unix_timestamp,
    'PanelCurrentConsumption': round(PanelCurrent, 2),
    'PanelTotalConsumption': round(PanelTotal, 2),
    'FeedCurrentConsumption': abs(round(FeedCurrent,2)),
    'FeedTotalConsumption': abs(round(FeedTotal, 2)),
    'GridCurrentConsumption': abs(round(GridCurrent,2)),
    'GridTotalConsumption': round(GridTotal, 2),
    'HouseholdCurrentConsumption': round(HouseholdCurrent,2),
    'HouseholdTotalConsumption': round(HouseholdTotal, 2),
    'BatteryCurrentConsumption': round(BatteryCurrent, 2),
    'BatteryTotalConsumption': round(BatteryTotal, 2),
    'BatteryPercentage': int(round(BatteryPercentage, 2)),
    'BatteryState' : LoadState
        }
    logging.info('** writing RTC record to database - {0} **'.format(now.strftime("%d.%m.%Y %H:%M")))
    return record

def insert():
    dictRecord = collect_data()
    columns = list(dictRecord.keys())
    values = list(dictRecord.values())
    cmd = 'INSERT INTO RTC (' + (','.join('"' + str(v) + '"' for v in columns)) + ') VALUES(' + (','.join('?' for v in values)) + ');'
    try:
        write(cmd, values)
    except Exception as e:
        logging.info('sql error while writing: {0} \n'.format(e))


if __name__ == '__main__':
    insert()


