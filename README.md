# ProjectSocrates

Steps to get Project Up and running

1. Intall git

2. Clone repo: https://github.com/adithyabsk/ProjectSocrates.git
	* copy over the var and etc directories from ```/backups``` if necessary

3. Run this command ```yum -y install $(cat utils/installed-software.log)``` from the project home

4. Intall [pip](https://pip.pypa.io/en/stable/installing/)
	* For CentOS do [this](https://www.liquidweb.com/kb/how-to-install-pip-on-centos-7/)

5. Add the keys to the keys folder by copying over:
	* ```keys.config.sample --> keys.config```
	* ```db_keys.config.sample --> db_keys.config```
	* ```model.config.sample --> model.config```

6. Next, run ```utils/setup.py``` from either utils or the main directory

7. Restore the database backup or run ```utils/init_dbs.py```
	* Make sure to properly configure the database

8. Copy over the systemd files if necessary
