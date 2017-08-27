#!/usr/bin/env python

import sqlite3

mult_db = sqlite3.connect('multipliers.db')
mult_cursor = mult_db.cursor()

mult_cursor.execute("""CREATE TABLE Multipliers (
					   id varchar(36) primary key,
					   video_id varchar(11),
					   value real,
					   used integer""")
mult_db.commit()
mult_db.close()

votes_db = sqlite3.connect('votes.db')
votes_cursor = votes_db.cursor()

votes_cursor.execute("""CREATE TABLE Votes (
					   video_id varchar(11) primary key,
					   votes real,
					   multiplier real,
					   played integer""")
votes_db.commit()
votes_db.close()