# GuardPlot
Senior Year Capstone Project (SUU 2020): Visualization and Plotting Engine to visualize and detect anomalies in historic and live data.

GaurdPlot is a terminal based, Python3 log data analyzer. It will create databases, analyze log data, display visuals, guess at what went wrong, and keep a log of hosts, anomaly severity, and the time at which they occurred.

This software is currently only designed for Linux systems, specifically Debian.

## Prerequisites

#### pip3 Required Packages

Use the package manager [pip3](https://pip-python3.readthedocs.io/en/stable/) to install [argparse](https://docs.python.org/3/library/argparse.html) and [colorama](https://pypi.org/project/colorama/):


```bash
pip3 install argparse colorama
```

#### sqlite3 Database

The software utilizes sqlite3 for storing data accessible for Python3. sqlite3 should be included with Python3. If not, please download sqlite3 via [pip3](https://pip-python3.readthedocs.io/en/stable/):

```bash
pip3 install pysqlite3 
```

#### File Structure

Ensure that the following file structure is maintained and files are created:

```shell
guardplot
|  config.ini
|
└──data
|  |  anomReasons.csv
|
└──dbbuilder
|  |  dbbuilder.py
|
└──guardplot
   |  gsclasses.py
   |  gslink.py
   |  guardplot.py


``` 

#### anomReasons.csv

The anomReasons.csv file needs to exist for the program to have enough data to run. If the file is not present, create it and copy/paste the following into it and save it into the guardplot/data/ folder:

```shell
sevh3,dos attack,ddos attack
sevh2,dos attack,ddos attack,network is being probed
sevh1,network is being probed
sevl1,unknown reason
sevl2,unknown reason
sevl3,unknown reason
sev0,network is being held,recording host system error
glob,recording host system error
nores,system is being held,system is currently off
```

This data is read into a python dictionary, the first value is the key and is determined/hard coded in the software.

#### Configuration File

In the guardplot/ directory is the config.ini file that contains the following lines (the attributes are set to defaults):

```yaml
[database]
import = data/json
database = data/HostData.db

[anomalies]
logs = data/anomLogs.csv
reasons = data/anomReasons.csv
```

This is to set the file locations that are used by the program. Altering these will alter where the files are located.

* import: The directory that contains the json files that need to be read into the database
* database: The location of the database file used by the software
* logs: The location of the anomaly logs recorded by the software
* reasons: The best guess of the software as to the reasons behind anomalies

#### Input Data

The code is set up to read through all directories with the date format "YYYY-mm-dd" as the names, with each containing logs for times throughout that date. The dbbuilder.py software reads in the json formatted data, preprocesses it, and saves it into a sqlite3 database.

The Database reader is expecting the following json structure for each event:

```json
{host,events,date,epoch}
```

## Usage

#### Create the Database

The software requires that the json data be imported and read into a sqlite3 database. Before you can run any analysis, this database must be created using the dbbuilder.py program:

```shell
usage: dbbuilder.py [-a] [-s] [-h]

optional arguments:
  -h, --help         show this help message and exit
  -a, --all-reload   reload all entries in the database
  -s, --stat-reload  reload all stats in the database
```

This will construct a database with the following tables:
* LOGS: The raw data from the Json
* INDVSTATS: Contains the analysis and stats of each log entry
* DAILYSTATS: Contains the analysis and stats for each day of each host
* OVERALLSTATS: Contains the analysis and stats for each host for all time


NOTE: Using the command without any parameters will load any not included data from the Json resource and update the tables (the OVERALLSTATS table is completely recalculated).

* Using the [-a] parameter will drop all tables and recreate the database.

* Using the [-s] parameter will drop all stats entries in the database and recalculate them

The conversion of Json into sqlite3 is incredibly fast; however, the actual analysis performed on each and every data point is not. On average expect this process to take 6-10 hours to complete for the very first time use. After that the database is simply updated and shouldn't take long if done routinely.

#### Using GuardPlot

Once the database is created, populated, and all data analyzed, you can start your analysis of the data using the guardplot.py software. The Usage is below:

```shell
usage: GuardPlot.py [-h] [-a] [-g] [-i IP [-o | -d DATE | -l -e EVENTS [-p PREVIOUSEVENTS] -t TIME]]

optional arguments:
  -h, --help            show this help message and exit
  -a, --anomaly-view    displays details about anomalies rather than a plot
  -g, --global          performs global anomaly detection
  -i IP, --ip IP        evalute the given ip address
  -o, --overall         if ip is provided, view daily stats from last 33 date entries
  -d DATE, --date DATE  if ip is provided, evaluate the given date
  -l, --live            if ip is provided, performs live anomaly detection, event and time required
  -e EVENTS, --events EVENTS
                        when in live mode, evaluate the live data point
  -p PREVIOUSEVENTS, --previous-events PREVIOUSEVENTS
                        when in live mode, evaluate the data point compared to previous data point
  -t EPOCH, --time EPOCH
                        when in live mode, provide an epoch for comparison

```

## License
[MIT](https://choosealicense.com/licenses/mit/)
