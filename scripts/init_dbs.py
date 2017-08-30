#!/usr/bin/env python

import pymysql.cursors

# DB
db_keys = None
if os.path.isfile("db_keys.config"):
  with open("db_key.config", "r") as model_file:
    model_parameters = json.load(model_file)
else:
  sys.exit("db_key.config was not found, please update model config file")

# Config DB
DB_HOST = secrets["DB_HOST"]
DB_USER = secrets["DB_USER"]
DB_PASS = secrets["DB_PASS"]
DB_ID = secrets["DB_ID"]

# Connect to the database
votes_conn = pymysql.connect(host=DB_HOST,
                             user=DB_USER,
                             password=DB_PASS,
                             db=DB_ID,
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