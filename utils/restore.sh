#!/bin/bash

tar -xvzf $1
cd backup

yum -y install $(cat installed-software.log)
yum -y install expect

tar -xvf --overwrite www-data.tar.gz -C /var/www
tar -xvf --overwrite etc.tar.gz -C /etc

mysql -u root test < test.sql
mysql -u root prod < prod.sql
mysql -u root 'flush privileges;'

cp twitchbot.service /etc/systemd/system
chmod 664 /etc/systemd/system/twitchbot.service

systemctl enable twitchbot.service
systemctl start twitchbot.service

systemctl enable httpd.service
systemctl start httpd.service

cd ..
rm -rf backup/


