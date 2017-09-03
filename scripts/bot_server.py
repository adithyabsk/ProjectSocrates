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

class VoteTranscriber(threading.Thread):
  CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

  def __init__(self, votes, commands, socket):
    threading.Thread.__init__(self)

    self.votes = votes
    self.commands = commands

    self.socket = socket
    self.socket.connect((TWITCH_HOST, TWITCH_PORT))
    self.socket.send("PASS {}\r\n".format(TWITCH_OAUTH).encode("utf-8"))
    self.socket.send("NICK {}\r\n".format(TWITCH_NICK).encode("utf-8"))
    self.socket.send("JOIN {}\r\n".format(TWITCH_CHAN).encode("utf-8"))

  def chat(self, msg):
    package = u"PRIVMSG #{} :{}\r\n".format(TWITCH_CHAN, msg.encode("utf-8")).encode("utf-8")
    # package1 = u":videovotebot!videovotebot@videovotebot@tmi.twitch.tv PRIVMSG #{} :{}".format(TWITCH_CHAN, msg.encode("utf-8")).encode("utf-8")
    self.socket.send(package)
    print("Tried to print: {}".format(package.decode("utf-8")))

  def set_slow_mode(self, sock, time):
    if time == 0:
      self.chat(sock, "/slowoff")
    else:
      self.chat(sock, "/slow {}".format(time))

  def run(self):
    while True:
      response = self.socket.recv(1024).decode("utf-8")
      if response == "PING :tmi.twitch.tv\r\n":
        self.socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
      else:
        username = re.search(r"\w+", response).group(0) # return the entire match
        message = VoteTranscriber.CHAT_MSG.sub("", response)
        username = "".join(str(username).split())
        message = "".join(str(message).split())
        self.votes.put((username, message))
        print "{} put to queue by {}".format((username, message), self.name)
        time.sleep(1 / TWITCH_RATE)
      try:
        message = self.commands.get_nowait() # Can raise error
        self.chat(message)
        self.commands.task_done()
      except: pass

class VoteProcessor(threading.Thread):
  def __init__(self, votes, commands, socket):
    threading.Thread.__init__(self)
    self.socket = socket
    self.votes = votes
    self.commands = commands
    self.votes_conn = pymysql.connect(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASS,
                                      db=DB_ID,
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)

  def put_vote(self, video_id):
    try:
      with self.votes_conn.cursor() as cursor:
        sql = "INSERT INTO `Votes` (`video_id`, `votes`, `multiplier`, `play_date`, `create_date`) VALUES (%s, 1, 1.0, '0000-00-00', %s) ON DUPLICATE KEY UPDATE `votes` = `votes` + 1"
        cursor.execute(sql, (video_id, time.strftime("%Y-%m-%d")))
      self.votes_conn.commit()
    except Exception as e:
      print "There was an error 1 {}".format(e)

  def verify_video(self, video_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
      developerKey=YOUTUBE_DEVELOPER_KEY)

    results = youtube.videos().list(
      part="id",
      id=video_id
    ).execute()

    return results["items"][0]["id"] if results["items"] else None

  def parse_bot(self, msg):
    parts = msg.split(' ')
    com = parts[0]
    num = 5

    if(len(parts) == 2):
      try:
        num = max(int(parts[1]), 20)
      except:
        pass
    return com, num

  def top_command(self, com, num=5):
    try: num = int(num)
    except ValueError:
      	pass
    if num <=0 or num > 10: num = 5
    dat = []
    sql = "SELECT video_id, votes, multiplier, play_date, (votes * multiplier) AS score FROM Votes WHERE play_date = '0000-00-00' ORDER BY score DESC LIMIT {}".format(str(num))
    with self.votes_conn.cursor() as cursor:
      cursor.execute(sql)
      for row in cursor:
        dat += [(row["video_id"],row["votes"],row["multiplier"])]

    self.printvideos(dat, "Top")

  def random_command(self, com, num):
    dat = []
    try: num = int(num)
    except ValueError:
      	pass
    if num <=0 or num > 10: num = 5
    sql = "SELECT video_id, votes, multiplier, play_date, (votes*multiplier) AS score FROM Votes WHERE play_date='0000-00-00' ORDER BY RAND() LIMIT {}".format(str(num))
    with self.votes_conn.cursor() as cursor:
      cursor.execute(sql)
      for row in cursor:
        dat += [(row["video_id"],row["votes"],row["multiplier"])]

    self.printvideos(dat, "Random")


  def hot_command(self, com, num):
    dat = []
    try: num = int(num)
    except ValueError:
      	pass
    if num <=0 or num > 10: num = 5
    sql = "SELECT video_id, votes, multiplier, play_date, create_date, (LOG(votes) + (TO_SECONDS(NOW()) - TO_SECONDS(create_date))/45000) AS score FROM Votes WHERE play_date='0000-00-00' ORDER BY score DESC LIMIT {}".format(str(num))
    with self.votes_conn.cursor() as cursor:
      cursor.execute(sql)
      for row in cursor:
        dat += [(row["video_id"],row["votes"],row["multiplier"])]

    self.printvideos(dat, "Hot")

  def printvideos(self, dat, t):
    linlen = 40
    sp = u" "
    nb = u" "
    rt = u"\r\n"
    header = "{} Videos ({})".format(t, len(dat))
    body = ""    

    for vid in dat:
      line = "[{}]".format(vid[0])
      line = line + sp*(linlen-len(line))
      body += line
      line = "This is a test title a aha aha"
      line = line.replace(" ", rt) +  sp*(len(line) % linlen)
      body += line
      line = "+{}  {}x".format(vid[1], vid[2])
      line = line.replace(" ", rt) + sp*(len(line) - linlen)
      body += line
      body += sp*linlen + " "

    print(header + " " + body)

      #self.commands.put(msg)

  def process_message(self, m):
    # Processing to prevent uncessary calling of YT API

    #Bot Commands
    if(m[0] == "!"):
      message = m[1:]
      if(message.lower() == "top"):
        self.top_command(*self.parse_bot(message))
      if(message.lower() == "random"):
        self.random_command(*self.arse_bot(message))
      if(message.lower() == "hot"):
        self.hot_command(*self.parse_bot(message))
      return None

    if len(m) != 11: return None
    else: return self.verify_video(m)
 
  def add_vote(self, username, video_id):
    try:
      with self.votes_conn.cursor() as cursor:
        sql = "INSERT INTO `Ledger` (`username`, `video_id`, `timestamp`) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, video_id, time.strftime("%Y-%m-%d %H:%M:%S")))
    
      self.votes_conn.commit()
    except Exception as e:
      print "There was an error 2 {}".format(e) 
    
    self.put_vote(video_id)

  def run(self):
    while True:
      try:
        username, message = self.votes.get_nowait() # Can raise error
        video_id = self.process_message(message)
        if video_id != None:
          self.add_vote(username, video_id)
          print "{} popped from queue and added to ledger by {}".format((username, message), self.name)
        else: print "{} popped from queue by {}".format((username, message), self.name)
        self.votes.task_done()
      except: pass

def main():
  s = socket.socket()
  votes = Queue()
  commands = Queue()
  t1 = VoteTranscriber(votes, commands, s)
  t2 = VoteProcessor(votes, commands,  s)
  t1.daemon = True
  t2.daemon = True
  t1.start()
  t2.start()
  while True:
      time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise
