#!/usr/bin/env python

# Python imports
import os

# CronTab
from crontab import CronTab

cron = CronTab(user=True)

job = cron.new(command='/home/ec2-user/ProjectSocrates/ProjectSocrates/bin/python /home/ec2-user/ProjectSocrates/utils/delete_old_entries.py'.format(os.getcwd()))
job.every(1).days()

job2 = cron.new(command='/home/ec2-user/ProjectSocrates/ProjectSocrates/bin/python /home/ec2-user/ProjectSocrates/utils/add_reddit.py'.format(os.getcwd()))
job2.every(1).days()

cron.write()
