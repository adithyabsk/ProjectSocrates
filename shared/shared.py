#!/usr/bin/env python

# python imports
import os
import sys
os.environ["PYTHONDONTWRITEBYTECODE"] = "1" #OSX hotfix
sys.dont_write_bytecode = True
import re

# Isodate
import isodate

# Youtube API
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

# Secrets
os.environ["PYTHONDONTWRITEBYTECODE"] = "1" #OSX hotfix
sys.dont_write_bytecode = True
import secrets # secrets is in this directory


def verify_video(video_id):
	if not video_id: return None
	youtube = build(secrets.YOUTUBE_API_SERVICE_NAME, secrets.YOUTUBE_API_VERSION,
					developerKey=secrets.YOUTUBE_DEVELOPER_KEY)

	results = youtube.videos().list(
		part="id,contentDetails",
		id=video_id
	).execute()
	
	if results["items"]:
		contentDetails = results["items"][0]["contentDetails"]
		durationString = contentDetails["duration"]
		if "contentRating" in contentDetails: return None
		duration = isodate.parse_duration(durationString)
		if duration.total_seconds() <= 600:
			return video_id
		else: return None
	else: return None

def get_video_id(msg):
	if not msg: return None
	if len(msg) == 11: return msg
	# url or id itself
	id_regex = re.compile(r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
	id_search = id_regex.search(msg)
	if id_search and id_search.group(7): return id_search.group(7)[:11]
	else: return None
