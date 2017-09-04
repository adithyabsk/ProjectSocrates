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


PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
#PP_URL = "https://www.paypal.com/cgi-bin/webscr"

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


def write_db(f):


    prod = f["option_selection1"].value
    vidid = f["option_selection2"].value

    

    done = 0

    mod = 0

    if(prod == "50% Power-Up"):
        mod = 0.5
    if(prod == "100% Power-Up"):
        mod = 1
    if(prod == "50% Power-Drain"):
        mod = -0.5

    today = datetime.date.today().strftime("%Y-%m-%d")

    db = MySQLdb.connect(host="localhost", user="root", passwd="Bagwell107",db="test")

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


    
