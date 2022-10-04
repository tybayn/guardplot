#!/usr/bin/env python3

# MIT License
#
# GuardPlot
#
# Copyright © 2020 Ty Bayn
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
# and associated documentation files (the "Software"), to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial 
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT 
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN 
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import datetime, pytz
from datetime import datetime, timedelta
from colorama import Fore, Style

#-------------------------------------DATA CLASS----------------------------------------
class DATA:
    
    #Constructor: Initializes all the points of the DATA class----------------------
    def __init__(self,host,d_events,is_reset,epoch):
        self.host = host
        self.dEvents = d_events
        self.isReset = is_reset
        self.epoch = epoch
        self.time = self.getMountainTime(datetime.utcfromtimestamp(epoch))
        self.isModerate = False
        self.isSevere = False
        self.isGlobalAnomaly = False
        self.isBlank = False
        
    #setCondition: Determines the level of anomalous data---------------------------
    def setCondition(self, low, high, oLow, oHigh):
        if (self.dEvents > oHigh and self.dEvents > high) or (self.dEvents < oLow and self.dEvents < low):
            self.isSevere = True

        elif ((self.dEvents > oHigh and self.dEvents <= high) or 
            (self.dEvents <= oHigh and self.dEvents > high) or
            (self.dEvents < oLow and self.dEvents >= low) or
            (self.dEvents >= oLow and self.dEvents < low)):
            self.isModerate = True

    #setGlobalAnomaly: Removes all anomaly tags and adds the isGlobalAnomaly tag----
    def setGlobalAnomaly(self):
        self.isModerate = False
        self.isSevere = False
        self.isGlobalAnomaly = True

    #setBlank: Removes all anomaly tags, used only if the data point is void -------
    def setBlank(self):
        self.isModerate = False
        self.isSevere = False
        self.isGlobalAnomaly = False
        self.isBlank = True

    #getChar: Returns the character used for representing the state of the data-----
    def getChar(self):
        if self.isModerate:
            return 'm'
        elif self.isSevere:
            return 's'
        elif self.isGlobalAnomaly:
            return 'g'
        elif self.isBlank:
            return 'b'
        else:
            return 'o'

    #getMountainTime: Converts the epoch into human readable HH:mm------------------
    def getMountainTime(self, dt):
        if self.is_dst(dt,"US/Mountain"):
            return (dt - timedelta(hours = 7)).strftime("%H:%M")
        else:
            return (dt - timedelta(hours = 8)).strftime("%H:%M")

    #setTime: Allows data to be set manually (HH:mm)--------------------------------
    def setTime(self, timeStr):
        self.time = timeStr

    #is_dst: Determines if the given epoch falls within or out of daylight savings--
    def is_dst(self, dt = None, timezone = "UTC"):
        if dt == None:
            dt = datetime.timezone(timezone)
        timezone = pytz.timezone(timezone)
        try:
            timezone_aware_date = timezone.localize(dt, is_dst = None)
        except pytz.NonExistentTimeError:
            return False
        except pytz.AmbiguousTimeError:
            return True
        return timezone_aware_date.tzinfo._dst.seconds != 0

    #isBlank: Returns if a datapoint is void---------------------------------------
    def isBlank(self):
        return self.isBlank
    
    #dstAdjust: adjusts the time a set number of hours
    def dstAdjust(self, direction = 1):
        if direction == 1:
             self.time = (datetime.strptime(self.time, "%H:%M") + timedelta(hours = 1)).strftime("%H:%M")
        else:
            self.time = (datetime.strptime(self.time, "%H:%M") - timedelta(hours = 1)).strftime("%H:%M")
#--------------------------------------------------------------------------------------

