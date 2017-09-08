#!/usr/bin/env python

import praw
import re
import json
import sys
import os
import time

import isodate

# MariaDB API
import pymysql.cursors

# Youtube API
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

# DB
db_keys = None
if os.path.isfile("../keys/db_keys.config"):
	with open("../keys/db_keys.config", "r") as key_file:
		db_keys = json.load(key_file)
else:
	sys.exit("db_keys.config was not found, please update model config file")

# Secrets
secrets = None
if os.path.isfile("../keys/bot_keys.config"):
	with open("../keys/bot_keys.config", "r") as keys_file:
		secrets = json.load(keys_file)
else:
	sys.exit("../keys/bot_keys.config was not found, please update sample file with keys")

# DB
DB_HOST = db_keys["DB_HOST"]
DB_USER = db_keys["DB_USER"]
DB_PASS = db_keys["DB_PASS"]
DB_ID = db_keys["DB_ID"]

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


def verify_video(video_id):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=YOUTUBE_DEVELOPER_KEY)

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

def add_video(video_id):
	votes_conn = pymysql.connect(host=DB_HOST,
								 user=DB_USER,
								 password=DB_PASS,
								 db=DB_ID,
								 charset='utf8mb4',
								 cursorclass=pymysql.cursors.DictCursor)
	try:
		with votes_conn.cursor() as cursor:
			sql = "INSERT INTO `Votes` (`video_id`, `votes`, `multiplier`, `play_date`, `create_date`) VALUES (%s, 1, 1.0, '0000-00-00', %s) ON DUPLICATE KEY UPDATE `votes` = `votes` + 1"
			cursor.execute(sql, (video_id, time.strftime("%Y-%m-%d")))
			votes_conn.commit()
	except Exception as e:
		print "There was an error 1 {}".format(e)

subreddit = 'ContagiousLaughter'

reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
					 client_secret=REDDIT_CLIENT_SECRET,
					 password=REDDIT_PASSWORD,
					 user_agent=REDDIT_USER_AGENT,
					 username=REDDIT_USERNAME)

count = 0

def load_subreddit(subreddit):
	count = 0
	for submission in reddit.subreddit(subreddit).top('day'):
		print count
		if(submission.ups < 30): continue
		url = submission.url

		video_id = None
		id_regex = re.compile(r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
		id_search = id_regex.search(url)
		if id_search and id_search.group(7): video_id = verify_video(id_search.group(7)[:11])
		else: video_id = None

		if video_id:
			print video_id
			add_video(video_id)
			count += 1


def main():
	subreddits = None
	with open("load_videos.config") as videos_file:
		subreddits = json.load(videos_file)["subreddits"]
	if not subreddits:
		print("Failed to load config file load_videos.config")
		quit()
	for sub in subreddits:
		load_subreddit(sub)


if __name__ == "__main__":
	main()
