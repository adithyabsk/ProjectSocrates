#!/usr/bin/env python

# Python imports
import json
import sys
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
if os.path.isfile("bot_keys.config"):
  with open("bot_keys.config", "r") as keys_file:
    secrets = json.load(keys_file)
else:
  sys.exit("bot_keys.config was not found, please update sample file with keys")
# Model
model_parameters = None
if os.path.isfile("model.config"):
  with open("model.config", "r") as model_file:
    model_parameters = json.load(model_file)
else:
  sys.exit("model.config was not found, please update model config file")
# DB
db_keys = None
if os.path.isfile("db_keys.config"):
  with open("db_key.config", "r") as model_file:
    model_parameters = json.load(model_file)
else:
  sys.exit("db_key.config was not found, please update model config file")

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

  def __init__(self, votes, socket):
    threading.Thread.__init__(self)
    self.votes = votes
    self.socket = socket
    self.socket.connect((TWITCH_HOST, TWITCH_PORT))
    self.socket.send("PASS {}\r\n".format(TWITCH_OAUTH).encode("utf-8"))
    self.socket.send("NICK {}\r\n".format(TWITCH_NICK).encode("utf-8"))
    self.socket.send("JOIN {}\r\n".format(TWITCH_CHAN).encode("utf-8"))

  def chat(self, sock, msg):
    """
    Send a chat message to the server.
    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    sock.send("PRIVMSG #{} :{}".format(TWITCH_CHAN, msg))

  def set_slow_mode(self, sock, time):
    """
    Set or unset slowmode
    Keyword arguments:
    sock -- the socket over which to send the message
    time -- the length of time in seconds to set slow mode
    """
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

class VoteProcessor(threading.Thread):
  def __init__(self, votes):
    threading.Thread.__init__(self)
    self.votes = votes
    self.votes_conn = pymysql.connect(host=DB_HOST,
                                      user=DB_USER,
                                      password=DB_PASS,
                                      db=DB_ID,
                                      charset='utf8mb4',
                                      cursorclass=pymysql.cursors.DictCursor)

  def put_vote(self, video_id):
    try:
      with self.votes_conn.cursor() as cursor:
        sql = "INSERT INTO `Votes` (`video_id`, `votes`, `multiplier`, `play_date`, `create_date`) VALUES (%s, %d, %f, %s) ON DUPLICATE KEY UPDATE `votes` = `votes` + 1"
        cursor.execute(sql, (video_id, 1, 1.0, "0000-00-00", time.strftime("%Y-%m-%d")))
      self.votes_conn.commit()
    except Exception e:
      print "There was an error {}".format(e)

  def verify_video(self, video_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
      developerKey=YOUTUBE_DEVELOPER_KEY)

    results = youtube.videos().list(
      part="id",
      id=video_id
    ).execute()

    return results["items"][0]["id"] if results["items"] else None

  def process_message(self, m):
    # Processing to prevent uncessary calling of YT API
    if len(m) != 11: return None
    else: return self.verify_video(m)

  def add_vote(self, username, video_id):
    try:
      with self.votes_conn.cursor() as cursor:
        sql = "INSERT INTO `Ledger` (`username`, `video_id`) VALUES (%s, %s)"
        cursor.execute(sql, (username, video_id, time.strftime("%Y-%m-%d %H:%M:%S")))
      self.votes_conn.commit()
    except Exception e:
      print "There was an error {}".format(e)
    
    self.put_vote(video_id)

  def run(self):
    while True:
      username, message = self.votes.get()
      video_id = self.process_message(message)
      if video_id != None:
        self.add_vote(username, "http://www.youtube.com/watch?v="+video_id)
        print "{} popped from queue and added to ledger by {}".format((username, message), self.name)
      else: print "{} popped from queue by {}".format((username, message), self.name)
      self.votes.task_done()

def main():
  s = socket.socket()
  votes = Queue()
  t1 = VoteTranscriber(votes, s)
  t2 = VoteProcessor(votes)
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

