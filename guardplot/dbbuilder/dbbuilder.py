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

import sqlite3, json, os, datetime, argparse, statistics
import configparser
from datetime import datetime
from os import path

#-------------------------------------Arg parsing--------------------------------------
parser = argparse.ArgumentParser()

parser.add_argument(
    "-a", "--all-reload",
    dest = "all",
    action = "store_const",
    const = True,
    help = "reload all entries in the database",
    default = False,
)

parser.add_argument(
    "-s", "--stat-reload",
    dest = "stat",
    action = "store_const",
    const = True,
    help = "reload all stats in the database",
    default = False,
)

args = parser.parse_args()
#--------------------------------------------------------------------------------------

#---------------------------------------Globals----------------------------------------
home_dir = path.dirname(path.dirname(path.abspath(__file__)))
config = configparser.ConfigParser()
config.read(path.join(home_dir,"config.ini"))
DATAPATH = path.join(home_dir,config.get("database","import"))
#--------------------------------------------------------------------------------------

#----------------------------------------MAIN------------------------------------------
def main():
    

    #Connect to database (will create if not found)
    conn = sqlite3.connect(path.join(home_dir,config.get("database","database")))
    c = conn.cursor()
    date = 0

    #Check if table exists, create if not
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='LOGS' ''')
    if c.fetchone()[0]==0 :
        print("\nDatabase not found, creating database...", flush = True)
        c.execute(''' CREATE TABLE LOGS ([host] text, [events] integer, [date] text, [epoch] INTEGER) ''')
        print("LOGS table created!")
        c.execute(''' CREATE TABLE INDVSTATS ([host] text, [d_events] integer, [is_reset] integer, [date] text,[epoch] INTEGER) ''')
        print("INDVSTATS table created!")
        c.execute(''' CREATE TABLE DAILYSTATS ([host] text, [low] real, [avg] real, [high] real, [stddev] real, [date] text) ''')
        print("DAILYSTATS table created!")
        c.execute(''' CREATE TABLE OVERALLSTATS ([host] text, [low] real, [avg] real, [high] real, [stddev] real) ''')
        print("OVERALLSTATS table created!")
        stopDate = datetime.strptime("1970-01-01", "%Y-%m-%d")
    
    #If all flag is set (args)
    elif args.all:
        print("\nAll reload requested. Reloading database...", flush = True)
        c.execute(''' DROP TABLE LOGS ''')
        c.execute(''' DROP TABLE INDVSTATS ''')
        c.execute(''' DROP TABLE DAILYSTATS ''')
        c.execute(''' DROP TABLE OVERALLSTATS ''')
        print("Tables dropped. Creating database...")
        c.execute(''' CREATE TABLE LOGS ([host] text, [events] integer, [date] text, [epoch] INTEGER) ''')
        print("LOGS table created!")
        c.execute(''' CREATE TABLE INDVSTATS ([host] text, [d_events] integer, [is_reset] integer, [date] text,[epoch] INTEGER) ''')
        print("INDVSTATS table created!")
        c.execute(''' CREATE TABLE DAILYSTATS ([host] text, [low] real, [avg] real, [high] real, [stddev] real, [date] text) ''')
        print("DAILYSTATS table created!")
        c.execute(''' CREATE TABLE OVERALLSTATS ([host] text, [low] real, [avg] real, [high] real, [stddev] real) ''')
        print("OVERALLSTATS table created!")
        stopDate = datetime.strptime("1970-01-01", "%Y-%m-%d")

    #If stats flag is set (args)
    elif args.stat:
        print("\nStat reload requested. Reloading database...", flush = True)
        c.execute(''' DROP TABLE INDVSTATS ''')
        c.execute(''' DROP TABLE DAILYSTATS ''')
        c.execute(''' DROP TABLE OVERALLSTATS ''')
        print("Tables dropped. Creating database...")
        c.execute(''' CREATE TABLE INDVSTATS ([host] text, [d_events] integer, [is_reset] integer, [date] text,[epoch] INTEGER) ''')
        print("INDVSTATS table created!")
        c.execute(''' CREATE TABLE DAILYSTATS ([host] text, [low] real, [avg] real, [high] real, [stddev] real, [date] text) ''')
        print("DAILYSTATS table created!")
        c.execute(''' CREATE TABLE OVERALLSTATS ([host] text, [low] real, [avg] real, [high] real, [stddev] real) ''')
        print("OVERALLSTATS table created!")
        stopDate = datetime.strptime("1970-01-01", "%Y-%m-%d")

    #If Table exists, get last entry date (adding is better)
    else:
        print("\nNew data load requested. Loading database...", flush = True)
        c.execute(''' DROP TABLE OVERALLSTATS ''')
        c.execute(''' CREATE TABLE OVERALLSTATS ([host] text, [low] real, [avg] real, [high] real, [stddev] real) ''')
        c.execute(''' SELECT date, MAX(epoch) FROM LOGS ''')
        date = c.fetchone()[0] or "1970-01-01"
        print("\nLast DB entry for " + str(date)); 
        query = ''' DELETE FROM LOGS WHERE date = ? '''
        dataTuple =(str(date), )
        c.execute(query,dataTuple)
        query = ''' DELETE FROM INDVSTATS WHERE date = ? '''
        c.execute(query,dataTuple)
        query = ''' DELETE FROM DAILYSTATS WHERE date = ? '''
        c.execute(query,dataTuple)
        stopDate = datetime.strptime(date, "%Y-%m-%d")

    #If not just stat reload
    if not args.stat:

        #Load Json data into sqlite
        print("Reading in Json data...", flush = True)
        readThreads = []
        data = []
        curVal = 1
        fileSize = len(os.listdir(DATAPATH))

        #Read through all json data
        for dirs in os.listdir(DATAPATH):
            print('Reading in data (' + str(dirs) +') ' + str(curVal) + '/' + str(fileSize) , end = '', flush = True)
            print(end = '\r', flush = True)
            dirDate = datetime.strptime(dirs, "%Y-%m-%d")

            if dirDate >= stopDate or args.all:
                for file in os.listdir(DATAPATH + "/" + dirs):
                    jsFile = json.load(open(f"{DATAPATH}/{dirs}/{file}","r"))
                    for line in jsFile:
                        query = ''' INSERT INTO LOGS (host, events, date, epoch) VALUES(?,?,?,?) '''
                        dataTuple = (line["host"],line["events"],line["date"],line["epoch"])
                        c.execute(query,dataTuple)
            curVal = curVal + 1

        conn.commit()
        print("LOGS table populated.                            ")

    print("Beginning STATS analysis...")

    #Get current list of IPs and run full stat analysis
    print("Getting list of hosts...", flush = True)
    c.execute(''' SELECT host FROM LOGS GROUP BY host ''')
    ipList = c.fetchall()
    ipSize = len(ipList)
    curVal = 1
    print("Starting analysis of hosts...", flush = True)
    logQuery = ''' INSERT INTO INDVSTATS (host, d_events, is_reset, date, epoch) VALUES(?,?,?,?,?) '''

    for ip in ipList:
        #Start Printing which ip is being analyzed and total count
        print("Analyzing host (" + str(ip[0]) +") " + str(curVal) + "/" + str(ipSize) + " (D)    ", end = '', flush = True)
        print(end = '\r', flush = True)
        
        #Analyze IP for Daily Statistics and additional LOG data
        query = ''' SELECT * FROM LOGS WHERE host = ? ORDER BY epoch ASC '''
        dataTuple = (str(ip[0]), )
        c.execute(query,dataTuple)

        data = []
        prevData = 0
        rows = c.fetchall()
        date = datetime.strptime("1970-01-01", "%Y-%m-%d")
        isFirst = True
        curVal2 = 1
        logQueryTuples = []
        for line in rows:
            print("Analyzing host (" + str(ip[0]) +") " + str(curVal) + "/" + str(ipSize) + " (D) " + str(curVal2) + "/" + str(len(rows)), end = '', flush = True)
            print(end = '\r', flush = True)
            curDate = datetime.strptime(line[2], "%Y-%m-%d")

            #Check if only recent or all replace
            if curDate >= stopDate or args.all or args.stat:
                #If date changes, drop stats into database and reset counters
                if curDate > date:
                    if isFirst:
                        isFirst = False
                    else:
                        avg = statistics.mean(data)
                        if len(data) > 1:
                            stddev = statistics.stdev(data)
                        else:
                            stddev = 0.0
                        low = avg - stddev
                        high = avg + stddev
                        query = ''' INSERT INTO DAILYSTATS (host, low, avg, high, stddev, date) VALUES(?,?,?,?,?,?) '''
                        dataTuple = (str(ip[0]), low, avg, high, stddev, date.strftime("%Y-%m-%d"))
                        c.execute(query,dataTuple)
                        data = []
                
                isReset = 0
                if prevData > int(line[1]):
                    prevData = 0
                    isReset = 1

                d_events = int(line[1]) - prevData
                data.append(float(d_events))
                
                prevData = int(line[1])
                date = curDate

                #Write delta events and isReset to INDVSTATS table, to add further analytical power
                logQueryTuples.append((str(ip[0]),int(d_events),int(isReset),str(line[2]),int(line[3])))
            curVal2 = curVal2 + 1

        avg = statistics.mean(data)
        if len(data) > 1:
            stddev = statistics.stdev(data)
        else:
            stddev = 0.0
        low = avg - stddev
        high = avg + stddev
        query = ''' INSERT INTO DAILYSTATS (host, low, avg, high, stddev, date) VALUES(?,?,?,?,?,?) '''
        dataTuple = (str(ip[0]), low, avg, high, stddev, date.strftime("%Y-%m-%d"))
        c.execute(query,dataTuple)

        #Massive log update
        c.executemany(logQuery, logQueryTuples)

        #Analyze IP for Overall Statistics
        print("Analyzing host (" + str(ip[0]) +") " + str(curVal) + "/" + str(ipSize) + " (O)            ", end = '', flush = True)
        print(end = '\r', flush = True)
        query = ''' SELECT d_events FROM INDVSTATS WHERE host = ? '''
        dataTuple = (str(ip[0]), )
        c.execute(query, dataTuple)
        deltaEventsIn = c.fetchall()
        deltaEvents = []
        for evt in deltaEventsIn:
            deltaEvents.append(float(evt[0]))

        overallAvg = statistics.mean(deltaEvents)
        if len(deltaEvents) > 1:
            overallStdDev = statistics.stdev(deltaEvents)
        else:
            overallStdDev = 0.0
        overallLow = overallAvg - overallStdDev
        overallHigh = overallAvg + overallStdDev

        query = ''' INSERT INTO OVERALLSTATS (host, low, avg, high, stddev) VALUES(?,?,?,?,?) '''
        dataTuple = (str(ip[0]), overallLow, overallAvg, overallHigh, overallStdDev)
        c.execute(query, dataTuple)


        curVal = curVal + 1
            
    print("STATS tables populated.                                  ")
    
    print("Databases populated. Operation Complete!")
    conn.commit()
    c.close()
#--------------------------------------------------------------------------------------

main()