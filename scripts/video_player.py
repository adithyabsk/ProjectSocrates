#!/usr/bin/env python

# Python imports
import os
import time
import json
import select

# Reddit API
import praw

# Web Browser Controller
import selenium.webdriver as webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys

# Twitch Api
from twitch import TwitchClient

# PyMySQL
import pymysql.cursors

# Secrets
sys.path.insert(0, '../shared')
import secrets

TWITCH_ID = 170727258 # Twitch Channel ID
NO_VOTES_URL = "https://videovote.org/none.html" # No Vote URL

votes_conn = pymysql.connect(host=secrets.DB_HOST,
							 user=secrets.DB_USER,
							 password=secrets.DB_PASS,
							 db=secrets.DB_PROD_ID,
							 charset='utf8mb4',
							 cursorclass=pymysql.cursors.DictCursor)

client = TwitchClient(client_id=secrets.TWITCH_CLIENT_ID)

def create_browser():
	return webdriver.Chrome() # Change browser here

def play_new_video(browser, link):
	browser.get(link)
	player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
	# driver.find_element_by_xpath('/html/body').send_keys(Keys.F11)
	time.sleep(5)
	actions = webdriver.ActionChains(browser)
	actions.send_keys('f')
	actions.perform()
	while player_status:
		try:
			browser.find_element_by_class_name('videoAdUiSkipButton').click()
		except:
			pass
		try:
			browser.find_element_by_class_name('close-button').click()
		except:
			pass

		skip = False
		while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
			line = sys.stdin.readline()
			if line:
				print("Line " + str(line))
				if("skip" in line):
					print("Skipping")
					skip = True
		if skip: break

		time.sleep(1)
		player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
	actions.send_keys(u'\ue00c')

def get_top_unplayed_video():
	try:
	  with votes_conn.cursor() as cursor:
		sql = "SELECT `video_id`, `votes`, `multiplier`, `play_date`, (`multiplier` * `votes`) AS score FROM Votes WHERE `play_date` = '0000-00-00' ORDER BY score DESC LIMIT 1"
		cursor.execute(sql) 
		return cursor.fetchone()["video_id"]
	except Exception as e:
	  print "There was an error {}".format(e)
	  return None

def set_video_as_played(video_id):
	try:
	  with votes_conn.cursor() as cursor:
		sql = "UPDATE `Votes` SET `play_date` = %s WHERE `video_id` = %s"
		cursor.execute(sql, (time.strftime("%Y-%m-%d"), video_id))
	  votes_conn.commit()
	except Exception as e:
	  print "There was an error {}".format(e)

def check_viewers():
	data = client.streams.get_stream_by_user(TWITCH_ID)
	return data['viewers'] if data else None

def run():
	is_showing_none_page = False

	browser = create_browser()
	browser.maximize_window()
	
	while True:
		video_id = None
		viewers = check_viewers()

		if viewers and viewers < 1:
			if not is_showing_none_page:
				is_showing_none_page = True
				browser.get(NO_VOTES_URL)
			time.sleep(5)
			continue
		else:
			is_showing_none_page = False

		try:
			video_id = get_top_unplayed_video()
		except:
			pass

		print "Current video: {} and viewers: {}".format(video_id, viewers)

		if video_id:
			is_showing_none_page = False
			link = "https://www.youtube.com/watch?v={}".format(video_id)
			play_new_video(browser,link)
			set_video_as_played(video_id)
		else:
			if not is_showing_none_page:
				is_showing_none_page = True
				browser.get(NO_VOTES_URL)
			time.sleep(5)

def main():
	run()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		exit = 1
		raise
