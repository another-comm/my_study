--mysqldump备份数据库
--1 备份数据库 test
mysqldump  -uroot -p --master-data=2 --events --routines --triggers --single-transaction  shop>d:\mysql\db\lxy_shop.sql
--2 备份数据表
mysqldump  -uroot -p  --master-data=2 --events --routines --triggers --single-transaction test provinces>d:\mysql\db\provinces.sql
--3 带条件备份
mysqldump -uroot -p --master-data=2 --events --routines --triggers --single-transaction --where "age>30" test user>d:\mysql\db\user.sql
--3 备份所有的数据库
mysqldump  -uroot -p --master-data=2 --events --routines --triggers --single-transaction --all-databases >d:\mysql\db\all.sql

--4导入数据库 test
--方法一：shell命令下
mysql -uroot -p -e"create database test"
mysql -uroot -p test<d:/db/test.sql
--方法二：mysql命令下
create database test;
use test;
source d:/db/test.sql;



--查看二进制日志
mysqlbinlog --no-defaults -v -v --base64-output=DECODE-ROWS d:\mysql\log\mysql_bin.000027

--利用二进制日志做增量备份
mysqlbinlog --start-position=156  --stop-position=646  d:\mysql\log\mysql_bin.000027>d:\mysql\db\king_diff.sql