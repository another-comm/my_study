

-- 、使用查询数据1.sql文件中的user表完成如下操作

DROP DATABASE Student;
CREATE DATABASE IF NOT EXISTS Student;
USE Student;

CREATE TABLE user(
id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(20) NOT NULL UNIQUE COMMENT '编号',
age TINYINT UNSIGNED NOT NULL DEFAULT 18  COMMENT '年龄',
sex ENUM('男','女','保密') NOT NULL DEFAULT '保密' COMMENT '性别',
addr VARCHAR(20) NOT NULL DEFAULT '北京',
married TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0代表未结婚，1代表已婚',
salary FLOAT(8,2) NOT NULL DEFAULT 0 COMMENT '薪水'
)ENGINE=INNODB CHARSET=UTF8;
INSERT user VALUES(1,'king',23,'男','北京',1,50000);
INSERT user(username,age,sex,addr,married,salary) VALUES('queen',27,'女','上海',0,25000);
INSERT user SET username='imooc',age=31,sex='女',addr='北京',salary=40000;
INSERT user VALUES(NULL,'张三',38,'男','上海',0,15000),
(NULL,'张三风',38,'男','上海',0,15000),
(NULL,'张子轩',39,'女','北京',1,85000),
(NULL,'汪杨',42,'男','深圳',1,95000),
(NULL,'刘德凯',58,'男','广州',0,115000),
(NULL,'吴峰',28,'男','北京',0,75000),
(NULL,'浦丽',18,'女','北京',1,65000),
(NULL,'刘小明',36,'女','广州',0,15000);

-- 1）创建视图user_view,显示user表的name，age，salary并将字段名显示为user_name、user_age,user_salary.
CREATE VIEW user_view AS
SELECT	username AS user_name,age AS user_age, salary AS user_salary
FROM user;
-- 2）查看视图的详细结构
DESC user_view;

-- 3）更新视图，插入三条记录：
-- 李四，28，23000
-- 王武，30，35000
-- 严淼，34，5600
INSERT INTO user_view (user_name, user_age, user_salary) VALUES 
('李四', 28, 23000),
('王武', 30, 35000),
('严淼', 34, 5600);

-- 4) 从user_view中查询年龄大于25岁的用户（结合理论课思考视图的查询是如何转化为对基本表的查询）。 
SELECT * FROM user_view WHERE user_age > 25;

-- 5）修改视图，使视图显示年龄大于30岁的用户信息
ALTER VIEW user_view AS
SELECT username AS user_name,age AS user_age, salary AS user_salary
FROM user
WHERE age >30;
-- 6）删除视图
DROP VIEW user_view;