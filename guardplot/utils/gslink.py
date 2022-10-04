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

import sqlite3, sys, datetime, statistics, csv, configparser
from datetime import datetime
from utils import DATA, DATESTATS, STATS
from os import path

#---------------------------------------DBlink-----------------------------------------
class gslink:

    #Constructor: Loading Anomaly Log and Reason Dictionary into memory------------
    def __init__(self):
        self.home_dir = path.dirname(path.dirname(path.abspath(__file__)))
        self.config = configparser.ConfigParser()
        self.config.read(path.join(self.home_dir,"config.ini"))
        self.globalAnomalyDict = None
        print("Loading logs...")
        self.logDict = self.readLogs()
        self.reasonDict = self.readReasons()

    #isIP: Returns if an IP address if found in the database-----------------------
    def isIP(self, host):
        #Get all IPs
        conn = sqlite3.connect(path.join(self.home_dir,self.config.get("database","database")))
        c = conn.cursor()

        #Check if table exists, end if not
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='LOGS' ''')
        if c.fetchone()[0]==0 :
            print("\nDatabase not found! Looking for .db file in data/ directory!")
            c.close()
            sys.exit()

        query = ''' SELECT COUNT(*) FROM OVERALLSTATS WHERE host = ? '''
        dataTuple = (str(host), )
        c.execute(query, dataTuple)
        numHost = int(c.fetchone()[0])

        c.close()

        return numHost > 0

    #isDate: Returns if a date exists in the database-----------------------------
    def isDate(self, host, date):
        #Get all dates for the host
        conn = sqlite3.connect(path.join(self.home_dir,self.config.get("database","database")))
        c = conn.cursor()

        #Check if table exists, end if not
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='LOGS' ''')
        if c.fetchone()[0]==0 :
            print("\nDatabase not found! Looking for .db file in data/ directory!")
            c.close()
            sys.exit()

        query = ''' SELECT COUNT(*) FROM DAILYSTATS WHERE host = ? AND date = ? '''
        dataTuple = (str(host), str(date))
        c.execute(query, dataTuple)
        numDate = int(c.fetchone()[0])

        c.close()

        return numDate > 0

    #loadIPOverall: Loads all dates and datapoints into a single class-----------
    def loadIPOverall(self, ip, detectGlobal = False, date = None):
        
        #Create new STATS object
        newStats = STATS(ip, detectGlobal)

        #Get all dates for the host
        conn = sqlite3.connect(path.join(self.home_dir,self.config.get("database","database")))
        c = conn.cursor()

        #Check if table exists, end if not
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='LOGS' ''')
        if c.fetchone()[0]==0 :
            print("\nDatabase not found! Looking for .db file in data/ directory!")
            c.close()
            sys.exit()

        #If global is detected, we need to load the dictionary
        if detectGlobal and self.globalAnomalyDict == None:
            self.globalAnomalyDict = dict()
            print("\nGlobal Anomaly detection requested! This may take a few minutes...")
            c.execute(''' SELECT INDVSTATS.epoch, (COUNT(INDVSTATS.host)/((SELECT COUNT(INDVSTATS.host) FROM INDVSTATS GROUP BY epoch) / 100.0)) FROM INDVSTATS JOIN DAILYSTATS ON (INDVSTATS.host = DAILYSTATS.host AND INDVSTATS.date = DAILYSTATS.date) JOIN OVERALLSTATS ON (INDVSTATS.host = OVERALLSTATS.host) WHERE ((INDVSTATS.d_events > OVERALLSTATS.high AND INDVSTATS.d_events > DAILYSTATS.high) OR (INDVSTATS.d_events < OVERALLSTATS.low AND INDVSTATS.d_events < DAILYSTATS.low)) GROUP BY epoch ''')
            globAnomData = c.fetchall()
            for gDat in globAnomData:
                self.globalAnomalyDict[str(gDat[0])] = float(gDat[1])
            
        print("\nPreparing to load host data...")
        print("Loading [" + '-'*40 + "] ?/?", end='', flush = True)
        print(end='\r', flush = True)

        if date is None:
            query = ''' SELECT * FROM INDVSTATS WHERE host = ? ORDER BY date ASC '''
            dataTuple = (str(ip), )
            c.execute(query, dataTuple)
            allData = c.fetchall()
            query = ''' SELECT COUNT(*) FROM DAILYSTATS WHERE host = ? '''
            c.execute(query, dataTuple)
            size = int(c.fetchone()[0])
        

        else:
            query = ''' SELECT * FROM INDVSTATS WHERE host = ? AND date = ? '''
            dataTuple = (str(ip), str(date))
            c.execute(query, dataTuple)
            allData = c.fetchall()
            query = ''' SELECT COUNT(*) FROM DAILYSTATS WHERE host = ? AND date = ? '''
            c.execute(query, dataTuple)
            size = int(c.fetchone()[0])
        
        c.close()
        date = datetime.strptime(allData[0][3], "%Y-%m-%d")
        subData = []
        curNum = 1

        for entry in allData:
            curDate = datetime.strptime(entry[3], "%Y-%m-%d")

            load = int((curNum / size) * 40)
            left = 40 - load

            print("Loading [" + '='*load + '-'*left + "] " + str(curNum) + "/" + str(size), end='', flush = True)
            print(end='\r', flush = True)
            
            if curDate > date:
                newStats.addDateStat(self.loadIPDate(str(ip), date.strftime("%Y-%m-%d"), detectGlobal, subData))
                subData = []
                curNum = curNum + 1

            subData.append(entry)
            date = curDate
            

        newStats.addDateStat(self.loadIPDate(str(ip), date.strftime("%Y-%m-%d"), detectGlobal, subData))
        print("Loading [" + '='*40 + "] Done               ", flush = True)

        return newStats
         
    #loadIPDate: Load all data values for a particular date from the database----
    def loadIPDate(self, ip, date, detectGlobal = False, givenData = None):

        #Get all data from DB
        conn = sqlite3.connect(path.join(self.home_dir,self.config.get("database","database")))
        c = conn.cursor()

        #Check if table exists, end if not
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='LOGS' ''')
        if c.fetchone()[0]==0 :
            print("\nDatabase not found! Looking for .db file in data/ directory!")
            c.close()
            sys.exit()

        #If global is detected, we need to load the dictionary
        if detectGlobal and self.globalAnomalyDict == None:
            self.globalAnomalyDict = dict()
            print("\nGlobal Anomaly detection requested! This may take a few minutes...")
            c.execute(''' SELECT INDVSTATS.epoch, (COUNT(INDVSTATS.host)/((SELECT COUNT(INDVSTATS.host) FROM INDVSTATS GROUP BY epoch) / 100.0)) FROM INDVSTATS JOIN DAILYSTATS ON (INDVSTATS.host = DAILYSTATS.host AND INDVSTATS.date = DAILYSTATS.date) JOIN OVERALLSTATS ON (INDVSTATS.host = OVERALLSTATS.host) WHERE ((INDVSTATS.d_events > OVERALLSTATS.high AND INDVSTATS.d_events > DAILYSTATS.high) OR (INDVSTATS.d_events < OVERALLSTATS.low AND INDVSTATS.d_events < DAILYSTATS.low)) GROUP BY epoch ''')
            globAnomData = c.fetchall()
            for gDat in globAnomData:
                self.globalAnomalyDict[str(gDat)[0]] = float(gDat[1])

        query = ''' SELECT DAILYSTATS.low, DAILYSTATS.avg, DAILYSTATS.high, DAILYSTATS.stddev, OVERALLSTATS.low, OVERALLSTATS.avg, OVERALLSTATS.high, OVERALLSTATS.stddev FROM DAILYSTATS JOIN OVERALLSTATS ON (DAILYSTATS.host = OVERALLSTATS.host) WHERE DAILYSTATS.host = ? AND DAILYSTATS.date = ? '''
        dataTuple = (str(ip), str(date))
        c.execute(query, dataTuple)

        statData = c.fetchone()

        if givenData == None:
            query = ''' SELECT * FROM INDVSTATS WHERE host = ? and date = ? '''
            dataTuple = (str(ip), str(date))
            c.execute(query, dataTuple)

            indvData = c.fetchall()
        else:
            indvData = givenData

        #Look through the data to make a DATESTATS 
        newDateStats = DATESTATS(ip,date)
        newDateStats.setStats(statData[0], statData[1], statData[2], statData[3])
        newDateStats.setOverallStats(statData[4], statData[5], statData[6], statData[7])

        #Loop through each entry for indvstats
        for entry in indvData:
            curData = DATA(ip, entry[1], entry[2], entry[4])
            curData.setCondition(statData[0], statData[2], statData[4], statData[6])
            if curData.isSevere and detectGlobal:
                if self.globalAnomalyDict[str(entry[4])] >= 70:
                    curData.setGlobalAnomaly()

            newDateStats.addData(curData)

        c.close()
        newDateStats.dstAdjust()
        newDateStats.gapAdjust()
        return newDateStats

    #liveAnalysis: Does a short and simple analysis to determine if a value is anomalous
    def liveAnalysis(self, ip, epoch, events, prevEvents = -1):

        #Get all data from DB
        conn = sqlite3.connect(path.join(self.home_dir,self.config.get("database","database")))
        c = conn.cursor();    

        #Check if table exists, end if not
        c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='LOGS' ''')
        if c.fetchone()[0]==0 :
            print("\nDatabase not found! Looking for .db file in data/ directory!")
            c.close()
            sys.exit();    

        #Get last "30 days" of data
        print("\nLive Anomaly detection requested! Reading in historic data...")
        query = ''' SELECT epoch, events FROM LOGS WHERE host = ? LIMIT (30 * 96) '''
        dataTuple = (str(ip), )
        c.execute(query, dataTuple)
        histData = c.fetchall()

        #Get overall historical data
        query = ''' SELECT low, high FROM OVERALLSTATS WHERE host = ? '''
        dataTuple = (str(ip), )
        c.execute(query, dataTuple)
        overall = c.fetchone()

        c.close()

        #Seperate data, and only grab relevant hours
        conciseHistEvents = []

        curTime = ""
        time = datetime.fromtimestamp(epoch).strftime("%H:%M")

        for entry in histData:
            curTime = datetime.fromtimestamp(entry[0]).strftime("%H:%M")
            if curTime == time:
                conciseHistEvents.append(int(entry[1]))

        #Calculate avg and stddev for those hours
        if len(conciseHistEvents) > 0:
            eAvg = statistics.mean(conciseHistEvents)
            if len(conciseHistEvents) > 1:
                eStd = statistics.stdev(conciseHistEvents)
            else:
                eStd = 0
        else:
            eAvg = 0
            eStd = 0

        if prevEvents != -1:
            dEvent = events - prevEvents
        else:
            dEvent = -1

        anomReturn = "\nHost: " + str(ip) + "\nEpoch: " + str(epoch) + "\nEvents: " + str(events) + "\n\n"

        #Find anomalies based on events reported
        if int(events) > (eAvg + eStd):
            anomReason = "Anomaly: Higher than normal reported events compared to historical times!\nUpper Limit: " + str(eAvg + eStd)
        elif int(events) < (eAvg - eStd):
            anomReason = "Anomaly: Lower than normal reported events compared to historical times!\nLower Limit: " + str(eAvg - eStd)
        elif (dEvent == -1 and int(events) == 0) or (int(events) - dEvent == 0) :
            anomReason = "Anomaly: Zero events reported! Is host down?"
        elif dEvent != -1 and dEvent > overall[1]:
            anomReason = "Anomaly: Higher frequency of events reported when compared to host's overall data!"
        elif dEvent != -1 and dEvent < overall[0]:
            anomReason = "Anomaly: Lower frequency of events reported when compared to host's overall data!"
        else:
            anomReason = None

        if anomReason is None:
            anomReturn = anomReturn + "No anomalies found."
        else:
            anomReturn = anomReturn + "ANOMALY DETECTED!\n" + anomReason

        return anomReturn

    #addLog: Adds an anomaly to the anomaly log-----------------------------------
    def addLog(self,ip,epoch,type):
        key = str(ip) + "|" + str(epoch)

        if not key in self.logDict:
            self.logDict[key] = str(type)

    #readLogs: Reads the log csv into memory--------------------------------------
    def readLogs(self):
        logDict = dict()
        try:
            with open(path.join(self.home_dir,self.config.get("anomalies","logs")), mode='r') as infile:
                reader = csv.reader(infile)
                for rows in reader:
                    logDict[rows[0]] = rows[1]
        except OSError as e:
            open(path.join(self.home_dir,self.config.get("anomalies","logs")), mode='w+')

        return logDict

    #writeLogs: Writes the log memory structure back to a csv file----------------
    def writeLogs(self):
        print("\nWriting data to logs")
        with open(path.join(self.home_dir,self.config.get("anomalies","logs")), mode='w') as outfile:
            for key in self.logDict.keys():
                outfile.write(key + "," + self.logDict[key] + "\n")

    #readReasons: Reads the Reasons csv into the Reasons dictionary---------------
    def readReasons(self):
        reasonDict = dict()
        with open(path.join(self.home_dir,self.config.get("anomalies","reasons")), mode='r') as infile:
            reader = csv.reader(infile)
            for data in reader:
                reason = []
                for item in data[1:]:
                    reason.append(item)
                reasonDict[data[0]] = reason

        return reasonDict

    #getReason: Returns a list of possible reasons associated with a key-----------
    def getReason(self, key):
        reasonStr = ""
        for item in self.reasonDict[key]:
            reasonStr += item + ", "; 

        return reasonStr
#--------------------------------------------------------------------------------------
        
            


        
        
        
