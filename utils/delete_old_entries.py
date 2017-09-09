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

votes_conn = pymysql.connect(host=secrets.DB_HOST,
							 user=secrets.DB_USER,
							 password=secrets.DB_PASS,
							 db=secrets.DB_PROD_ID,
							 charset='utf8mb4',
							 cursorclass=pymysql.cursors.DictCursor)

try:
	with votes_conn.cursor() as cursor:
		sql = "DELETE FROM `Votes` WHERE DATEDIFF(CURDATE(), `create_date`) >= 3 AND `play_date` = '0000-00-00'"
		cursor.execute(sql)
	votes_conn.commit()
except Exception as e:
	print "There was an error 1 {}".format(e)