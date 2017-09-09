#!/usr/bin/env python

import praw
import re
import json
import sys
import os
import time
import requests

import isodate

# MariaDB API
import pymysql.cursors

# Youtube API
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

# DB


secrets = None
with open("../videovote.pub",'r') as rsa:
	botkeys = requests.post("https://videovote.org/cgi-bin/keys.py",data={"auth":rsa.read(),"file":"bot_keys.config"})
	print(botkeys.text)
	secrets = json.loads(botkeys.text)



# YT
YOUTUBE_DEVELOPER_KEY = secrets["YOUTUBE_DEVELOPER_KEY"]
YOUTUBE_API_SERVICE_NAME = secrets["YOUTUBE_API_SERVICE_NAME"]
YOUTUBE_API_VERSION = secrets["YOUTUBE_API_VERSION"]

# Reddit
REDDIT_CLIENT_ID = secrets["REDDIT_CLIENT_ID"]
REDDIT_CLIENT_SECRET = secrets["REDDIT_CLIENT_SECRET"]
REDDIT_PASSWORD = secrets["REDDIT_PASSWORD"]
REDDIT_USER_AGENT = secrets["REDDIT_USER_AGENT"]
REDDIT_USERNAME= secrets["REDDIT_USERNAME"]


