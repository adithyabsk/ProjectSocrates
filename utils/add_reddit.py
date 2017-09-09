#!/usr/bin/env python

import sys
import time
import json

# MariaDB API
import pymysql.cursors

# Reddit API
import praw

# Secrets
os.environ["PYTHONDONTWRITEBYTECODE"] = "1" #OSX hotfix
sys.dont_write_bytecode = True
sys.path.insert(0, '../shared')
import secrets
import shared

def add_video(video_id):
	votes_conn = pymysql.connect(host=secrets.DB_HOST,
								 user=secrets.DB_USER,
								 password=secrets.DB_PASS,
								 db=secrets.DB_PROD_ID,
								 charset='utf8mb4',
								 cursorclass=pymysql.cursors.DictCursor)
	try:
		with votes_conn.cursor() as cursor:
			sql = "INSERT INTO `Votes` (`video_id`, `votes`, `multiplier`, `play_date`, `create_date`) VALUES (%s, 1, 1.0, '0000-00-00', %s) ON DUPLICATE KEY UPDATE `votes` = `votes` + 1"
			cursor.execute(sql, (video_id, time.strftime("%Y-%m-%d")))
			votes_conn.commit()
	except Exception as e:
		print "There was an error 1 {}".format(e)

reddit = praw.Reddit(client_id=secrets.REDDIT_CLIENT_ID,
					 client_secret=secrets.REDDIT_CLIENT_SECRET,
					 password=secrets.REDDIT_PASSWORD,
					 user_agent=secrets.REDDIT_USER_AGENT,
					 username=secrets.REDDIT_USERNAME)

def load_subreddit(subreddit):
	count = 1
	for submission in reddit.subreddit(subreddit).top('day'):
		print count
		if(submission.ups < 30): continue
		url = submission.url
		video_id = shared.get_video_id(shared.verify_video(url))
		if video_id:
			print video_id
			add_video(video_id)
			count += 1

def main():
	subreddits = None
	with open("load_videos.config") as videos_file:
		subreddits = json.load(videos_file)["subreddits"]
	if not subreddits:
		sys.exit("Failed to load config file load_videos.config")
	for sub in subreddits:
		load_subreddit(sub)


if __name__ == "__main__":
	main()
