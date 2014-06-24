#!/usr/bin/python

import time
import yaml
import smtplib
import logging
import requests
import datetime
from email.mime.text import MIMEText
from BeautifulSoup import BeautifulSoup

try:
    stream = file('config.yml', 'r')
except:
    logging.debug('Config file not found!')
    print "Config file not found!"
config = yaml.load(stream)

if config['debug']:
    logging.basicConfig(level=logging.DEBUG, filename=config['debug_file'],
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

# Read previous goals from goalfile
logging.debug('Read goals from goalfile.')
goalfile="goals.txt"
goals= [line.strip() for line in open(goalfile, 'r')]

# Define the rough date and times for the matches to limit the feed polling
matches = [ [ datetime.datetime(2014,  6, 29, 18, 0, 0), 
              datetime.datetime(2014,  6, 29, 22, 0, 0) ],
            [ datetime.datetime(2014,  7,  5, 22, 0, 0), 
              datetime.datetime(2014,  7,  6,  2, 0, 0) ],
            [ datetime.datetime(2014,  7,  9, 22, 0, 0), 
              datetime.datetime(2014,  7, 10,  2, 0, 0) ],
            [ datetime.datetime(2014,  7, 12, 22, 0, 0), 
              datetime.datetime(2014,  7, 13,  2, 0, 0) ],
            [ datetime.datetime(2014,  7, 13, 21, 0, 0), 
              datetime.datetime(2014,  7, 14,  2, 0, 0) ] ]

def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def yo_all(api_token):
    """Yo all subscribers on the given API secret"""
    return requests.post("http://api.justyo.co/yoall/", data={'api_token': api_token})

sleep = 60
while True:
    for match in matches:
        logging.debug('Checking if time is within any of the match times')
        if time_in_range( match[0], match[1], datetime.datetime.now()):
            # Sleep less
            sleep = 10

            # Get list of soccer events from feed and parse it
            logging.debug('It\'s game time! Get list of soccer events from feed and parse it.')
            source=requests.get(config['feed']).text
            parsed=BeautifulSoup(source)
            items=parsed.findAll("item")

            # Filter list of items
            dutch = [ i for i in items if "Goal for Netherlands" in i.description.string
                                        and i.pubdate.string not in goals ]
            for i in dutch:
                # Send Yo
                logging.debug('There\'s a goal! Sending Yo.')
                yo_all(config['api_key'])

                # Add goal to list
                goals.append(i.guid.string)

                # Write goal to file
                logging.debug('Writing goal to file.')
                gfile=open(goalfile, 'a')
                gfile.write(i.pubdate.string + "\n")
                gfile.close

                # Send email
                logging.debug('Sending email.')
                msg = MIMEText(i.pubdate.string + " " + i.description.string)
                msg['Subject'] = "Nederland heeft gescoord!"
                msg['From'] = config['from_email']
                msg['To'] = config['to_email']
                s = smtplib.SMTP('localhost')
                s.sendmail(config['from_email'], config['to_email'], msg.as_string())
                s.quit()
            # Do not evaluate the other matches:
            break
        else:
            sleep = 60
    time.sleep(sleep)
