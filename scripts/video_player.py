#!/usr/bin/env python

# Python imports
import time
import sqlite3
import os
import json
import pymysql.cursors

import sys
import select

# Reddit API
import praw

# Web Browser Controller
import selenium.webdriver as webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys


# Get Keys Here
db_keys = None
if os.path.isfile("../keys/db_keys.config"):
  with open("../keys/db_keys.config", "r") as db_file:
    db_keys = json.load(db_file)
else:
  sys.exit("../keys/db_keys.config was not found, please update model config file")

DB_HOST = db_keys["DB_HOST"]
DB_USER = db_keys["DB_USER"]
DB_PASS = db_keys["DB_PASS"]
DB_ID = db_keys["DB_ID"]

votes_conn = pymysql.connect(host=DB_HOST,
                             user=DB_USER,
                             password=DB_PASS,
                             db=DB_ID,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

def create_browser():
    return webdriver.Chrome() # Change browser here

def play_new_video(browser, link):
    browser.get("{}".format(link))
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
            browser.find_element_bt_class_name('close-button').click()
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
	print(cursor)
        return cursor.fetchone()["video_id"]
    except Exception as e:
      print "There was an error {}".format(e)

def set_video_as_played(video_id):
    try:
      with votes_conn.cursor() as cursor:
        sql = "UPDATE `Votes` SET `play_date` = %s WHERE `video_id` = %s"
        cursor.execute(sql, (time.strftime("%Y-%m-%d"), video_id))
      votes_conn.commit()
    except Exception as e:
      print "There was an error {}".format(e)

def run():
    browser = create_browser()
    browser.maximize_window()
    while True:
        video_id = None
        try:
            video_id = get_top_unplayed_video()
        except:
            pass
        link = "https://www.youtube.com/watch?v={}".format(video_id)
        play_new_video(browser,link)
        set_video_as_played(video_id)


def main():
    run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit = 1
        raise
