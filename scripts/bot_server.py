#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python imports
import json
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os.path
import socket
import re
import time
import datetime
import isodate
import threading
from Queue import Queue

# MariaDB API
import pymysql.cursors

# Youtube API
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

# Twitch API
from twitch import TwitchClient

# Paypal API
import paypalrestsdk

# Load Secretes and Model Parameters
# Secrets
secrets = None
if os.path.isfile("../keys/bot_keys.config"):
  with open("../keys/bot_keys.config", "r") as keys_file:
    secrets = json.load(keys_file)
else:
  sys.exit("../keys/bot_keys.config was not found, please update sample file with keys")
# Model
model_parameters = None
if os.path.isfile("../keys/model.config"):
  with open("../keys/model.config", "r") as model_file:
    model_parameters = json.load(model_file)
else:
  sys.exit("../keys/model.config was not found, please update model config file")
# DB
db_keys = None
if os.path.isfile("../keys/db_keys.config"):
  with open("../keys/db_keys.config", "r") as key_file:
    db_keys = json.load(key_file)
else:
  sys.exit("../keys/db_keys.config was not found, please update model config file")

# Set Secrets and Model Parameters
# YT
YOUTUBE_DEVELOPER_KEY = secrets["YOUTUBE_DEVELOPER_KEY"]
YOUTUBE_API_SERVICE_NAME = secrets["YOUTUBE_API_SERVICE_NAME"]
YOUTUBE_API_VERSION = secrets["YOUTUBE_API_VERSION"]
# Twitch
TWITCH_HOST = secrets["TWITCH_HOST"] # the Twitch IRC server
TWITCH_PORT = secrets["TWITCH_PORT"] # always use port 6667!
TWITCH_NICK = secrets["TWITCH_NICK"] # your Twitch username, lowercase
TWITCH_OAUTH = secrets["TWITCH_OAUTH"] # your Twitch OAuth token
TWITCH_CHAN = secrets["TWITCH_CHAN"] # the channel you want to join
TWITCH_RATE = secrets["TWITCH_RATE"] # messages per second you can send
# Model
MAX_COOLDOWN = model_parameters["MAX_COOLDOWN"] # in seconds
MAX_FRAC_VOTES = model_parameters["MAX_FRAC_VOTES"] # proportion
VOTE_PROB = model_parameters["VOTE_PROB"] # probablity of active user vote
DUTY_CYCLE = model_parameters["DUTY_CYCLE"] # in seconds
# DB
DB_HOST = db_keys["DB_HOST"]
DB_USER = db_keys["DB_USER"]
DB_PASS = db_keys["DB_PASS"]
DB_ID = db_keys["DB_ID"]


class TwitchWriter(threading.Thread):
  def __init__(self, response_queue, socket):
    threading.Thread.__init__(self)
    
    self.socket = socket
    self.response_queue = response_queue
  
  def chat(self, msg):
    self.socket.send("PRIVMSG {} :{}\r\n".format(TWITCH_CHAN, msg[:500]).encode("utf-8"))

  def run(self):
    while True:
      # thread is blocked by get() so sleep is not necessary
      msg = self.response_queue.get()
      self.chat(msg)
      self.response_queue.task_done()

class TwitchReader(threading.Thread):
  CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

  def __init__(self, message_queue, socket):
    threading.Thread.__init__(self)

    self.message_queue = message_queue
    self.socket = socket

  def run(self):
    while True:
      response = self.socket.recv(1024).decode("utf-8")
      if response == "PING :tmi.twitch.tv\r\n":
        self.socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
      else:
        username = re.search(r"\w+", response).group(0) # return the entire match
        message = TwitchReader.CHAT_MSG.sub("", response)
        username = "".join(str(username).split())
        message = "".join(str(message).split())
        self.message_queue.put((username, message))
        # print "{} put to queue by {}".format((username, message), self.name)
        time.sleep(1 / TWITCH_RATE)

