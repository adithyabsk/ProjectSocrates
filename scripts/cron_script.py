#!/usr/bin/env python

# Python imports
import os

# CronTab
from crontab import CronTab

cron = CronTab(user=True)

job = cron.new(command='python {}/scripts/delete_old_entries.py'.format(os.getcwd()))
job.every(1).days()

cron.write()
