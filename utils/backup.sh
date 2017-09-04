#!/bin/bash

mkdir backup
cd backup

rpm -qa > installed-software.log

mysqldump -u root -pBagwell107 test > test.sql
mysqldump -u root -pBagwell107 prod > prod.sql


tar -zcvf www-data.tar.gz /var/www/
tar -zcvf etc.tar.gz /etc/


cd ..

tar -zcvf backup$(date '+%Y%m%d').tar.gz backup/
rm -rf backup/


