#!/usr/bin/env python

from crontab import CronTab

cron = CronTab(user=True)

job = cron.new(command='python {}/scripts/delete_old_entries.py'.format(os.getcwd()))
job.day.every(1)

cron.write()