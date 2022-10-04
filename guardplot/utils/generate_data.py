from datetime import datetime, timedelta
import numpy
import random
import configparser
from os import path, makedirs
import json

home_dir = path.dirname(path.dirname(path.abspath(__file__)))
config = configparser.ConfigParser()
config.read(path.join(home_dir,"config.ini"))
DATAPATH = path.join(home_dir,config.get("database","import"))

hosts = []
host_base = "192.168.0."
for i in range(100,130):
    hosts.append(f"{host_base}{i}")

start_date = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=90)
cur_date = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)

print(f"Generating test data into '{DATAPATH}'")

while start_date <= cur_date:
    
    temp_date = f"{start_date:%Y-%m-%d}"
    idx = 0
    for host in hosts:

        if not path.exists(f"{DATAPATH}/{start_date:%Y-%m-%d}"):
            makedirs(f"{DATAPATH}/{start_date:%Y-%m-%d}")

        with open(f"{DATAPATH}/{start_date:%Y-%m-%d}/logs_{idx}.json","w") as file:
            json_data = []
            mean = random.randint(100,600)
            std_dev = random.randint(50,mean//2)
            events = list(map(int,numpy.random.normal(mean, std_dev, 24*4)))
            event_idx = 0
            while f"{start_date:%Y-%m-%d}" == temp_date:

                data = {
                    "host":host,
                    "events":events[event_idx],
                    "date":f"{start_date:%Y-%m-%d}",
                    "epoch":int(start_date.timestamp())
                }

                json_data.append(data)

                event_idx += 1
                start_date = start_date + timedelta(minutes=15)
            file.write(json.dumps(json_data))

            
        start_date = start_date - timedelta(days=1)
        idx += 1

    start_date = start_date + timedelta(days=1)

print("Example data generated")



