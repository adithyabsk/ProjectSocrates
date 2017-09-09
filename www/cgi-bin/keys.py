#!/usr/bin/python

import sys
import cgi
import os
import subprocess


data = cgi.FieldStorage()

pubkey = data.getvalue("auth")
request = data.getvalue("file")




with open("/home/ec2-user/ProjectSocrates/keys/authorized_keys",'r') as keys:
	for key in keys.readlines():
		if(pubkey.split(' ')[1].split() == key.split(' ')[1].split()):
			with open("/home/ec2-user/ProjectSocrates/keys/" + str(request),'r') as resp:
				print "Status: 200 Ok\n"
				print(resp.read())


