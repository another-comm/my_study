-- 1.启动和关闭mysql服务

net start mysql
net stop mysql

-- 2.登录mysql

mysql -uroot -p

-- 退出mysql

quit

-- 3.利用prompt 命令修改提示符为：当前用户@服务器名>;

prompt \u@\h>

-- 4.显示当前服务器版本，当前日期，当前用户，当前数据库;

SELECT VERSION();
SELECT NOW();
SELECT USER();
SELECT DATABASE();

-- 5.创建shop数据库;

CREATE DATABASE IF NOT EXISTS shop;

 --6.查看shop数据库信息;

 SHOW CREATE DATABASE shop;

-- 7.修改数据库的字符集为big5;

  ALTER DATABASE shop CHARACTER SET big5;

-- 8删除shop 数据库

  DROP DATABASE IF EXISTS shop;

