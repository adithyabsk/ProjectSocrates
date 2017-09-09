#!/bin/bash

#Upack Backup
tar -xvzf $1
cd backup


#Install Required Packages
yum -y install $(cat installed-software.log)
pip install -r requirements.txt

#Setup virtualenv
virtualenv /home/ec2-user/ProjectSocrates/ProjectSocrates
/home/ec2-user/ProjectSocrates/ProjectSocrates/bin/pip install -r /home/ec2-user/ProjectSocrates/utils/requirements.txt

#Unpack etc directory (config files)
tar -xvf --overwrite etc.tar.gz -C /etc

#Symlink www directory
mv /var/www /var/www-old
ln -s /home/ec2-user/ProjectSocrates/www /var/www

#Set file permissions
chmod a+x /home/ec2-user/
chmod a+x /home/ec2-user/ProjectSocrates

chown -R apache:apache /home/ec2-user/ProjectSocrates/www
chown -R apache:apache /home/ec2-user/ProjectSocrates/keys

chmod -R 777 /home/ec2-user/ProjectSocrates/www
chmod -R 777 /home/ec2-user/ProjectSocrates/keys

#Import MySQL databases and update privs
"CREATE DATABASE test" | mysql -u root
"CREATE DATABASE prod" | mysql -u root
mysql -u root test < test.sql
mysql -u root prod < prod.sql
mysql -u root 'flush privileges;'

#Install twitchbot service
ln -s twitchbot.service /etc/systemd/system/twitchbot.service
chmod 664 /etc/systemd/system/twitchbot.service
chmod a+x /home/ec2-user/

systemctl enable twitchbot.service
systemctl start twitchbot.service

#Set apache to autostart
systemctl enable httpd.service
systemctl start httpd.service

#Clean Up
cd ..
rm -rf backup/


