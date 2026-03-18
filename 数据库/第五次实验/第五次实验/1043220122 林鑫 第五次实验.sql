-- ==============================
-- 设计性实验五：Student与Score表查询
-- ==============================

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS school ;
USE school;

-- 2. 删除旧表（若存在）
DROP TABLE IF EXISTS Score;
DROP TABLE IF EXISTS Student;

-- 3. 创建 Student 表
CREATE TABLE Student (
    Sid INT PRIMARY KEY AUTO_INCREMENT,
    Num INT NOT NULL UNIQUE,
    Name VARCHAR(20) NOT NULL,
    Sex VARCHAR(4) NOT NULL,
    Birthday YEAR,
    Dept VARCHAR(20) NOT NULL,
    Address VARCHAR(50)
)ENGINE=INNODB CHARSET=UTF8;

-- 4. 创建 Score 表

CREATE TABLE Score (
    Id INT PRIMARY KEY AUTO_INCREMENT,
    Cname VARCHAR(20),
    Sid INT NOT NULL,
    Grade INT,
    FOREIGN KEY (Sid) REFERENCES Student(Sid)
)ENGINE=INNODB CHARSET=UTF8;

-- 5. 插入 Student 表数据
INSERT INTO Student (Sid, Num, Name, Sex, Birthday, Dept, Address) VALUES
(1, 901, '张军', '男', 1985, '计算机系', '北京市海淀区'),
(2, 902, '张超群', '男', 1986, '中文系', '北京市昌平区'),
(3, 903, '张美丽', '女', 1990, '中文系', '云南省西双版纳'),
(4, 904, '李五一', '男', 1990, '英语系', '辽宁省阜新市'),
(5, 905, '王芳', '女', 1991, '英语系', '福建省厦门市'),
(6, 906, '王桂', '男', 1988, '计算机系', '湖南省衡阳市');

-- 6. 插入 Score 表数据

INSERT INTO Score (Id, Cname, Sid, Grade) VALUES
(1, '计算机', 1, 98),
(2, '英语', 1, 80),
(3, '计算机', 2, 65),
(4, '中文', 2, 88),
(5, '中文', 3, 95),
(6, '计算机', 4, 70),
(7, '英语', 4, 92),
(8, '英语', 5, 94),
(9, '计算机', 6, 90),
(10, '英语', 6, 85);

-- ==============================
-- === 实验题目部分 ===
-- ==============================

-- 1) 查询 Student 表的所有记录
-- 方法一：
SELECT * FROM Student;
-- 方法二：
SELECT Sid, Num, Name, Sex, Birthday, Dept, Address FROM Student;

-- 2) 查询所有学生的学号、姓名和院系信息
SELECT Num, Name, Dept FROM Student;

-- 3) 查询计算机系和英语系的学生信息
-- 方法一：IN
SELECT * FROM Student WHERE Dept IN ('计算机系', '英语系');
-- 方法二：OR
SELECT * FROM Student WHERE Dept = '计算机系' OR Dept = '英语系';

-- 4) 查询年龄在18到22岁的学生
-- 方法一：BETWEEN AND
SELECT * FROM Student
WHERE (DATE_FORMAT(NOW(), '%Y') - Birthday) BETWEEN 18 AND 22;
-- 方法二：AND 比较
SELECT * FROM Student
WHERE (DATE_FORMAT(NOW(), '%Y') - Birthday) >= 18
  AND (DATE_FORMAT(NOW(), '%Y') - Birthday) <= 22;

-- 5) 查询北京市的学生
SELECT * FROM Student WHERE Address LIKE '北京市%';

-- 6) 查询姓张且姓名为三个字的学生
SELECT * FROM Student WHERE Name LIKE '张__';

-- 7) 为 Student 表新增一列 Desc，允许为 NULL
ALTER TABLE Student ADD  `Desc` VARCHAR(100) NULL;

-- 8) 更新学号为903的学生的Desc为“少数民族生”
UPDATE Student SET `Desc` = '少数民族生' WHERE Num = 903;

-- 9) 查询 Desc 为空的学生
SELECT * FROM Student WHERE `Desc` IS NULL;

-- 10) 查询计算机成绩≥90的学生编号
SELECT Sid FROM Score WHERE Cname = '计算机' AND Grade >= 90;
