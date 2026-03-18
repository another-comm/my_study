-- 创建数据库 StudentInfo
CREATE DATABASE StudentInfo;
-- 使用数据库
USE StudentInfo;
-- 创建加上约束的student表
CREATE TABLE student(
	Uid INT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE COMMENT "学生编号",
	num CHAR(10) NOT NULL UNIQUE COMMENT "学号",
	name VARCHAR(20)  NOT NULL COMMENT "姓名",
	sex ENUM('男','女') NOT NULL COMMENT "性别",
	birthday DATE COMMENT "出生日期",
	address JSON COMMENT "家庭住址"
)ENGINE=INNODB CHARSET=utf8mb4;

-- 创建加上约束的grade表
CREATE TABLE grade(
	Cid INT PRIMARY KEY AUTO_INCREMENT NOT NULL UNIQUE COMMENT "课程编号",
	Course VARCHAR(10) NOT NULL COMMENT "课程名",
	Uid INT NOT NULL COMMENT "学生编号",
	Grade SMALLINT COMMENT "成绩",
	-- 定义外键约束：将Uid关联到student表的Uid字段
	FOREIGN KEY(Uid) REFERENCES student(Uid)
)ENGINE=INNODB CHARSET=utf8mb4;


