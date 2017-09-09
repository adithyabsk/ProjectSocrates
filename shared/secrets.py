#!/usr/bin/env python

import os
import sys
import json
import requests

keys = None
if os.path.isfile("../videovote.pub"):
	with open("../videovote.pub",'r') as rsa:
		botkeys = requests.post("https://videovote.org/cgi-bin/keys.py",data={"auth":rsa.read(),"file":"keys.config"})
		if(botkeys.status_code != 200):
			sys.exit("Unable to authenticate")
		keys = json.loads(botkeys.text)
else:
	sys.exit("Unable to find ../videovote.pub")

# YT
YOUTUBE_DEVELOPER_KEY = keys["YOUTUBE_DEVELOPER_KEY"]
YOUTUBE_API_SERVICE_NAME = keys["YOUTUBE_API_SERVICE_NAME"]
YOUTUBE_API_VERSION = keys["YOUTUBE_API_VERSION"]

# Twitch
TWITCH_HOST = keys["TWITCH_HOST"]
TWITCH_PORT = keys["TWITCH_PORT"]
TWITCH_NICK = keys["TWITCH_NICK"]
TWITCH_OAUTH = keys["TWITCH_OAUTH"]
TWITCH_CHAN = keys["TWITCH_CHAN"]
TWITCH_RATE = keys["TWITCH_RATE"]

# Twitch App
TWITCH_CLIENT_ID = keys["TWITCH_APP"]["CLIENT_ID"]
TWITCH_CLIENT_SECRET = keys["TWITCH_APP"]["CLIENT_SECRET"]

# Reddit
REDDIT_CLIENT_ID = keys["REDDIT_CLIENT_ID"]
REDDIT_CLIENT_SECRET = keys["REDDIT_CLIENT_SECRET"]
REDDIT_PASSWORD = keys["REDDIT_PASSWORD"]
REDDIT_USER_AGENT = keys["REDDIT_USER_AGENT"]
REDDIT_USERNAME= keys["REDDIT_USERNAME"]

# DB
DB_HOST = keys["DB_HOST"]
DB_USER = keys["DB_USER"]
DB_PASS = keys["DB_PASS"]
DB_PROD_ID = keys["DB_PROD_ID"]
DB_TEST_ID = keys["DB_TEST_ID"]

if __name__ == '__main__':
	global_vars = {k: v for k, v in dict(globals()).iteritems() if k.isupper()}
	print "Keys\n----"
	length = max(map(len, global_vars.keys()))
	for k, v in sorted(global_vars.items()):
		print "{0:<{width}}  {1:}".format(k, v, width=length)
