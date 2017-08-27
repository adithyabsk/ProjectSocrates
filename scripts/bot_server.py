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
import sqlite3

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
if os.path.isfile("keys.config"):
  with open("keys.config", "r") as keys_file:
    secrets = json.load(keys_file)
else:
  sys.exit('keys.config was not found, please update sample file with keys')
# Model
model_parameters = None
if os.path.isfile("model.config"):
  with open("model.config", "r") as model_file:
    model_parameters = json.load(model_file)
else:
  sys.exit('model.config was not found, please update model config file')

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

# try:
#   print verify_video('y6120QOlsfU')
# except HttpError, e:
#   print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

paypalrestsdk.configure({
  'mode': 'sandbox', #sandbox or live
  'client_id': 'YOUR APPLICATION CLIENT ID',
  'client_secret': 'YOUR APPLICATION CLIENT SECRET' })

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

    # self.votes_db = sqlite3.connect('votes.db')
    # self.votes_cursor = self.votes_db.cursor()
    # 
    # self.mult_db = sqlite3.connect('multipliers.db')
    # self.mult_cursor = self.mult_db.cursor()

  def put_vote(self, video_id, multiplier=None):
    votes_db = sqlite3.connect('votes.db')
    votes_cursor = votes_db.cursor()

    should_update_multiplier = False
    if multiplier: should_update_multiplier = True
    else: multiplier = 1.0

    # First check if key exists
    votes_cursor.execute("SELECT * FROM Votes WHERE video_id = ?", (video_id,))
    data = votes_cursor.fetchall()
    if len(data) == 0:
      print "Beginning to add vote..."
      # Key does not exist
      try:
        print "Key does not exist so creating key...."
        votes_cursor.execute("""INSERT INTO Votes (video_id, votes, multiplier, played) 
        VALUES (?, ?, ?, ?)""", (video_id, 1*multiplier, multiplier, 0,))
        votes_db.commit()
        print "Value was added to "
      except Exception as e:
        print "There was an error 1: " + e.args[0]
      finally:
        votes_db.close()
    else:
      # Key does exist
      try:
        if should_update_multiplier:
          votes_cursor.execute("""UPDATE Votes SET multiplier = multiplier + ? WHERE video_id = ?""", (multiplier, video_id,))
          votes_cursor.execute("""UPDATE Votes SET votes = (votes + 1) * multiplier WHERE video_id = ?""", (video_id,))
        else:
          votes_cursor.execute("""UPDATE Votes SET votes = votes + (1 * multiplier) WHERE video_id = ?""", (video_id,))
        votes_db.commit()
      except Exception as e:
        print "There was an error 2: {}\n".format(e)
      finally:
        votes_db.close()

  def verify_video(self, video_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
      developerKey=YOUTUBE_DEVELOPER_KEY)

    results = youtube.videos().list(
      part="id",
      id=video_id
    ).execute()

    # print json.dumps(results, indent=4)

    return results["items"][0]["id"] if results["items"] else None

  def process_message(self, m):
    # Processing to prevent uncessary calling of YT API
    if len(m) != 11: return None
    else: return self.verify_video(m)

  def add_vote(self, username, video_id, multiplier):
    with open('ledger.txt', 'a') as ledger_file:
      ledger_file.write("{}, {}\n".format(username, video_id))
    
    self.put_vote(video_id, multiplier)

  def get_multiplier(self, video_id):
    mult_db = sqlite3.connect('multipliers.db')
    mult_cursor = mult_db.cursor()

    try:
      mult_cursor.execute('SELECT * FROM Multipliers WHERE used = 0 AND video_id = ?',
    (video_id,))
      multipliers = mult_cursor.fetchall()
      mult_cursor.execute('UPDATE Multipliers SET used = 1 WHERE video_id = ?',
    (video_id,))
      mult_db.commit()
      if len(multipliers) == 0: return None
      else: return sum([x[2] for x in multipliers])
    except Exception as e:
      print "There was an error 3: {}\n".format(e)
      return None
    finally:
      mult_db.close()

  def run(self):
    while True:
      username, message = self.votes.get()
      video_id = self.process_message(message)
      if video_id != None:
        multiplier = self.get_multiplier(video_id)
        self.add_vote(username, "http://www.youtube.com/watch?v="+video_id, multiplier)
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

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise

