#!/usr/bin/env python


from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

import json
import sys
import os.path

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
secrets = None
if os.path.isfile("keys.config"):
	with open("keys.config", "r") as keys_file:
		secrets = json.load(keys_file)
else:
	sys.exit('keys.config was not found, please update sample file with keys')

# Secrets were successfully loaded
DEVELOPER_KEY = secrets["DEVELOPER_KEY"]
YOUTUBE_API_SERVICE_NAME = secrets["YOUTUBE_API_SERVICE_NAME"]
YOUTUBE_API_VERSION = secrets["YOUTUBE_API_VERSION"]

def verify_video(video_id):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  # Call the search.list method to retrieve results matching the specified
  # query term.
  results = youtube.videos().list(
    part="id",
    id=video_id
  ).execute()

  print json.dumps(results, indent=4)

  return results["items"][0]["id"] if results["items"] else None

# try:
#   print verify_video('y6120QOlsfU')
# except HttpError, e:
#   print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

