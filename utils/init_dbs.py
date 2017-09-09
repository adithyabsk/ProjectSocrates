#!/usr/bin/env python

# python imports
import os
import sys

# MariaDB API
import pymysql.cursors

# Secrets and Shared
os.environ["PYTHONDONTWRITEBYTECODE"] = "1" #OSX hotfix
sys.dont_write_bytecode = True
sys.path.insert(0, '../shared')
import secrets

# Connect to the database
votes_conn = pymysql.connect(host=secrets.DB_HOST,
							 user=secrets.DB_USER,
							 password=secrets.DB_PASS,
							 db=secrets.DB_PROD_ID,
							 charset='utf8mb4',
							 cursorclass=pymysql.cursors.DictCursor)

def set_votes_schema():
	try:
		with votes_conn.cursor() as cursor:
			sql = "CREATE TABLE `Votes` (`video_id` VARCHAR(11) NOT NULL, `votes` INT, `multiplier` DOUBLE, `play_date` DATE, `create_date` DATE, PRIMARY KEY (`video_id`))"
			cursor.execute(sql)
		votes_conn.commit()
	except:
		pass

def set_ledger_schema():
	try:
		with votes_conn.cursor() as cursor:
			sql = "CREATE TABLE `Ledger` (`id` INT NOT NULL AUTO_INCREMENT, `username` VARCHAR(25), `video_id` VARCHAR(11), `timestamp` DATETIME, PRIMARY KEY (`id`))"
			cursor.execute(sql)
		votes_conn.commit()
	except:
		pass

set_votes_schema()
set_ledger_schema()

votes_conn.close()
