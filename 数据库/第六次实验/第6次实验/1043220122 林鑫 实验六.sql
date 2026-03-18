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

-- 1. 从student表中统计每个院系有多少人并为统计的人数取别名sum_Dept，统计用户名详情并取别名stu_Detail.
SELECT 
    Dept, 
    COUNT(*) AS sum_Dept,
    GROUP_CONCAT(Name) AS stu_Detail
FROM 
    Student
GROUP BY 
    Dept;

-- 2. 从score表中查询每个科目的最高分。
SELECT 
    Cname, 
    MAX(Grade) AS max_grade
FROM 
    score
GROUP BY 
    Cname;

-- 3. 计算每个考试科目的平均成绩。
SELECT 
    AVG(Grade) AS avg_grade
FROM
    score
GROUP BY
    Cname;

-- 4. 将计算机成绩按从高到低进行排序 (显示学生姓名和成绩)
SELECT 
    s.name,sc.Grade
FROM
    Student AS s
JOIN 
    score AS sc 
ON
    s.Sid = sc.Sid
WHERE 
    sc.Cname = '计算机' 
ORDER BY
    sc.Grade DESC;

-- 5. 查询student表中的第2条到第4条的记录
SELECT
    Sid,Num,Name,Sex,Birthday,Dept,Address
FROM
    Student
LIMIT
    1,3;

-- 6. 查询李五一的考试科目和考试成绩
SELECT
    sc.Cname,sc.Grade
FROM
    Student AS s
JOIN
    score AS sc
ON
    s.Sid = sc.Sid
WHERE
    s.Name = '李五一' ;

-- 7. 查询所有学生的信息和考试信息
SELECT
    s.Sid,s.Num,s.Name,s.Sex,s.Birthday,s.Dept,s.Address,
    sc.Id,sc.Cname,sc.Grade
FROM
    Student AS s
JOIN
    score AS sc
ON
    s.Sid = sc.Sid  ;

-- 8. 计算每个学生的总成绩（需显示学生姓名）
SELECT
    s.Name,
    SUM(sc.Grade) AS total_grade
FROM
    Student AS s
JOIN
    score AS sc
ON
    s.Sid = sc.Sid
GROUP BY
    s.Sid ;

-- 9. 查询计算机成绩低于95分的学生的信息
SELECT
     s.Sid,s.Num,s.Name,s.Sex,s.Birthday,s.Dept,s.Address
FROM
    Student AS s
JOIN
    score AS sc
ON
    s.Sid = sc.Sid
WHERE
    sc.Cname = '计算机' AND sc.Grade < 95;

-- 10. 查询同时参加计算机和英语考试的学生的信息
-- (通过两次表连接)
SELECT 
     s.Sid,s.Num,s.Name,s.Sex,s.Birthday,s.Dept,s.Address
FROM 
    Student s
JOIN 
    score sc1 
ON 
    s.Sid = sc1.Sid
JOIN 
    score sc2
ON 
    s.Sid = sc2.Sid
WHERE 
    sc1.Cname = '计算机' AND  sc2.Cname = '英语';

-- 11. 查询姓张或姓王同学的姓名、院系、考试科目和成绩
SELECT 
    s.Name,s.Dept, 
    sc.Cname, sc.Grade
FROM 
    Student s
JOIN 
    score sc 
ON 
    s.Sid = sc.Sid
WHERE 
    s.Name LIKE '张%' OR s.Name LIKE '王%';

-- 12. 查询都是湖南的同学的姓名、年龄、院系、考试科目和成绩。
SELECT
    s.Name,(YEAR(CURDATE()) - s.Birthday) AS Age,s.Dept,
    sc.Cname,sc.Grade
FROM 
    Student s
JOIN 
    score sc 
ON 
    s.Sid = sc.Sid
WHERE
    s.Address LIKE '湖南%'
