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

import sys,os,json,threading,datetime,statistics,time, argparse, configparser;
from os import path;
from threading import Thread;
from datetime import datetime, timezone;
from colorama import Fore, Style;
from gslink import gslink;

#Globals
SEVEREHIGH3 = "sevh3";
SEVEREHIGH2 = "sevh2";
SEVEREHIGH1 = "sevh1";
SEVERELOW3 = "sevl3";
SEVERELOW2 = "sevl2";
SEVERELOW1 = "sevl1";
SEVEREZERO = "sev0";
GLOBALANOM = "glob";
NORESPONSE = "nores";

#-------------------------------------Arg parsing--------------------------------------
parser = argparse.ArgumentParser();

parser.usage = "guardplot.py [-h] [-a] [-g] [-i IP [-o | -d DATE | -l -e EVENTS [-p PREVIOUSEVENTS] -t TIME]]";

parser.add_argument(
	"-a", "--anomaly-view",
	dest = "anom",
	action = "store_const",
	const = True,
	help = "displays details about anomalies rather than a plot",
	default = False,
)

parser.add_argument(
	"-g", "--global",
	dest = "glob",
	action = "store_const",
	const = True,
	help = "performs global anomaly detection",
	default = False,
)

parser.add_argument(
	"-i", "--ip",
	type = str,
	dest = "ip",
	action = "store",
	help = "evalute the given ip address",
	default = None,
)

parser.add_argument(
	"-o", "--overall",
	dest = "overall",
	action = "store_const",
	const = True,
	help = "if ip is provided, view daily stats from last 33 date entries",
	default = False,
)

parser.add_argument(
	"-d", "--date",
	type = str,
	dest = "date",
	action = "store",
	help = "if ip is provided, evaluate the given date",
	default = None,
)

parser.add_argument(
	"-l", "--live",
	dest = "live",
	action = "store_const",
	const = True,
	help = "if ip is provided, performs live anomaly detection, event and time required",
	default = False,
)

parser.add_argument(
	"-e", "--events",
	type = int,
	dest = "events",
	action = "store",
	help = "when in live mode, evaluate the live data point",
	default = None,
)

parser.add_argument(
	"-p", "--previous-events",
	type = int,
	dest = "previousEvents",
	action = "store",
	help = "when in live mode, evaluate the data point compared to previous data point",
	default = None,
)

parser.add_argument(
	"-t", "--time",
	type = int,
	dest = "epoch",
	action = "store",
	help = "when in live mode, provide an epoch for comparison",
	default = None,
)

args = parser.parse_args();
#--------------------------------------------------------------------------------------

#----------------------------------------MAIN------------------------------------------
def main():

	#Make sure args are valid
	if args.ip is None and args.date is not None:
		print("When using --date, --ip-address is required\n", file=sys.stderr);
		parser.print_help();
		exit(1);

	if args.ip is None and args.overall == True:
		print("When using --overall, --ip-address is required\n", file=sys.stderr);
		parser.print_help();
		exit(1);

	if args.live and (args.events is None or args.epoch is None or args.ip is None):
		print("When using --live, --ip-address, --events and --time are required\n", file=sys.stderr);
		parser.print_help();
		exit(1);

	print("Welcome to GuardPlot!");

	#Create the DataBase Link
	link = gslink();
	
	#If Live mode
	if args.live == True:
		if args.ip is None or not link.isIP(args.ip):
			print("Invalid IP or IP not found\n");
			exit(1);

		if args.previousEvents is None:
			print(link.liveAnalysis(args.ip,args.epoch,args.events));
		else:
			print(link.liveAnalysis(args.ip,args.epoch,args.events, args.previousEvents));

	else:
		#Check if com arg IP exists
		if args.ip is None or not link.isIP(args.ip):
			print("Please choose an IP address to analyze.\n");
			ip = input("Input IP: ");

			while not link.isIP(ip):
				print("\nIP not found in database! Please try again!");
				ip = input("Input IP: ");
		else:
			ip = args.ip;

		#Check if loading single date
		if args.overall == True:
			clearScreen();
			curHost = link.loadIPOverall(ip);
			clearScreen();
			guardPlotOverall(curHost);
			input("Press enter to continue...");

		elif args.date is None or not link.isDate(args.ip, args.date):
			clearScreen();
			if args.glob == True:
				curHost = link.loadIPOverall(ip, True);
			else:
				curHost = link.loadIPOverall(ip);
			date = "";
			while date != quit:
				clearScreen();
				curHost.printDates();
				date = input("Input date (type 'all' for overall stats or 'quit' to exit): ");

				if date == "quit" or date == "q" or date == "Q":
					break;

				if date == "all":
					clearScreen();
					guardPlotOverall(curHost);
				else:
					if not link.isDate(ip, date):
						print("No such date for host found");
					else:
						clearScreen();
						if args.anom == True:
							guardList(curHost.date[str(date)],link);
						else:
							guardPlot(curHost.date[str(date)]);

				input("Press enter to continue...");
				clearScreen();

		else:
			clearScreen();
			if args.glob == True:
				curHost = link.loadIPOverall(ip, True, args.date);
			else:
				curHost = link.loadIPOverall(ip, False, args.date);
			clearScreen();
			if args.anom == True:
				guardList(curHost.date[str(args.date)],link);
			else:
				guardPlot(curHost.date[str(args.date)]);

			input("Press enter to continue...");
		
