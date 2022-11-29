#!/usr/bin/env python3
import logging, time, math, re, base64, uuid
from timer import FakeGatoTimer
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

EPOCH_OFFSET = 978307200

def precisionRound(num, prec):
    factor = math.pow(10, prec)
    return round(num * factor) / factor

def hexToBase64(x):
    string = re.sub(r"[^0-9A-F]", '', ('' + x), flags = re.I)
    b = bytearray.fromhex(string)
    return base64.b64encode(b).decode('utf-8')
    
def base64ToHex(x):
    if len(x) == 0:
        return x
    else:
        return base64.b64decode(x).hex()

def swap16(i):
	return ((i & 0xFF) << 8) | ((i >> 8) & 0xFF)

def swap32(i):
    return ((i & 0xFF) << 24) | ((i & 0xFF00) << 8) | ((i >> 8) & 0xFF00) | ((i >> 24) & 0xFF)

def isValid(value):
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def toLongFormUUID(uuid, base = '-0000-1000-8000-0026BB765291'):
    if isValid(uuid) == True:
        return uuid.upper()
    elif isValid(uuid+base) == False:
        logging.info("uuid was not a valid UUID or short form UUID: {0}:".format(uuid))
    elif isValid('00000000' + base) == False:
        logging.info("base was not a valid base UUID: {0}:".format(base))
    return (('00000000' + uuid)[:-8] + base).upper()

def toShortFormUUID(uuid, base = '-0000-1000-8000-0026BB765291'):
    uuid = toLongFormUUID(uuid, base)
    return uuid[0, 8]

