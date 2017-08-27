#!/usr/bin/env python
 
from time import time
from urllib import urlencode
from sqlite3 import connect, Error as sqerr
from urllib2 import urlopen, Request
from circuits.web import Controller, Server
 
def verify_ipn(data):
	# prepares provided data set to inform PayPal we wish to validate the response
	data["cmd"] = "_notify-validate"
	params = urlencode(data)
 
	# sends the data and request to the PayPal Sandbox
	req = Request("""https://www.sandbox.paypal.com/cgi-bin/webscr""", params)
	req.add_header("Content-type", "application/x-www-form-urlencoded")
	# reads the response back from PayPal
	response = urlopen(req)
	status = response.read()
 
	# If not verified
	if not status == "VERIFIED":
		return False
 
	# if not the correct receiver ID
	if not data["receiver_id"] == "6494XYFBWKC8U":
		return False
 
	# if not the correct currency
	if not data["mc_currency"] == "USD":
		return False
 
	# otherwise...
	return True
 
class Root(Controller):
	# if the app will not be served at the root of the domain, uncomment the next line
	#channel = "/ipn"
 
	# index is invoked on the root path, or the designated channel URI
	def index(self, **data):
		# If there is no txn_id in the received arguments don't proceed
		if not "txn_id" in data:
			return "No Parameters"
 
		# Verify the data received with Paypal
		if not verify_ipn(data):
			return "Unable to Verify"
 
		# Suggested Check : check the item IDs and Prices to make sure they match with records
 
		# If verified, store desired information about the transaction
		reference = data["txn_id"]
		amount = data["mc_gross"]
		email = data["payer_email"]
		name = data["first_name"] + " " + data["last_name"]
		status = data["payment_status"]

		# Get user twitch username from transaction
		# Add flag to know whether credits have been used
 
		# Open a connection to a local SQLite database (use MySQLdb for MySQL, psycopg or PyGreSQL for PostgreSQL)
		conn = connect('db')
		curs = conn.cursor()
		try:
			curs.execute("""INSERT INTO ipn (id, purchased, txn, name, email, price, notes, status) 
			VALUES (NULL, ?, ?, ?, ?, ?, NULL, ?)""", (time(), reference, name, email, amount, status,))
			conn.commit()
		except sqerr, e:
			return "SQL Error: " + e.args[0]
		conn.close()
 
		# Alternatively you can generate license keys, email users login information
		# or setup accounts upon successful payment. The status will always be "Completed" on success.
		# Likewise you can revoke user access, if status is "Canceled", or another payment error.
 
		return "Success"
 
	def lookup(self, id):
		if not id:
			return ierr("No Transaction Provided")
 
		conn = connect('db')
		curs = conn.cursor()
		try:
			# Pulls a record from the database matching the transaction ID
			curs.execute("""SELECT name FROM ipn WHERE txn = ? LIMIT 1""", (id,))
			row = curs.fetchone()
			ret = row[0]
		except sqerr, e:
			ret = ierr(e.args[0])
 
		# The response will either by the name of the buyer, or a SQL error message
		return ret
 
# Standard TCP method		
#(Server(("127.0.0.1", 9000)) + Root()).run()
 
# Unix Socket Method - make sure webserver can read and write to the socket file
(Server(("ipn.sock")) + Root()).run()