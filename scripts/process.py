#!/usr/bin/env python

import cgi
import time
import MySQLdb
from sys import exc_info
from string import split
from string import strip
from sys import exit
from urllib import urlencode
import urllib2
import datetime

import re
import isodate

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

#PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
PP_URL = "https://www.paypal.com/cgi-bin/webscr"

def confirm_paypal(f):
    
    newparams={}
    for key in f.keys():
        newparams[key]=f[key].value

    newparams["cmd"]="_notify-validate"
    params=urlencode(newparams)

    req = urllib2.Request(PP_URL)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    fo = urllib2.urlopen(PP_URL, params)
    ret = fo.read()
    if ret == "VERIFIED":
        print "Status: 200 Ok\n"
    else:
        exit(0)

    return ret


def verify_video(video_id):
    # 1. Check if video in db
    # 2. If not, check existance
    # 3. If so, check video length
    youtube = build("youtube", "v3", developerKey="AIzaSyAktJ5_6rO76r9rfEM6JGpdbeH2lKeo2dQ")

    results = youtube.videos().list(
        part="id,contentDetails",
        id=video_id
    ).execute()
    
    if results["items"]:
        durationString = results["items"][0]["contentDetails"]["duration"]
        duration = isodate.parse_duration(durationString)
        if duration.total_seconds() <= 600: 
          return video_id
        else: return None
    else: return None



def write_db(f):


    prod = f["option_selection1"].value
    vidid = f["option_selection2"].value

    if len(vidid) == 11: vidid = verify_video(vidid)
    else:
        id_regex = re.compile(r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
        id_search = id_regex.search(vidid)
        if id_search and id_search.group(7): vidid = verify_video(id_search.group(7)[:11])
        else: return
    
    if not vidid: return

    done = 0

    mod = 0

    if(prod == "50% Power-Up"):
        mod = 0.5
    if(prod == "100% Power-Up"):
        mod = 1
    if(prod == "50% Power-Drain"):
        mod = -0.5

    today = datetime.date.today().strftime("%Y-%m-%d")

    db = MySQLdb.connect(host="localhost", user="root", passwd="Bagwell107",db="prod")

    query = 'INSERT INTO Votes (video_id,votes,multiplier,play_date,create_date) VALUES("%s",0,%d,0000-00-00,"%s") ON DUPLICATE KEY UPDATE multiplier=multiplier+%d;' % (db.escape_string(vidid),mod,today,mod)


    cursor = db.cursor()
    cursor.execute(query)

    db.commit()
    cursor.close()
    db.close()



f = cgi.FieldStorage()
a = confirm_paypal(f)


if not f['payment_status'].value == "Completed":
     exit(0)
else:
     pass

write_db(f)


    
