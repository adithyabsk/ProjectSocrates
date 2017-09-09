#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Set Default encoding
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# Python imports
import json
import os.path
import socket
import re
import time
import datetime
import threading
from Queue import Queue

# MariaDB API
import pymysql.cursors

# Secrets and Shared
os.environ["PYTHONDONTWRITEBYTECODE"] = "1" #OSX hotfix
sys.dont_write_bytecode = True
sys.path.insert(0, '../shared')
import secrets
import shared


class TwitchWriter(threading.Thread):
	def __init__(self, response_queue, socket):
		threading.Thread.__init__(self)
		
		self.socket = socket
		self.response_queue = response_queue
	
	def chat(self, msg):
		self.socket.send("PRIVMSG {} :{}\r\n".format(secrets.TWITCH_CHAN, msg[:500]).encode("utf-8"))

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
				username = re.search(r"\w+", response).group(0)
				message = TwitchReader.CHAT_MSG.sub("", response)
				username = "".join(str(username).split())
				message = "".join(str(message).split())

				self.message_queue.put((username, message))
				time.sleep(1 / secrets.TWITCH_RATE)

class MessageProcessor(threading.Thread):
	def __init__(self, message_queue, response_queue, socket):
		threading.Thread.__init__(self)
		
		self.socket = socket
		self.message_queue = message_queue
		self.response_queue = response_queue
		self.votes_conn = pymysql.connect(host=secrets.DB_HOST,
										  user=secrets.DB_USER,
										  password=secrets.DB_PASS,
										  db=secrets.DB_PROD_ID,
										  charset='utf8mb4',
										  cursorclass=pymysql.cursors.DictCursor)
		
		self.last_top = datetime.datetime.min
		self.last_random = datetime.datetime.min
		self.last_hot = datetime.datetime.min

	def get_data(self, sql, *args):
		data = []
		with self.votes_conn.cursor() as cursor:
			cursor.execute(sql, args)
			for row in cursor:
				data += [(row["video_id"],row["votes"],row["multiplier"])]
		return data

	def top_command(self):
		sql = "SELECT video_id, votes, multiplier, play_date, (votes * multiplier) AS score FROM Votes WHERE play_date = '0000-00-00' ORDER BY score DESC LIMIT 10"
		data = self.get_data(sql)
		if data: self.print_videos(data, "Top")

	def random_command(self):
		sql = "SELECT video_id, votes, multiplier, play_date, (votes*multiplier) AS score FROM Votes WHERE play_date='0000-00-00' ORDER BY RAND() LIMIT 10"
		data = self.get_data(sql)
		if data: self.print_videos(data, "Random")

	def hot_command(self):
		sql = "SELECT video_id, votes, multiplier, play_date, create_date, (LOG(votes) + (TO_SECONDS(NOW()) - TO_SECONDS(create_date))/45000) AS score FROM Votes WHERE play_date='0000-00-00' ORDER BY score DESC LIMIT 10"
		data = self.get_data(sql)
		if data: self.print_videos(data, "Hot")

	def status_command(self, video_id):
		sql = "SELECT * FROM Votes WHERE video_id = %s"
		data = self.get_data(sql, video_id)
		if data: self.print_videos(data, "Status")

	def print_videos(self, data, t):
		msg = u"Rank_Votes__Mult_{}_Videos".format(t).ljust(40).replace(" ", "_")+u" "
		for i, row in enumerate(data):
			video_id, votes, multiplier = row
			rank = i+1 if t != "Status" else "NA"
			msg += u"{: <2}____{: <5}_{:.1f}___{}".format(rank, votes, multiplier, video_id).ljust(40).replace(" ", "_")+u" "
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
			elif(message.lower()[:6] == "status"):
				status_msg = message[6:]
				video_id = shared.get_video_id(status_msg)
				if not video_id: return None
				self.status_command(video_id) # Video id should be of id style
				print "The status command was run for: {}".format(video_id)
			return None
		else:
			return shared.verify_video(shared.get_video_id(m))

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
	s.connect((secrets.TWITCH_HOST, secrets.TWITCH_PORT))
	s.send("PASS {}\r\n".format(secrets.TWITCH_OAUTH).encode("utf-8"))
	s.send("NICK {}\r\n".format(secrets.TWITCH_NICK).encode("utf-8"))
	s.send("JOIN {}\r\n".format(secrets.TWITCH_CHAN).encode("utf-8"))
	
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