class FakeGatoHistory():
    def __init__(self, accessoryType, accessory, *args, **kwargs):
        super().__init__(*args, **kwargs) 
        self.signatures = []
        self.accessory = accessory
        self.accessoryName = self.accessory.display_name
        self.accessoryType = accessoryType
        self.memorySize = 4032
        self.entry2address = lambda e: e % self.memorySize
        self.minutes = 10
        self.firstEntry = 0
        self.lastEntry = 0
        self.history = [self.accessoryName]
        self.usedMemory = 0
        self.currentEntry = 1
        self.transfer = False
        self.setTime = True
        self.restarted = True
        self.refTime = 0
        self.memoryAddress = 0 
        self.dataStream = ''

        logging.info('Registring Events {0}'.format(self.accessoryName))
        self.service = self.accessory.add_preload_service('History', chars =['HistoryStatus','HistoryEntries','HistoryRequest','SetTime'])
        self.HistoryEntries = self.service.configure_char("HistoryEntries")
        self.HistoryRequest = self.service.configure_char('HistoryRequest')
        self.HistoryStatus = self.service.configure_char("HistoryStatus")
        self.CurrentTime = self.service.configure_char('SetTime')
        self.HistoryEntries.getter_callback = self.getCurrentHistoryEntries
        self.HistoryRequest.setter_callback = self.setCurrentHistoryRequest
        self.CurrentTime.setter_callback = self.setCurrentSetTime

        self.globalFakeGatoTimer = FakeGatoTimer(self.minutes,  self.accessoryName)
    
        match self.accessoryType:
            case 'weather':
                self.accessoryType116 = "03 0102 0202 0302"
                self.accessoryType117 = "07"
                self.globalFakeGatoTimer.subscribe(self, self.calculateAverage)
            case 'energy':
                self.accessoryType116 = "04 0102 0202 0702 0f03"
                self.accessoryType117 = "1f"
                self.globalFakeGatoTimer.subscribe(self, self.calculateAverage)
            case 'room':
                self.accessoryType116 = "04 0102 0202 0402 0f03"
                self.accessoryType117 = "0f"
                self.globalFakeGatoTimer.subscribe(self, self.calculateAverage)
            case 'room2':
                self.accessoryType116 = "07 0102 0202 2202 2901 2501 2302 2801"
                self.accessoryType117 = "7f"
                self.globalFakeGatoTimer.subscribe(self, self.calculateAverage)
            case 'door':
                self.accessoryType116 = "01 0601"
                self.accessoryType117 = "01"
                self.globalFakeGatoTimer.subscribe(self, self.select_types)
            case 'motion':
                self.accessoryType116 = "02 1301 1c01"
                self.accessoryType117 = "02"
                self.globalFakeGatoTimer.subscribe(self, self.select_types)
            case 'switch':
                self.accessoryType116 = "01 0e01"
                self.accessoryType117 = "01"
                self.globalFakeGatoTimer.subscribe(self, self.select_types)
            case 'aqua':
                self.accessoryType116 = "03 1f01 2a08 2302"
                self.accessoryType117 = "05"
                self.accessoryType117bis = "07"
            case 'thermo':
                self.accessoryType116 = "05 0102 1102 1001 1201 1d01"
                self.accessoryType117 = "1f"
            case 'custom':
                self.signatures = []
                sorted_signature = []
                for x in self.service:
                    for y in x.get_characteristic(x):
                        self.uuid = isValid(y['UUID'])
                        if self.uuid== '00000011-0000-1000-8000-0026BB765291': # CurrentTemperature
                            self.signatures.append({'signature': '0102', 'length': 4, 'uuid': toLongFormUUID(self.uuid), 'factor': 100, 'entry': 'temp'})
                            sorted_signature.append('0102')
                        elif self.uuid == '000000C8-0000-1000-8000-0026BB765291': # VOCDensity
                            self.signatures.append({'signature': '2202', 'length': 4, 'uuid': toLongFormUUID(self.uuid), 'factor': 1, 'entry': 'voc'})
                            sorted_signature.append('2202')
                        elif self.uuid == '00000010-0000-1000-8000-0026BB765291': #CurrentRelativeHumidity
                            self.signatures.append({'signature': '0202', 'length': 4, 'uuid': toLongFormUUID(self.uuid), 'factor': 100, 'entry': 'humidity'})
                            sorted_signature.append('0202')
                        elif self.uuid == 'E863F10F-079E-48FF-8F27-9C2605A29F52': #AtmosphericPressure
                            self.signatures.append({'signature': '0302', 'length': 4, 'uuid': toLongFormUUID(self.uuid),'factor': 10, 'entry': 'pressure'})
                            sorted_signature.append('0302')
                        elif self.uuid == 'E863F10B-079E-48FF-8F27-9C2605A29F52': #EveAirQuality
                            self.signatures.append({'signature': '0702', 'length': 4, 'uuid': toLongFormUUID(self.uuid),'factor': 10, 'entry': 'ppm'})
                            sorted_signature.append('0702')
                        elif self.uuid == '0000006A-0000-1000-8000-0026BB765291': #ContactSensorState
                            self.signatures.append({'signature': '0601', 'length': 2, 'uuid': toLongFormUUID(self.uuid), 'factor': 1, 'entry': 'contact'})
                            sorted_signature.append('0601')
                        elif self.uuid == 'E863F10D-079E-48FF-8F27-9C2605A29F52': #CurrentConsumption
                            self.signatures.append({'signature': '0702', 'length': 4, 'uuid': toLongFormUUID(self.uuid), 'factor': 10, 'entry': 'power'})
                            sorted_signature.append('0702')
                        elif self.uuid == '00000025-0000-1000-8000-0026BB765291': #Switch On
                            self.signatures.append({'signature': '0e01', 'length': 2, 'uuid': toLongFormUUID(self.uuid), 'factor': 1, 'entry': 'status'})
                            sorted_signature.append('0e01')
                        elif self.uuid == '00000022-0000-1000-8000-0026BB765291': #MotionDetected
                            self.signatures.append({'signature': '0c01', 'length': 2, 'uuid': toLongFormUUID(self.uuid), 'factor': 1, 'entry': 'motion'})
                            sorted_signature.append('0c01')

                    # here we need just the sorted 'signature' and count, self.signature will needed by getCurrentHistoryEntries
                sorted_signature.sort()
                sorted_string = (i + ' ' for i in sorted_signature)
                self.accessoryType116 =' 0' + str(len(sorted_signature)) + ' ' + sorted_string  # type: ignore
                logging.info("Services: {0}:".format(self.accessoryType116))
                self.globalFakeGatoTimer.subscribe(self, self.calculateAverage)
    

    def calculateAverage(self, params): # callback
        backLog = params['backLog'] if 'backLog' in params else []
        previousAvrg = params['previousAvrg'] if 'previousAvrg' in params else {}
        timer = params['timer']
        calc = {
		    	'sum': {},
			    'num': {},
			    'avrg': {}
		        }
        for dict in backLog: #list
            for key, val in dict.items(): #dict
                if key != 'time':
                    if not key in calc['sum']:
                        calc['sum'][key] = 0
                    if not key in calc['num']:
                        calc['num'][key] = 0
                    calc['sum'][key] += val
                    calc['num'][key] += 1
                    calc['avrg'][key] = precisionRound(calc['sum'][key] / calc['num'][key], 2)
                    if key == 'voc':
                        calc['avrg'][key] = int(calc['avrg'][key])

        calc['avrg']['time'] = int(round(time.time()))
        for key, val in previousAvrg.items():
            if key != 'time':
                if len(backLog) == 0 or (key not in calc['avrg']):
                    calc['avrg'][key] = previousAvrg[key]
        if len(calc['avrg']) > 1:
            self._addEntry(calc['avrg'])
            timer.emptyData(self)
        return calc['avrg']

    def select_types(self, params): # callback
        backLog = params['backLog'] if 'backLog' in params else []
        immediate = params['immediate']
        actualEntry = {}
        if len(backLog) != 0:
            if immediate == None:
                actualEntry['time'] = int(round(time.time()))
                actualEntry['status'] = backLog[0]['status']
            else:
                actualEntry['time'] = backLog[0]['time']
                actualEntry['status'] = backLog[0]['status']
            self._addEntry(actualEntry)

    def sendHistory(self, address):
        if address != 0:
            self.currentEntry = address
        else:
            self.currentEntry = 1 
        self.transfer = True

    def addEntry(self, entry):
        self.entry = entry
        match self.accessoryType:
            case 'door' | 'motion' | 'switch':
                self.globalFakeGatoTimer.addData({ 'entry': self.entry, 'service': self, 'immediateCallback': True})
            case 'aqua':
                self._addEntry({ 'time': self.entry['time'], 'status': self.entry['status'], 'waterAmount': self.entry['waterAmount'] , 'immediateCallback': True})
            case 'weather':
                self.globalFakeGatoTimer.addData({ 'entry': self.entry, 'service': self})
            case 'room':
                self.globalFakeGatoTimer.addData({ 'entry': self.entry, 'service': self})
            case 'room2':
                self.globalFakeGatoTimer.addData({ 'entry': self.entry, 'service': self})
            case 'energy':
                self.globalFakeGatoTimer.addData({ 'entry': self.entry, 'service': self})
            case 'custom':
                if 'power' in entry or 'temp' in entry:
                    self.globalFakeGatoTimer.addData({ 'entry': self.entry, 'service': self })
                else:
                    self._addEntry(self.entry)
            case _:
                self._addEntry(self.entry)

    def _addEntry(self, entry):
        if self.usedMemory < self.memorySize:
            self.usedMemory += 1
            self.firstEntry = 0
            self.lastEntry = self.usedMemory
            self.history.append(self.lastEntry)
        else:
            self.firstEntry += 1
            self.lastEntry = self.firstEntry + self.usedMemory
            self.history.append(self.lastEntry)
            if self.restarted == True:
                self.history[self.entry2address(self.lastEntry)] = {'time': entry['time'],'setRefTime': 1}
                self.firstEntry += 1
                self.lastEntry = self.firstEntry + self.usedMemory
                self.restarted = False
        if self.refTime == 0:
            self.refTime = entry['time'] - EPOCH_OFFSET
            self.history[self.lastEntry] = {'time': entry['time'],'setRefTime': 1}
            self.lastEntry += 1
            self.usedMemory += 1
            self.history.append(self.lastEntry)
        self.history[self.entry2address(self.lastEntry)] = entry
        if self.usedMemory < self.memorySize:
            val = ('{0}00000000{1}{2}{3}{4}{5}000000000101'.format(
            format(swap32(int(entry['time'] - self.refTime - EPOCH_OFFSET)),'08X'),
            format(swap32(int(self.refTime)),'08X'),
            self.accessoryType116,
            format(swap16(int(self.usedMemory + 1)),'04X'),
            format(swap16(int(self.memorySize)),'04X'),
            format(swap32(int(self.firstEntry)),'08X')
            ))
        else:
            val = ('{0}00000000{1}{2}{3}{4}{5}000000000101'.format(
            format(swap32(int(entry['time'] - self.refTime - EPOCH_OFFSET)),'08X'),
            format(swap32(int(self.refTime)),'08X'),
            self.accessoryType116,
            format(swap16(int(self.usedMemory)),'04X'),
            format(swap16(int(self.memorySize)),'04X'),
            format(swap32(int(self.firstEntry+1)),'08X')
            ))   
        
        self.HistoryStatus.set_value(hexToBase64(val))
        #self.service.configure_char("HistoryStatus", value = hexToBase64(val))
        #logging.info("First entry {0}: {1}".format(self.accessoryName, self.firstEntry))
        #logging.info("Last entry {0}: {1}".format(self.accessoryName, self.lastEntry))
        #logging.info("Used memory {0}: {1}".format(self.accessoryName, self.usedMemory))
        #logging.info("116 {0}: {1}".format(self.accessoryName, val)
        


    def getCurrentHistoryEntries(self):
        if (self.currentEntry <= self.lastEntry) and (self.transfer == True):
            self.memoryAddress = self.entry2address(self.currentEntry)
            for x in self.history:
            #for x in range(10):
                if self.history[self.memoryAddress].get('setRefTime') == 1 or self.setTime == True or self.currentEntry == self.firstEntry +1:
                    self.dataStream  += (",15{0} 0100 0000 81{1}0000 0000 00 0000".format(
                        format(int(swap32(self.currentEntry)), '08X'), 
                        format(int(swap32(self.refTime)), '08X'))
                    )
                    self.setTime = False
                else:
                    logging.info("{0} Entry: {1}, Address: {2}".format(self.accessoryName, self.currentEntry, self.memoryAddress))
                    match self.accessoryType:
                        case 'weather':
                            self.dataStream += (",10 {0}{1}-{2}:{3} {4} {5}".format(format(swap32(int(self.currentEntry)), '08X'),
                            format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08X'),
                            self.accessoryType117,
                            format(swap16(int(self.history[self.memoryAddress].get('temp') * 100)), '04X'),
			                format(swap16(int(self.history[self.memoryAddress].get('humidity') * 100)), '04X'),
			                format(swap16(int(self.history[self.memoryAddress].get('pressure') * 10)), '04X'))
                            )
                        case 'energy':
                            self.dataStream += (",14 {0}{1}-{2}:0000 0000 {3} 0000 0000".format(
                            format(swap32(int(self.currentEntry)), '08X'),
                            format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08X'),
			                self.accessoryType117,
			                format(swap16(int(self.history[self.memoryAddress].get('power') * 10)), '04X'))
                            )
                        case 'room':
                            self.dataStream += (",13 {0}{1}{2}{3}{4}{5}0000 00".format(format(swap32(int(self.currentEntry)), '08X'),
                            format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08x'),
			                self.accessoryType117,
			                format(swap16(int(self.history[self.memoryAddress].get('temp') * 100)), '04X'),
			                format(swap16(int(self.history[self.memoryAddress].get('humidity') * 100)), '04X'),
			                format(swap16(int(self.history[self.memoryAddress].get('ppm'))), '04X'))
                            )
                        case 'room2':
                            self.dataStream += (",15 {0}{1}{2}{3}{4}{5}0054 a80f01".format(format(swap32(int(self.currentEntry)), '08X'),
                            format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08x'),
                            self.accessoryType117,
                            format(swap16(int(self.history[self.memoryAddress].get('temp') * 100)), '04X'),
                            format(swap16(int(self.history[self.memoryAddress].get('humidity') * 100)), '04X'),
                            format(swap16(int(self.history[self.memoryAddress].get('voc'))), '04X'))
                            )
                        case 'door' | 'motion' | 'switch':
                            self.dataStream += (",0b {0}{1}{2}{3}".format(format(swap32(int(self.currentEntry)), '08X'),
                            format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08X'),
			                self.accessoryType117,
			                format(self.history[self.memoryAddress].get('status'), '02X'))
                            )
                        case 'aqua':
                            if self.history[self.memoryAddress].get('status') == True:
                                self.dataStream += (",0d {0}{1}{2}{3} 300c".format(format(swap32(int(self.currentEntry)), '08X'),
                                format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08X'),
			                    self.accessoryType117,
			                    format(self.history[self.memoryAddress].get('status'), '02X'))
                                )
                            else:
                                self.dataStream += (",15 {0}{1}{2}{3}{4} 00000000 300c".format(format(swap32(int(self.currentEntry)), '08X'),
			                    format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08X'),
			                    self.accessoryType117bis,
			                    format(self.history[self.memoryAddress].get('status'), '02X'),
			                    format(swap32(int(self.history[self.memoryAddress].get('waterAmount'))), '08X'))
                                )
                        case 'thermo':
                            self.dataStream += (",11 {0}{1}{2}{3}{4}{5} 0000".format(format(swap32(int(self.currentEntry)), '08X'),
                            format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08X'),
                            self.accessoryType117,
			                format(self.history[self.memoryAddress].get('currentTemp') * 100, '04X'),
			                format(self.history[self.memoryAddress].get('setTemp') * 100, '04X'),
			                format(self.history[self.memoryAddress].get('valvePosition'), '02X'))
                            )
                        case 'custom':
                            result = []
                            bitmask = 0
                            dataStream = ("{0}{1}".format(swap32(int(self.currentEntry)), '08X'),
                            format(swap32(int(self.history[self.memoryAddress].get('time') - self.refTime - EPOCH_OFFSET)), '08X'),
                            )
                            for key, value in self.history[self.memoryAddress]:
                                if key != 'time':
                                    for i in range(len(self.signatures)):
                                        if self.signatures[i]['entry'] == key:
                                            match self.signatures[i]['length']:
                                                case 8:
                                                    result.append(format(swap32(int(value * self.signatures[i]['factor'])), '08X'))
                                                    break
                                                case 4:
                                                    result.append(format(swap16(int(value * self.signatures[i]['factor'])), '04X'))
                                                    break
                                                case 2:
                                                    result.append(format(value * self.signatures[i]['factor'], '02X'))
                                                    break
                                            bitmask += round(math.pow(2, i))
                            a = ''
                            for i in result:
                                a = a + i +' '
                            results = dataStream + ' ' + format(bitmask, '02X' ) + ' ' + a  # type: ignore
                            self.dataStream += (' ' + '{}'.format(len(re.sub(r"[^0-9A-F]", '', results, flags = re.I))/2+1) + ' ' + results + ',')
                            break
                self.currentEntry += 1
                self.memoryAddress = self.entry2address(self.currentEntry)
                if (self.currentEntry > self.lastEntry):
                    break
            logging.info("Data {0}: {1}".format(self.accessoryName, self.dataStream))
            sendStream= self.dataStream
            self.dataStream =''
            return hexToBase64(sendStream)
        else:
            self.transfer = False
            return hexToBase64('00')

    def setCurrentHistoryRequest(self, val):
        valHex = base64ToHex(val)
        #logging.info("Data request {0}: {1}".format(self.accessoryName, valHex))
        valInt = int(valHex[4:12], base=16)
        address = swap32(valInt)
        #hexAddress = '{:x}'.format(address)
        #logging.info("Address requested {0}: {1}".format(self.accessoryName, hexAddress))
        self.sendHistory(address)
    

    def setCurrentSetTime(self, val):
        x = bytearray(base64.b64decode(val))
        x.reverse()
        date_time = datetime.fromtimestamp(EPOCH_OFFSET + int(x.hex(),16))
        d = date_time.strftime("%d.%m.%Y, %H:%M:%S")
        logging.info("Clock adjust {0}: {1} - {2}".format(self.accessoryName, base64ToHex(val), d))
        