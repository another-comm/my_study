-- 1.用root用户创建exam1@localhost用户，初始密码设置为‘123456’。让该用户对所有数据拥有SELECT,CREATE,DROP,SUPER和GRANT权限。
CREATE USER 'exam1'@'localhost' identified BY '123456';
GRANT SELECT,CREATE,DROP,SUPER ON *.* TO 'exam1'@'localhost' WITH GRANT OPTION;

-- 2.从四张权限表User，Db，Tables_priv，Columns_priv查看用户权限
SELECT * FROM mysql.user WHERE User='exam1' AND Host='localhost'\G;
SELECT * FROM mysql.db WHERE User='exam1' AND Host='localhost'\G;
SELECT * FROM mysql.tables_priv WHERE User='exam1' AND Host='localhost'\G;
SELECT * FROM mysql.columns_priv WHERE User='exam1' AND Host='localhost'\G;

-- 3.创建用户exam2@localhost，该用户没有初始密码。
CREATE USER 'exam2'@'localhost';

-- 4.将exam2@localhost重命名为exam3@localhost
RENAME USER 'exam2'@'localhost' TO 'exam3'@'localhost';

-- 5.用exam3登录，将其密码设置为‘686868’。
exit
mysql -u exam3 -p
ALTER user user() identified BY '686868';

-- 6.用exam1登录，为exam3设置CREATE和DROP权限。
exit
mysql -u exam1 -p
GRANT CREATE,DROP ON *.* TO 'exam3'@'localhost';

-- 7.用root用户登录，收回exam1和exam3的所有权限。
exit
mysql -u root -p
REVOKE ALL ON *.* FROM 'exam1'@'localhost';
REVOKE ALL ON *.* FROM 'exam3'@'localhost';

