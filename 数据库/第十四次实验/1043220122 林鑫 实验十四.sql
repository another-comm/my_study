-- 一、通过课堂PPT中的实例验证INNODB的四个隔离级别，并说明每个隔离级别的实现原理

四个隔离级别的原理：
1.未提交读：读不加锁，写加排它锁（X锁），直接读取磁盘中的数据。
2.提交读：基于 MVCC（多版本并发控制）实现 。读不加锁，执行“快照读”，且总是读取最新的快照；写加排它锁（X锁） 。
3.可重复读：基于 MVCC 。读不加锁，执行“快照读”，且总是读取事务开始后第一次读到的那个版本的快照；写加排它锁（X锁） 。
4.序列化：提供最高级别的隔离 。读加共享锁（S锁），写加排它锁（X锁），事务按顺序执行 。

-- 二、（1）确保二进制日志开启（2）将test数据库做一个全备份。（3）备份完后，在test数据库下创建一个和users一样的temp表，并将users表的数据复制给temp表。（4）误操作将test数据库删除了。（5）用全备和二进制日志恢复test数据库（包括新建的temp表）。
mysqldump -uroot -p --master-data=2  --single-transaction test > "C:\MySQL\mysql-8.0.25-winx64\mysql-8.0.25-winx64\db\test_backup.sql"
use test;
create table temp as select * from user;
drop database test;
mysql -uroot -p -e "create database test"
mysql -uroot -p test < "C:\MySQL\mysql-8.0.25-winx64\mysql-8.0.25-winx64\db\test_backup.sql"
mysqlbinlog --no-defaults --start-position=156 --stop-position=552 "C:\MySQL\mysql-8.0.25-winx64\mysql-8.0.25-winx64\log\mysql_bin.000028" | mysql -uroot -p test
-- 三、（1）刷新二进制日志（2）在temp表中任意添加一条记录 （3）误操作将刚添加的记录删除了（4）请利用二进制日志开始位置和结束位置对其进行恢复。
flush logs;
insert into temp (username, age) values ('test_user', 25);
delete from temp where username = 'test_user';
mysqlbinlog --no-defaults --start-position=235 --stop-position=453 "C:\MySQL\mysql-8.0.25-winx64\mysql-8.0.25-winx64\log\mysql_bin.000029" | mysql -uroot -p test