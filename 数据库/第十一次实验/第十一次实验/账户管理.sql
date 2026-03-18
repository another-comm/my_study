--创建用户
--1.查询create user 语法
 \h create user

--2.新建用户
CREATE USER test@'localhost' identified by '123456';
CREATE USER test@'%' identified by '123456';



--查看用户

SELECT user,host,authentication_string FROM mysql.user;
SELECT * FROM mysql.user WHERE user='test'\G


--3.在另一个session中登录用户,无授权，所以只能看到一个库information_schema

--4.在session1中设置用户过期
ALTER USER test@'localhost' PASSWORD EXPIRE;

--5.在session2中再次登录
/*[root@node-5 ~]# mysql -utest -p 
Enter password: 
mysql> show databases;
ERROR 1820 (HY000): You must reset your password using ALTER USER statement before executing this statement.
mysql> 
提示密码过期，重新设置密码
修改为原密码*/

-- 在session2中修改密码 user()函数为获取当前用户
mysql> alter user user() identified by '123456';


--删除用户
-- 用drop 语句
 DROP USER test@'%';

--修改用户账户
  RENAME user test@'localhost' TO test1@'localhost';
  RENAME user test1@'localhost' TO test@'localhost';
--修改用户密码

-- 使用Alter语句 
  ALTER user user() identified by '654321';




--账户权限管理
--1.授予权限
--a 将数据库的的所有权限赋给test@‘localhost’
GRANT ALL ON *.* TO 'test'@'localhost'; 

--b、为test1用户授予test库中所有表所有权限
CREATE USER test1@'localhost' identified by '123456';
GRANT ALL ON test.* TO 'test1'@'localhost';

--c、为test2用户授予test库中user表的SELECT权限
CREATE USER test2@'localhost' identified by '123456';
GRANT SELECT ON test.user TO 'test2'@'localhost';
SELECT * FROM mysql.tables_priv WHERE user='test2'\G

--d、为test3用户授予test库中user表的age字段SELECT update权限
CREATE USER test3@'localhost' identified by '123456';
GRANT UPDATE(age),SELECT(age) ON test.user TO 'test3'@'localhost';
SELECT * FROM mysql.columns_priv WHERE user='test3'\G

--session1上创建用户exam1并授权带WITH GRANT OPTION允许其可以将自身的权限授予其它用户
--并在session1上创建用户exam2
CREATE  USER exam1@'localhost' identified by '000';
GRANT CREATE,SELECT,DROP,INSERT,UPDATE ON  test.* TO exam1@'localhost'WITH GRANT OPTION;

CREATE USER exam2@'localhost' identified by '000';
--exam1开启session2 为exam2 授权
GRANT SELECT,DROP ON  test.* TO exam2@'localhost';
SELECT * FROM mysql.DB WHERE user='exam1'\G
--2.权限撤销
REVOKE CREATE ON test.* FROM 'exam1'@'localhost' ;
REVOKE ALL ON *.* FROM 'exam2'@'localhost' ;

