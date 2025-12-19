import requests
from hashlib import sha1
import hmac
import json
import csv
import pandas as pd
import os
import time
import sys
import random
from tqdm import tqdm
import ast

# total = 100 means the bar represents 100%
pbar = tqdm(total=500, desc = "Progress" )

progress = 0

increment = 1

TWO_HOURS = 2 * 60 * 60

DEV_ID = None
KEY = None  # replace with your PTV key

def getUrl(endpoint):
    # Determine whether to add '?' or '&'
    sep = '&' if '?' in endpoint else '?'
    # Build the raw string for signature
    raw = f"{endpoint}{sep}devid={DEV_ID}"
    # Generate HMAC-SHA1 signature and convert to uppercase hex
    hashed = hmac.new(KEY.encode(), raw.encode(), sha1)
    signature = hashed.hexdigest().upper()
    # Build final URL
    return f"https://timetableapi.ptv.vic.gov.au{raw}&signature={signature}"

def call(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


filename = "Data_from_script/processed.json"

if os.path.exists(filename):
    with open(filename) as f:
        processed_combs = {tuple(x[0]):x[1] for x in json.load(f)}

else:
    processed_combs = dict()

route_list = []
all_stop_route_list = []

""" The following code retrieves all routes and route_tye combinations."""

#Retrieving data for all routes.
url = getUrl("/v3/routes")
allroutes = call(url)

for route in allroutes["routes"]:
     route_id = route["route_id"]
     route_type = route["route_type"]
     route_list.append((route_type, route_id))

filtered_routes = [t for t in route_list if t[0] == 2]

""" The following code uses the combinations to get all the stops."""

url_list = []

for route_combs in filtered_routes:

    url = getUrl("/v3/stops/route/"+str(route_combs[1])+"/route_type/"+str(route_combs[0]))
    allstops = call(url)

    for stop in allstops["stops"]:
        stop_id = stop["stop_id"]
        url_list.append((route_combs[0], stop_id))

print(len(url_list))
            
remaining = [item for item in url_list if item not in processed_combs]

random_sample = random.sample(remaining, min(500, len(remaining)))

"""Calls the final link used to get the data."""

if os.path.exists("num_finished.txt"):
    with open("num_finished.txt", "r") as file:

        s = file.read().strip()
        lst = ast.literal_eval(s)
        done_combs = lst[0]
        remaining_combs = lst[1]

else:
    done_combs = 100
    remaining_combs = len(url_list) - done_combs
    
     
for item in random_sample:

    # Final Url to retrieve departures for particular route, stop and transport type.
    url = getUrl("/v3/departures/route_type/"+str(item[0])+"/stop/"+str(item[1]))
    datafinal = call(url)

    departures = datafinal.get('departures', [])

    done_combs +=1
    remaining_combs -=1

    with open("num_finished.txt", "w") as file:
        file.write(str([done_combs, remaining_combs]))

    if all(dictionary.get("estimated_departure_utc") == None for dictionary in departures ):
        continue

    if departures == []:
     continue

    progress += increment

    pbar.update(increment)

    processed_combs[item] = time.time()

    with open(filename, 'w') as f:
        json.dump([[list(k), v] for k,v in processed_combs.items()], f)

    df = open('Data_from_script/output.csv', 'a')

    cw = csv.writer(df)

    c = 0

    if os.path.isfile("Data_from_script/output.csv") and os.path.getsize("Data_from_script/output.csv") > 0:
        
        c=1 

    for item in departures:

        if c == 0 : 
            h  = item.keys()
            cw.writerow(h)
            c +=1
        
        cw.writerow(item.values())

    df.close()

    time.sleep(3)

pbar.close()  