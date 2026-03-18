CREATE DATABASE test;
USE test;
---创建数据表employee(不加约束）---
CREATE TABLE employee(
	id SMALLINT   COMMENT "编号",
	num CHAR(10)  COMMENT "工号",
	name VARCHAR(20) COMMENT "姓名",
	sex ENUM('男','女','保密')  COMMENT "性别",
	birthday D COMMENT "生日",
	address JSON COMMENT "地址", 
	salary DECIMAL(8,2) COMMENT "薪水"
	)ENGINE=INNODB CHARSET=UTF8;

---查看数据表employee
DESC employee;
SHOW CREATE TABLE employee;

---添加记录---
INSERT employee VALUES(1,'8133500125','张三','男','1969-05-18','{"province":"江苏","city":"无锡","detail":"万科城市花园"}
',8010.75);

INSERT employee(name,birthday)VALUES('小王','1990-09-05');

---查询记录---
SELECT * FROM employee;

---非空约束----
CREATE TABLE t1(
  id SMALLINT NOT NULL ,
  name VARCHAR(20)
  );
INSERT INTO t1(name)VALUES('kitty');
---自增，主键约束----
---列级---
CREATE TABLE t2(
  id SMALLINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(20) NOT NULL,
  age TINYINT
  );
---表级---
CREATE TABLE t2(
  id SMALLINT  AUTO_INCREMENT,
  name VARCHAR(20) NOT NULL,
  age TINYINT,
  PRIMARY KEY(id)
  );
INSERT INTO t2(name,age)VALUES('mike',18);
INSERT INTO t2(name,age)VALUES('jack',18);
--重置auto
-- 1.
-- 直接重置autoIncrement的值 ALTER TABLE table_name AUTO_INCREMENT =1;
ALTER TABLE t2 AUTO_INCREMENT=6;
INSERT INTO t2(name,age)VALUES('lily',20);
-- 2.
-- 通过truncate table 完成 TRUNCATE TABLE table_name;
TRUNCATE TABLE t2;



---唯一约束---
---列级---
CREATE TABLE t3(
  id SMALLINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(20) NOT NULL,
  age TINYINT,
  num CHAR(10) UNIQUE
  );
---表级---
CREATE TABLE t3(
  id SMALLINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(20) NOT NULL,
  age TINYINT,
  num CHAR(10),
  UNIQUE(num)
  );

---默认约束只有列级约束---
CREATE TABLE t4(
  id SMALLINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(20) ,
  sex ENUM('男','女')  NOT NULL DEFAULT '男',
  num CHAR(10) UNIQUE
  );

---外键约束---
---父表---
CREATE TABLE province(
  id SMALLINT PRIMARY KEY AUTO_INCREMENT,
  pname VARCHAR(10) NOT NULL UNIQUE
  );

  INSERT province VALUES
  (NULL,'江苏'),
  (NULL,'浙江'),
  (NULL,'湖北');
 
 SELECT * FROM province;

 ---子表外键约束---
 CREATE TABLE users(
 	id SMALLINT PRIMARY KEY AUTO_INCREMENT,
 	name VARCHAR(20) NOT NULL,
 	pid SMALLINT ,
 	FOREIGN KEY(pid) REFERENCES province(id)
 	 	);


-- 加上约束的employee表
CREATE TABLE employee(
  id SMALLINT  PRIMARY KEY AUTO_INCREMENT COMMENT "编号",
  num CHAR(10) UNIQUE COMMENT "工号",
  name VARCHAR(20) COMMENT "姓名",
  sex ENUM('男','女','保密') NOT NULL DEFAULT '保密' COMMENT "性别",
  birthday DATE COMMENT "生日",
  address JSON COMMENT "地址", 
  salary DECIMAL(8,2) COMMENT "薪水"
  )ENGINE=INNODB CHARSET=UTF8;

-- 修改表结构
CREATE TABLE USERS1(
 id SMALLINT,
 name VARCHAR(20) NOT NULL,
 pid SMALLINT
 );
---1.增加列---
ALTER TABLE users1 ADD age TINYINT AFTER name;
ALTER TABLE users1 ADD address VARCHAR(50) FIRST;

---删除列----
ALTER TABLE users1 DROP address ;



---2修改列定义-----
ALTER TABLE users1 MODIFY name VARCHAR(30) AFTER pid;

---3修改列名称----
ALTER TABLE users1 CHANGE name username VARCHAR(50);


---4增加主键---

ALTER TABLE users1 ADD  PRIMARY KEY(id);
---删除主键---

ALTER TABLE users1 DROP  PRIMARY KEY;


---5增加唯一约束---
ALTER TABLE users1 ADD  UNIQUE(username);

---删除唯一约束---
SHOW INDEXES FROM users1\G;

ALTER TABLE users1 DROP INDEX username;


----6增加外键,利用SHOW CREATE TABLE employee;查看添加的外键约束的约束名----

ALTER TABLE users ADD FOREIGN KEY(pid) REFERENCES province(id);


----先查找到外键名称，然后删除外键----
SHOW CREATE TABLE users;
ALTER TABLE users DROP FOREIGN KEY users_ibfk_1;

--7增加默认--
ALTER TABLE users1 ALTER age SET DEFAULT 20; 
--删除默认--
ALTER TABLE users1 ALTER age DROP DEFAULT;

----8改表名----
ALTER TABLE users1 RENAME TO users_p;
RENAME TABLE users_p TO newusers;

--9改存储引擎--
ALTER TABLE newusers ENGINE=MyISAM;





