#!/usr/bin/env python

# MariaDB API
import pymysql.cursors

# DB
db_keys = None
if os.path.isfile("db_keys.config"):
  with open("db_keys.config", "r") as key_file:
    db_keys = json.load(key_file)
else:
  sys.exit("db_keys.config was not found, please update model config file")

# DB
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

try:
  with votes_conn.cursor() as cursor:
    sql = "DELETE FROM `Votes` WHERE DATEDIFF(CURRDATE(), `create_date`) >= 3 AND `play_date` != '0000-00-00'"
    cursor.execute(sql)
  votes_conn.commit()
except Exception as e:
  print "There was an error 1 {}".format(e)