class MessageProcessor(threading.Thread):
  def __init__(self, message_queue, response_queue, socket):
    threading.Thread.__init__(self)
    
    self.socket = socket
    self.message_queue = message_queue
    self.response_queue = response_queue
    self.votes_conn = pymysql.connect(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASS,
                                      db=DB_ID,
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)
    
    self.last_top = datetime.datetime.min
    self.last_random = datetime.datetime.min
    self.last_hot = datetime.datetime.min

  def top_command(self):
    dat = []
    sql = "SELECT video_id, votes, multiplier, play_date, (votes * multiplier) AS score FROM Votes WHERE play_date = '0000-00-00' ORDER BY score DESC LIMIT 10"
    
    with self.votes_conn.cursor() as cursor:
      cursor.execute(sql)
      for row in cursor:
        dat += [(row["video_id"],row["votes"],row["multiplier"])]

    self.printvideos(dat, "Top")

  def random_command(self):
    dat = []
    sql = "SELECT video_id, votes, multiplier, play_date, (votes*multiplier) AS score FROM Votes WHERE play_date='0000-00-00' ORDER BY RAND() LIMIT 10"
    
    with self.votes_conn.cursor() as cursor:
      cursor.execute(sql)
      for row in cursor:
        dat += [(row["video_id"],row["votes"],row["multiplier"])]

    self.printvideos(dat, "Random")


  def hot_command(self):
    dat = []
    sql = "SELECT video_id, votes, multiplier, play_date, create_date, (LOG(votes) + (TO_SECONDS(NOW()) - TO_SECONDS(create_date))/45000) AS score FROM Votes WHERE play_date='0000-00-00' ORDER BY score DESC LIMIT 10"
    
    with self.votes_conn.cursor() as cursor:
      cursor.execute(sql)
      for row in cursor:
        dat += [(row["video_id"],row["votes"],row["multiplier"])]

    self.printvideos(dat, "Hot")

  def status_command(self, video_id):
    dat = []
    sql = "SELECT * FROM Votes WHERE video_id = %s"
    
    with self.votes_conn.cursor() as cursor:
      cursor.execute(sql, (video_id,))
      row = cursor[0]
      dat += [(row["video_id"],row["votes"],row["multiplier"])]

    self.printvideos(dat, "Status")

  def printvideos(self, dat, t):
    msg = u"Rank_Votes__Mult_{}_Videos".format(t).ljust(40).replace(" ", "_")+u" "
    for i, row in enumerate(dat):
      video_id, votes, multiplier = row
      msg += u"{: <2}____{: <5}_{:.1f}___{}".format(i+1, votes, multiplier, video_id).ljust(40).replace(" ", "_")+u" "
    self.response_queue.put(msg)

  def process_message(self, m):
    if(m[0] == "!"): # Bot Commands
      message = m[1:]
      now = datetime.datetime.now()
      if(message.lower() == "top" and (now - self.last_top).total_seconds() > 30):
        self.last_top = now
        self.top_command()
        print "The top command was run"
      elif(message.lower() == "random" and (now - self.last_random).total_seconds() > 30): 
        self.last_random = now
        self.random_command()
        print "The run command was run"
      elif(message.lower() == "hot" and (now - self.last_hot).total_seconds() > 30): 
        self.last_hot = now
        self.hot_command()
        print "The hot command was run"
      else: return None
      elif(message.lower()[:6] == "status"):
        status_mesg = m.split()
        video_id = None
        if len(status_mesg) != 2: return None
        if len(status_mesg[1]) == 11: video_id = status_mesg[1]
        else:
          id_regex = re.compile(r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
          id_search = id_regex.search(status_mesg[1])
          if id_search and id_search.group(7): video_id = id_search.group(7)
          else: return None
        self.status_command(video_id) # Video id should be of id style
        print "The status command was run for: {}".format(video_id)
      else: return None
    elif len(m) == 11: return self.verify_video(m) # video_id only
    else: # youtube url only
      id_regex = re.compile(r'^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#\&\?]*).*')
      id_search = id_regex.search(m)
      if id_search and id_search.group(7): return self.verify_video(id_search.group(7)[:11])
      else: return None

  def verify_video(self, video_id):
    # 1. Check if video in db
    # 2. If not, check existance
    # 3. If so, check video length
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

  def add_ledger(self, username, video_id):
    try:
      with self.votes_conn.cursor() as cursor:
        sql = "INSERT INTO `Ledger` (`username`, `video_id`, `timestamp`) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, video_id, time.strftime("%Y-%m-%d %H:%M:%S")))
    
      self.votes_conn.commit()
    except Exception as e:
      print "There was an error 2 {}".format(e) 
    
  def add_vote(self, video_id):
    try:
      with self.votes_conn.cursor() as cursor:
        sql = "INSERT INTO `Votes` (`video_id`, `votes`, `multiplier`, `play_date`, `create_date`) VALUES (%s, 1, 1.0, '0000-00-00', %s) ON DUPLICATE KEY UPDATE `votes` = `votes` + 1"
        cursor.execute(sql, (video_id, time.strftime("%Y-%m-%d")))
      self.votes_conn.commit()
    except Exception as e:
      print "There was an error 1 {}".format(e)

  def run(self):
    while True:
      username, message = self.message_queue.get()
      video_id = self.process_message(message)
      if video_id != None:
        self.add_ledger(username, video_id)
        self.add_vote(video_id)
        print "{} added a vote for {}".format(username, video_id)
        # print "{} popped from queue and added to ledger by {}".format((username, message), self.name)
      else: print "Processed {} from {}".format(message, username, self.name)
      self.message_queue.task_done()

def main():
  s = socket.socket()
  s.connect((TWITCH_HOST, TWITCH_PORT))
  s.send("PASS {}\r\n".format(TWITCH_OAUTH).encode("utf-8"))
  s.send("NICK {}\r\n".format(TWITCH_NICK).encode("utf-8"))
  s.send("JOIN {}\r\n".format(TWITCH_CHAN).encode("utf-8"))
  
  response_queue = Queue()
  message_queue = Queue()
  
  t1 = TwitchWriter(response_queue, s)
  t2 = TwitchReader(message_queue, s)
  t3 = MessageProcessor(message_queue, response_queue, s)  

  t1.daemon = True
  t2.daemon = True
  t3.daemon = True
  
  t1.start()
  t2.start()
  t3.start()

  while True:
      time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise
