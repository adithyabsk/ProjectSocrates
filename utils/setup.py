#!/usr/bin/env python

# Sets up virtualenv and initializes database

import os

print("This assumes you have setup pip and have installed virtualenv")

if 'utils' in os.getcwd(): os.chdir("..")

os.system("virtualenv ProjectSocrates")

new_shell_path = "{}/ProjectSocrates/bin/activate_this.py".format(os.getcwd())
execfile(new_shell_path, dict(__file__=new_shell_path))

os.system("pip install -r requirements.txt")

os.system("pip list")

os.system("cron_script.py")

os.system("")