#----------------------------------DATESTATS CLASS-------------------------------------
class DATESTATS:
    
    #Constructor: Initializes all the points of the DATESTATS class----------------
    def __init__(self, host, date):
        self.host = host
        self.date = date
        self.overall = dict()
        self.data = []
        self.low = 0.0
        self.avg = 0.0
        self.high = 0.0
        self.stddev = 0.0
        self.numSevere = 0
        self.numModerate = 0
        self.numGlobal = 0

    #setStats: Sets the classes stats equal to provided values---------------------
    def setStats(self, low, avg, high, stddev):
        self.low = low
        self.avg = avg
        self.high = high
        self.stddev = stddev

    #setOverallStats: Set the global stats equal to provided values----------------
    def setOverallStats(self, low, avg, high, stddev):
        self.overall['low'] = float(low)
        self.overall['avg'] = float(avg)
        self.overall['high'] = float(high)
        self.overall['stddev'] = float(stddev)

    #addData: Adds a new DATA class object to the data array-----------------------
    def addData(self,data):
        self.data.append(data)
        if data.isModerate:
            self.numModerate = self.numModerate + 1
        if data.isSevere:
            self.numSevere = self.numSevere + 1
        if data.isGlobalAnomaly:
            self.numGlobal = self.numGlobal + 1

    #getChar: Used for host overall stats, returns char that represents state------
    def getChar(self):
        if self.avg > self.overall['high'] or self.avg < self.overall['low']:
            return 'm'
        else:
            return 'o'

    #dstAdjust: Adjusts all DATA class points for daylight savings-----------------
    def dstAdjust(self):
        if self.data[0].time.split(':')[0] == '23' or len(self.data) > 96:
            for i in range(0,8):
                if self.data[i].time.split(':')[0] == '23' or self.data[i].time.split(':')[0] == '00':
                    self.data[i].dstAdjust()

    #gapAdjust: Goes through and adds void data points for times the host didn't respond
    def gapAdjust(self):
        gapTimes = []
        for h in range (0,24):
            gapTimes.append(f"{h:02d}:01")
            gapTimes.append(f"{h:02d}:16")
            gapTimes.append(f"{h:02d}:31")
            gapTimes.append(f"{h:02d}:46")

        if len(self.data) >= 96:
            return

        gapData = []
        
        datai = 0
        for i in range(0, len(gapTimes)):
            if datai < len(self.data) and self.data[datai].time == gapTimes[i]:
                gapData.append(self.data[datai])
                datai = datai + 1
            else:
                gapData.append(DATA(self.host,-1,False,-1))
                gapData[i].setBlank()
                gapData[i].setTime(gapTimes[i])

        self.data = gapData
#--------------------------------------------------------------------------------------            

#-------------------------------------STATS CLASS--------------------------------------
class STATS:

    #Constructor: Initializes all the points of the STATS class--------------------
    def __init__(self, host, hasGlobal = False):
        self.host = host
        self.date = dict()
        self.hasGlobal = hasGlobal
        self.MENUSPACE = 17

    #addDateStat: Adds a new DATESTAT object to the dictionary---------------------
    def addDateStat(self, date):
        self.date[date.date] = date

    #printDates: Prints the dates in a calendar type list
    def printDates(self):
        dateLine = ""
        avgLine = ""
        modLine = ""
        sevLine = ""
        gloLine = ""

        entry = 0

        print("")
        for key, item in self.date.items():

            mod = False
            sev = False
            if (self.date[key].avg > self.date[key].overall['high']) or (self.date[key].avg < self.date[key].overall['low']):
                mod = True
            if mod and float(self.date[key].numSevere)/float(len(self.date[key].data)) > 0.33:
                sev = True

            if sev:
                dateLine += 's' + str(key).ljust(self.MENUSPACE,' ') + 'k'
            elif mod:
                dateLine += 'm' + str(key).ljust(self.MENUSPACE,' ') + 'k'
            else:
                dateLine += str(key).ljust(self.MENUSPACE,' ')
            avgLine += str("Average : " + str(round(self.date[key].avg))).ljust(self.MENUSPACE,' ')
            modLine += str("Moderate: " + str(self.date[key].numModerate)).ljust(self.MENUSPACE, ' ')
            sevLine += str("Severe  : " + str(self.date[key].numSevere)).ljust(self.MENUSPACE, ' ')
            gloLine += str("Global  : " + str(self.date[key].numGlobal)).ljust(self.MENUSPACE, ' ')
            entry = (entry + 1) % 7
            if entry == 0:
                print(Style.BRIGHT, end='')
                for char in dateLine:
                    if char == 's':
                        print(Fore.RED, end='')
                    elif char == 'm':
                        print(Fore.YELLOW, end='')
                    elif char == 'k':
                        print(Style.RESET_ALL + Style.BRIGHT, end='')
                    else:
                        print(char, end='')
                print("")
                print(Style.RESET_ALL, end='')
                print(avgLine)
                print(modLine)
                print(sevLine)
                if self.hasGlobal:
                    print(gloLine)
                dateLine = ""
                avgLine = ""
                modLine = ""
                sevLine = ""
                gloLine = ""
                print('')

        print(Style.BRIGHT, end='')
        for char in dateLine:
            if char == 's':
                print(Fore.RED, end='')
            elif char == 'm':
                print(Fore.YELLOW, end='')
            elif char == 'k':
                print(Style.RESET_ALL + Style.BRIGHT, end='')
            else:
                print(char, end='')
        print("")
        print(Style.RESET_ALL, end='')
        print(avgLine)
        print(modLine)
        print(sevLine)
        if self.hasGlobal:
            print(gloLine)
        print('')
#--------------------------------------------------------------------------------------    
        
        
