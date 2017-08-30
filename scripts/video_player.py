#!/usr/bin/env python

# Python imports
import time
import sqlite3

# Reddit API
import praw

# Web Browser Controller
import selenium.webdriver as webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys


# Get Keys Here
db_keys = None
if os.path.isfile("db_keys.config"):
  with open("db_key.config", "r") as model_file:
    model_parameters = json.load(model_file)
else:
  sys.exit("db_key.config was not found, please update model config file")

DB_HOST = secrets["DB_HOST"]
DB_USER = secrets["DB_USER"]
DB_PASS = secrets["DB_PASS"]
DB_ID = secrets["DB_ID"]

votes = votes
votes_conn = pymysql.connect(host=DB_HOST,
                             user=DB_USER,
                             password=DB_PASS,
                             db=DB_ID,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

def create_browser():
    return webdriver.Firefox() # Change browser here

def play_new_video(browser, link):
    browser.get("{}".format(link))
    player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
    # driver.find_element_by_xpath('/html/body').send_keys(Keys.F11)
    browser.maximize_window()
    while player_status:
        time.sleep(1)
        player_status = browser.execute_script("return document.getElementById('movie_player').getPlayerState()")
    browser.find_element_by_xpath('/html/body').send_keys(Keys.ESCAPE)

def get_top_unplayed_video():
    try:
      with votes_conn.cursor() as cursor:
        sql = "SELECT `video_id`, `votes`, `multiplier`, `play_date` (`multiplier` * `votes`) AS score WHERE `play_date` = "0000-00-00" ORDER BY score LIMIT 1"
        cursor.execute(sql)
        return cursor[0]["video_id"]
    except Exception e:
      print "There was an error {}".format(e)

def set_video_as_played(video_id):
    try:
      with votes_conn.cursor() as cursor:
        sql = "UPDATE `Votes` SET play_date = %s WHERE `video_id` = %s"
        cursor.execute(sql, (time.strftime("%Y-%m-%d"), video_id))
      votes_conn.commit()
    except Exception e:
      print "There was an error {}".format(e)

def run():
    browser = create_browser()
    while True:
        video_id = None
        try:
            video_id = get_top_unplayed_video()
        except:

        link = "www.youtube.com/watch?v={}".format(video_id)
        play_new_video(link)
        set_video_as_played(video_id)


def main():
    run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit = 1
        raise