#--------------------------------------------------------------------------------------
	
#--------------------------------GUARD PLOT METHOD-------------------------------------
def guardPlot(data):

	HITCHAR = "o";
	MODCHAR = "m";
	SEVCHAR = "s";
	GLOCHAR = "g";
	BLACHAR = "b";

	#Create stat data
	seg = 12;
	maxLimit = 100;
	xLimit = 100;
	if len(data.data) - 1 < maxLimit:
		xLimit = len(data.data) - 1;

	minVal = 999999;
	maxVal = 0;

	for i in range(0, len(data.data) - 1):
		if not data.data[i].isBlank:
			if data.data[i].dEvents > maxVal:
				maxVal = data.data[i].dEvents;
			if data.data[i].dEvents < minVal:
				minVal = data.data[i].dEvents;

	stepVal = (maxVal - minVal) / 20;
	maxWidth = len(str(maxVal));

	#Create step values
	avgStep = stepVal;
	avgI = -1;
	maxStep = stepVal;
	maxI = -1;
	minStep = stepVal;
	minI = -1;

	allAvgStep = stepVal;
	allAvgI = -1;
	allMaxStep = stepVal;
	allMaxI = -1;
	allMinStep = stepVal;
	allMinI = -1;

	#Get values for Graphical steps
	stepList = [];
	for i in range(0,20):
		curStep = maxVal - (stepVal * i);
		stepList.append(curStep);
		if avgStep > abs(curStep - data.avg):
			avgStep = abs(curStep - data.avg);
			avgI = i;
		if maxStep > abs(curStep - (data.high)):
			maxStep = abs(curStep - (data.high));
			maxI = i;
		if minStep > abs(curStep - (data.low)):
			minStep = abs(curStep - (data.low));
			minI = i;

		if allAvgStep > abs(curStep - data.overall['avg']):
			allAvgStep = abs(curStep - data.overall['avg']);
			allAvgI = i;
		if allMaxStep > abs(curStep - (data.overall['high'])):
			allMaxStep = abs(curStep - (data.overall['high']));
			allMaxI = i;
		if allMinStep > abs(curStep - (data.overall['low'])):
			allMinStep = abs(curStep - (data.overall['low']));
			allMinI = i;

	#Create the plot with avg, std dev lines, and y range values
	plot = [];
	for i in range(0,20):
		if allAvgI == i and (maxI == i or minI == i):
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |=DEV/AVG  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -");
		elif allAvgI == i and avgI == i:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |=AVG/AVG- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -");
		elif avgI == i and (allMaxI == i or allMinI == i):
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |=AVG/DEV- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -");
		elif (maxI == i or minI == i) and (allMaxI == i or allMinI == i):
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |=DEV/DEV  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -");
		elif allAvgI == i:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |-AVG- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -");
		elif allMaxI == i or allMinI == i:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |-STD DEV  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -");
		elif avgI == i:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " | AVG- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -");
		elif maxI == i or minI == i:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " | STD DEV  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -");
		else:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |                                                                                                             ");
	plot.append(str(" ").rjust(maxWidth + 1,' ') + " |_________|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___|___");

	#Assign untouched Min and Max stdDevs to min and max of graph
	if minI == -1:
		minI = 21;
	if allMinI == -1:
		allMinI = 21;

	#Go through the data and plot the data points on the graph
	xRight = len(plot[len(plot) - 1]) - 1;

	for i in range(0,xLimit+1):
		x = xRight - i - (maxLimit - xLimit) + 1;
		point = data.data[len(data.data) - 1 - i];

		if not point.isBlank:
			y = min(range(len(stepList)), key=lambda l: abs(stepList[l] - point.dEvents));
			curLine = list(plot[y]);
			curLine[x] = point.getChar();
			plot[y] = "".join(curLine);

	#Print out the plot with colors
	print(' ', flush = True);
	print(("Data for " + str(data.host) + " on " + str(data.date)).center(120, ' '), flush = True);
	print("Events", flush = True);
	curI = 0;
	for line in plot:

		if "=DEV" in line or "=AVG" in line:
			color = 0 % 2;
			for char in line:
				if char in "=AVG/DE-":
					if color == 0:
						print(Fore.GREEN + char + Style.RESET_ALL, end = '', flush = True);
					else:
						print(Fore.BLUE + char + Style.RESET_ALL, end = '', flush = True);
					if char in "/-":
						color = (color + 1) % 2;
				elif char == HITCHAR:
					print(Fore.WHITE + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == MODCHAR:
					print(Fore.YELLOW + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == SEVCHAR:
					print(Fore.RED + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == GLOCHAR:
					print(Fore.MAGENTA + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				else:
					print(char, end='');
			print('', flush = True);
		elif "-STD DEV" in line or "-AVG" in line:
			for char in line:
				if char in "-AVGSTDEV":
					print(Fore.BLUE + char + Style.RESET_ALL, end='', flush = True);
				elif char == HITCHAR:
					print(Fore.WHITE + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == MODCHAR:
					print(Fore.YELLOW + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == SEVCHAR:
					print(Fore.RED + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == GLOCHAR:
					print(Fore.MAGENTA + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				else:
					print(char, end='');
			print('', flush = True);
		elif " STD DEV" in line or " AVG" in line:
			for char in line:
				if char in "-AVGSTDEV":
					print(Fore.GREEN + char + Style.RESET_ALL, end='', flush = True);
				elif char == HITCHAR:
					print(Fore.WHITE + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == MODCHAR:
					print(Fore.YELLOW + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == SEVCHAR:
					print(Fore.RED + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == GLOCHAR:
					print(Fore.MAGENTA + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				else:
					print(char, end='');
			print('', flush = True);
		else:
			for char in line:
				if char == HITCHAR:
					print(Fore.WHITE + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == MODCHAR:
					print(Fore.YELLOW + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == SEVCHAR:
					print(Fore.RED + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == GLOCHAR:
					print(Fore.MAGENTA + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				else:
					print(char, end='');
			print('', flush = True);
		curI = curI + 1;

	#Print out data times below graph
	timeLine = str("").rjust(maxWidth + 1,' ') + "      ";
	for i in range(0,len(data.data)):
		if i % 8 == 0:
			curTime = data.data[i].time.rjust(8,' ');
			timeLine += curTime;
	print(timeLine);

	#Print data
	print('');
	print(str(" ").rjust(maxWidth + 1,' '),end='');
	print("  o - Normal".ljust(30, ' '), end='');
	print(Fore.YELLOW + "o" + Style.RESET_ALL + " - Moderate Anomaly".ljust(29, ' '), end='');
	print(Fore.RED + "o" + Style.RESET_ALL + " - Severe Anomaly".ljust(29, ' '), end='');
	print(Fore.MAGENTA + "o" + Style.RESET_ALL + " - Global Anomaly".ljust(29, ' '), end='');
	print('\n');
	print(Fore.GREEN + str(" ").rjust(maxWidth + 1,' ') + (" || " + Style.RESET_ALL + "CURRENT DATE STATS").ljust(56, ' '), end='');
	print(Fore.BLUE + " || " + Style.RESET_ALL + "OVERALL STATS");
	print(Fore.GREEN + str(" ").rjust(maxWidth + 1,' ') + (" || " + Style.RESET_ALL + " Average Events: " + str(round(data.avg))).ljust(56, ' '), end='');
	print(Fore.BLUE + " || " + Style.RESET_ALL + " Average Events: " + str(round(data.overall['avg'])));
	print(Fore.GREEN + str(" ").rjust(maxWidth + 1,' ') + (" || " + Style.RESET_ALL + " Std Deviation: " + str(round(data.stddev))).ljust(56, ' '), end='');
	print(Fore.BLUE + " || " + Style.RESET_ALL + " Std Deviation: " + str(round(data.overall['stddev'])));
	print('');
#--------------------------------------------------------------------------------------

#----------------------------OVERALL GUARD PLOT METHOD---------------------------------
def guardPlotOverall(data):

	HITCHAR = "o";
	MODCHAR = "m";
	SEVCHAR = "s";
	GLOCHAR = "g";
	BLACHAR = "b";

	if len(data.date) >= 33:
		keyList = list(data.date.keys())[-33:]
	else:
		keyList = list(data.date.keys());	

	#Create stat data
	seg = 12;
	maxLimit = 33;
	xLimit = 33;
	if len(keyList) - 1 < maxLimit:
		xLimit = len(keyList) - 1;

	minVal = 999999;
	maxVal = 0;

	for key in keyList:
		if data.date[key].avg > maxVal:
			maxVal = data.date[key].avg;
		if data.date[key].avg < minVal:
			minVal = data.date[key].avg;

	stepVal = (maxVal - minVal) / 20;
	maxWidth = len(str(round(maxVal)));

	#Create step values
	allAvgStep = stepVal;
	allAvgI = -1;
	allMaxStep = stepVal;
	allMaxI = -1;
	allMinStep = stepVal;
	allMinI = -1;

	#Get values for Graphical steps
	stepList = [];
	for i in range(0,20):
		curStep = maxVal - (stepVal * i);
		stepList.append(curStep);

		if allAvgStep > abs(curStep - data.date[keyList[0]].overall['avg']):
			allAvgStep = abs(curStep - data.date[keyList[0]].overall['avg']);
			allAvgI = i;
		if allMaxStep > abs(curStep - (data.date[keyList[0]].overall['high'])):
			allMaxStep = abs(curStep - (data.date[keyList[0]].overall['high']));
			allMaxI = i;
		if allMinStep > abs(curStep - (data.date[keyList[0]].overall['low'])):
			allMinStep = abs(curStep - (data.date[keyList[0]].overall['low']));
			allMinI = i;

	#Create the plot with avg, std dev lines, and y range values
	plot = [];
	for i in range(0,20):

		if allAvgI == i:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |-AVG- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -");
		elif allMaxI == i or allMinI == i:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |-STD DEV  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  - -");
		else:
			plot.append(str(round(stepList[i])).rjust(maxWidth + 1,' ') + " |                                                                                                             ");
	plot.append(str(" ").rjust(maxWidth + 1,' ') + " |_________|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|__|");

	#Assign untouched Min and Max stdDevs to min and max of graph
	if allMinI == -1:
		allMinI = 21;

	#Go through the data and plot the data points on the graph
	xRight = len(plot[len(plot) - 1]) - 4;

	for i in range(0,xLimit+1):
		x = xRight - int(3 * i) - (maxLimit - xLimit) + 1;
		point = data.date[keyList[len(keyList) - 1 - i]];

		y = min(range(len(stepList)), key=lambda l: abs(stepList[l] - point.avg));
		curLine = list(plot[y]);
		curLine[x] = point.getChar();
		plot[y] = "".join(curLine);

	#Print out the plot with colors
	print(' ', flush = True);
	print(("Overall data for " + str(data.host) + " (Last 33 Dates with entries)").center(120, ' '), flush = True);
	print("Events", flush = True);
	curI = 0;
	for line in plot:

		if "-STD DEV" in line or "-AVG" in line:
			for char in line:
				if char in "-AVGSTDEV":
					print(Fore.BLUE + char + Style.RESET_ALL, end='', flush = True);
				elif char == HITCHAR:
					print(Fore.WHITE + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == MODCHAR:
					print(Fore.YELLOW + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == SEVCHAR:
					print(Fore.RED + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == GLOCHAR:
					print(Fore.MAGENTA + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				else:
					print(char, end='');
			print('', flush = True);
		else:
			for char in line:
				if char == HITCHAR:
					print(Fore.WHITE + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == MODCHAR:
					print(Fore.YELLOW + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == SEVCHAR:
					print(Fore.RED + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				elif char == GLOCHAR:
					print(Fore.MAGENTA + HITCHAR + Style.RESET_ALL, end = '', flush = True);
				else:
					print(char, end='');
			print('', flush = True);
		curI = curI + 1;

	#Print out data times below graph
	timeLine1 = str("").rjust(maxWidth + 1,' ') + "    MM:    ";
	timeLine2 = str("").rjust(maxWidth + 1,' ') + "    - :    ";
	timeLine3 = str("").rjust(maxWidth + 1,' ') + "    DD:    ";

	for i in range(0,len(keyList)):
		timeLine1 += data.date[keyList[i]].date[5:7].ljust(3,' ');
		timeLine2 += "-".ljust(3,' ');
		timeLine3 += data.date[keyList[i]].date[8:].ljust(3,' ');

	print(timeLine1);
	print(timeLine2);
	print(timeLine3);

	#Print data
	print('');
	print(str(" ").rjust(maxWidth + 1,' '),end='');
	print("  o - Normal".ljust(30, ' '), end='');
	print(Fore.YELLOW + "o" + Style.RESET_ALL + " - Moderate Anomaly".ljust(29, ' '), end='');
	print(Fore.RED + "o" + Style.RESET_ALL + " - Severe Anomaly".ljust(29, ' '), end='');
	print(Fore.MAGENTA + "o" + Style.RESET_ALL + " - Global Anomaly".ljust(29, ' '), end='');
	print('\n');

#--------------------------------------------------------------------------------------

#--------------------------------GUARD LIST METHOD-------------------------------------
def guardList(data, link):
	print(' ', flush = True);
	print(("Anomalies for " + str(data.host) + " on " + str(data.date)).center(120, ' '), flush = True); 

	line1 = "\n";
	line2 = "";
	line3 = "";
	line4 = "";
	line5 = "";
	line6 = "";
	hit = 0;
	isHit = False;

	#Go through each data item for the date and determine the level of anomaly
	for item in data.data:

		isHit = False;

		#If no response at a given time
		if item.isBlank:
			line1 = line1 + ("ANOMALY DETECTED: Failure to report").ljust(70,' ');
			line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
			line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
			line4 = line4 + ("Details: No report from host").ljust(70,' ');
			line5 = line5 + ("Possible Causes: " + link.getReason(NORESPONSE)).ljust(70,' ');
			line6 = line6 + (" ").ljust(70,' ');
			link.addLog(data.host,item.epoch,NORESPONSE);
			hit = (hit + 1) % 2;
			isHit = True;

		#If there is a response, but it was zero
		elif item.dEvents == 0:
				line1 = line1 + ("ANOMALY DETECTED: Severely Zero").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: 0 events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(SEVEREZERO)).ljust(70,' ');
				line6 = line6 + (" ").ljust(70,' ');
				link.addLog(data.host,item.epoch,SEVEREZERO);
				hit = (hit + 1) % 2;
				isHit = True;

		#If the value is well outside all std devs
		elif item.isSevere:

			#Subcategories of severity
			if item.dEvents > (data.high + (data.stddev * (2.0/3.0))):
				line1 = line1 + ("ANOMALY DETECTED: High Event Frequency (SEV Lev:3)").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(SEVEREHIGH3)).ljust(70,' ');
				line6 = line6 + ("Upper limit: " + str(data.high)).ljust(70,' ');
				link.addLog(data.host,item.epoch,SEVEREHIGH3);
				hit = (hit + 1) % 2;
				isHit = True;
			elif item.dEvents > (data.high + (data.stddev * (1.0/3.0))):
				line1 = line1 + ("ANOMALY DETECTED: High Event Frequency (SEV Lev:2)").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(SEVEREHIGH2)).ljust(70,' ');
				line6 = line6 + ("Upper limit: " + str(data.high)).ljust(70,' ');
				link.addLog(data.host,item.epoch,SEVEREHIGH2);
				hit = (hit + 1) % 2;
				isHit = True;
			elif item.dEvents > (data.high):
				line1 = line1 + ("ANOMALY DETECTED: High Event Frequency (SEV Lev:1)").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(SEVEREHIGH1)).ljust(70,' ');
				line6 = line6 + ("Upper limit: " + str(data.high)).ljust(70,' ');
				link.addLog(data.host,item.epoch,SEVEREHIGH1);
				hit = (hit + 1) % 2;
				isHit = True;
			elif item.dEvents < (data.low - (data.stddev * (2.0/3.0))):
				line1 = line1 + ("ANOMALY DETECTED: Low Event Frequency (SEV Lev:3)").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(SEVERELOW3)).ljust(70,' ');
				line6 = line6 + ("Lower limit: " + str(data.low)).ljust(70,' ');
				link.addLog(data.host,item.epoch,SEVERELOW3);
				hit = (hit + 1) % 2;
				isHit = True;
			elif item.dEvents < (data.low - (data.stddev * (1.0/3.0))):
				line1 = line1 + ("ANOMALY DETECTED: Low Event Frequency (SEV Lev:2)").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(SEVERELOW2)).ljust(70,' ');
				line6 = line6 + ("Lower limit: " + str(data.low)).ljust(70,' ');
				link.addLog(data.host,item.epoch,SEVERELOW2);
				hit = (hit + 1) % 2;
				isHit = True;
			elif item.dEvents < (data.low):
				line1 = line1 + ("ANOMALY DETECTED: Low Event Frequency (SEV Lev:1)").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(SEVERELOW1)).ljust(70,' ');
				line6 = line6 + ("Lower limit: " + str(data.low)).ljust(70,' ');
				link.addLog(data.host,item.epoch,SEVERELOW1);
				hit = (hit + 1) % 2;
				isHit = True;

		#If the found anomaly is a global anomaly
		elif item.isGlobalAnomaly:
			if item.dEvents > data.avg:
				line1 = line1 + ("GLOBAL ANOMALY DETECTED: High Event Frequency").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(GLOBALANOM)).ljust(70,' ');
				line6 = line6 + ("Upper limit: " + str(data.high)).ljust(70,' ');
				link.addLog(data.host,item.epoch,GLOBALANOM);
				hit = (hit + 1) % 2;
				isHit = True;

			else:
				line1 = line1 + ("GLOBAL ANOMALY DETECTED: Low Event Frequency").ljust(70,' ');
				line2 = line2 + ("Time: " + str(item.time)).ljust(70,' ');
				line3 = line3 + ("Epoch: " + str(item.epoch)).ljust(70,' ');
				line4 = line4 + ("Details: " + str(item.dEvents) + " events since last report").ljust(70,' ');
				line5 = line5 + ("Possible Causes: " + link.getReason(GLOBALANOM)).ljust(70,' ');
				line6 = line6 + ("Lower limit: " + str(data.low)).ljust(70,' ');
				link.addLog(data.host,item.epoch,GLOBALANOM);
				hit = (hit + 1) % 2;
				isHit = True;

		#Print out the data
		if hit == 0 and isHit:
			print(line1);
			print(line2);
			print(line3);
			print(line4);
			print(line5);
			print(line6);
			line1 = "\n";
			line2 = "";
			line3 = "";
			line4 = "";
			line5 = "";
			line6 = "";

	if hit == 1:
		print(line1);
		print(line2);
		print(line3);
		print(line4);
		print(line5);
		print(line6);

	#Write all new logs to file
	link.writeLogs();

#--------------------------------------------------------------------------------------

#-------------------------------CLEAR SCREEN METHOD------------------------------------
def clearScreen():
	if os.name == "nt":
		os.system("cls");
		os.system("cls");
	else:
		os.system("clear");
		os.system("clear");
#--------------------------------------------------------------------------------------

main();
