#!/usr/bin/env python

import os
import sys
import cgi
import time
import MySQLdb
import urllib2
import datetime
from urllib import urlencode

# Secrets and Shared
os.environ["PYTHONDONTWRITEBYTECODE"] = "1" #OSX hotfix
sys.dont_write_bytecode = True
sys.path.insert(0, '../shared')
import secrets
import shared

#PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
PP_URL = "https://www.paypal.com/cgi-bin/webscr"

def confirm_paypal(f):
	newparams = {}
	for key in f.keys():
		newparams[key] = f[key].value

	newparams["cmd"] = "_notify-validate"
	params=urlencode(newparams)

	req = urllib2.Request(PP_URL)
	req.add_header("Content-type", "application/x-www-form-urlencoded")
	fo = urllib2.urlopen(PP_URL, params)
	ret = fo.read()
	if ret == "VERIFIED":
		print "Status: 200 Ok\n"
	else:
		sys.exit(0)

	return ret

def write_db(f):
	prod = f["option_selection1"].value
	vidid = f["option_selection2"].value

	vidid = shared.verify_video(shared.get_video_id(vidid))
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

	db = MySQLdb.connect(host=secrets.DB_HOST, 
						 user=secrets.DB_USER, 
						 passwd=secrets.DB_PASS, 
						 db=secrets.DB_PROD_ID)

	query = 'INSERT INTO Votes (video_id,votes,multiplier,play_date,create_date) VALUES("%s",0,%d,0000-00-00,"%s") ON DUPLICATE KEY UPDATE multiplier=multiplier+%d;' % (db.escape_string(vidid),mod,today,mod)

	cursor = db.cursor()
	cursor.execute(query)

	db.commit()
	cursor.close()
	db.close()

f = cgi.FieldStorage()
a = confirm_paypal(f)

if not f['payment_status'].value == "Completed":
	sys.exit(0)
else:
	 pass

write_db(f)


	
