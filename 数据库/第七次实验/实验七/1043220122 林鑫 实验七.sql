-- ==============================
-- === 实验题目1 ===
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
-- 1)计算计算机成绩低于95分的学生的信息
SELECT *
FROM Student
WHERE Sid IN (
    SELECT Sid
    FROM Score
    WHERE Cname = '计算机' AND Grade < 95
);

-- 2)查询同时参加计算机和英语考试的学生的信息
SELECT *
FROM Student
WHERE Sid IN (
    SELECT Sid
    FROM Score
    WHERE Cname = '计算机'
)
AND Sid IN (
    SELECT Sid
    FROM Score
    WHERE Cname = '英语'
);
-- 3)查询姓张或姓王同学的姓名、院系、考试科目和成绩
SELECT s.Name,s.Dept,sc.Cname,sc.Grade
FROM Student AS s
JOIN Score AS sc ON s.Sid=sc.Sid
WHERE s.Sid IN(
    SELECT Sid
    FROM Student
    WHERE Name LIKE '张%' OR Name LIKE '王%'
);
-- 4)查询都是湖南的同学的姓名、年龄、院系、考试科目和成绩。
SELECT s.Name,(2025 - s.Birthday) AS Age,s.Dept,sc.Cname,sc.Grade
FROM Student AS s
JOIN Score AS sc ON s.Sid = sc.Sid
WHERE s.Sid IN (
    SELECT Sid
    FROM Student
    WHERE Address LIKE '湖南%'
    );

-- ==============================
-- === 实验题目2 ===
-- ==============================
CREATE TABLE S(
  SNO CHAR(6) PRIMARY KEY,
  SN VARCHAR(20) NOT NULL,
  AGE TINYINT UNSIGNED NOT NULL,
  DEPT VARCHAR(20) 
);
INSERT S VALUES('S1','李立勇',20,'CS'),
               ('S2','刘蓝',23,'IS'),
               ('S3','周小花',18,'MA'),
               ('S4','张立伟',19,'IS'),
               ('S5','王世明',19,'IS'),
               ('S6','陈思思',19,'MS');

CREATE TABLE C(
  CNO VARCHAR(6) PRIMARY KEY,
  CN VARCHAR(10) NOT NULL,
  CPNO VARCHAR(6) 
);
INSERT C VALUES('C1','数据库','C2'),
               ('C2','离散数学',NULL),
               ('C3','操作系统','C4'),
               ('C4','数据结构','C2');

CREATE TABLE SC(
  SNO CHAR(6),
  CNO VARCHAR(6),
  SCORE INT   NOT NULL,
  CONSTRAINT S_C_P PRIMARY KEY(SNO,CNO),
  CONSTRAINT S_F FOREIGN KEY(SNO) REFERENCES S(SNO),
  CONSTRAINT C_F FOREIGN KEY(CNO) REFERENCES C(CNO)
  );
INSERT SC VALUES('S1','C1',85),
                ('S1','C2',90),
                ('S1','C3',89),
                ('S1','C4',88),
                ('S2','C2',78),
                ('S2','C3',85),
                ('S3','C2',68),
                ('S3','C3',78),
                ('S3','C4',75),
                ('S4','C1',69),
                ('S4','C2',82),
                ('S4','C4',73),
                ('S5','C1',92),
                ('S5','C4',86);
                
-- ==============================
-- === 实验题目部分 ===
-- ==============================
-- 1)检索学生的所有情况。
SELECT *
FROM S;
-- 2)检索学生年龄大于等于20岁的学生姓名。
SELECT SN
FROM S
WHERE AGE >=20;
-- 3)检索先修课号为C2的课程号。
SELECT CNO
FROM C
WHERE CPNO = 'C2';
-- 4)检索选修了课程号C1成绩为A(大于等于90)的所有学生姓名。
SELECT SN
FROM S
WHERE SNO IN (
    SELECT SNO
    FROM SC
    WHERE CNO = 'C1' AND SCORE >= 90
);
-- 5)检索学号为S1的学生修读的所有课程名及先修课号。
SELECT CN,CPNO
FROM C
WHERE CNO IN (
    SELECT CNO
    FROM SC
    WHERE SNO = 'S1'
);
-- 6)检索年龄为23岁的学生所修读的课程名。
SELECT CN
FROM C
WHERE CNO IN (
    SELECT CNO
    FROM SC 
    WHERE SNO IN (
        SELECT SNO
        FROM S
        WHERE Age = 23
        )
    );
-- 7)检索至少修读了学号为S5的学生修读的一门课的学生的姓名。
SELECT SN
FROM S
WHERE SNO IN (
    SELECT SNO
    FROM SC
    WHERE CNO IN (  
        SELECT CNO
        FROM SC
        WHERE SNO = 'S5'
        )
    );
-- 8)检索不选修任何课程的学生的学号。
SELECT T1.SNO
FROM S AS T1
LEFT JOIN SC AS T2 ON T1.SNO = T2.SNO
WHERE T2.CNO IS NULL;

-- 4.（附加题）对练习3增加如下查询请求：
-- 1)检索不选修任何课程的学生的学号
同上面第8题
-- 2)查询选课两门课的学生的姓名
SELECT T1.SN
FROM S AS T1
JOIN SC AS T2 ON T1.SNO = T2.SNO
GROUP BY  T1.SNO, T1.SN 
HAVING COUNT(T2.CNO) = 2; 

-- 3)查询学习课程号为'C2',成绩为第一名的学生的姓名
SELECT T1.SN
FROM S AS T1
JOIN SC AS T2 ON T1.SNO =T2.SNO
WHERE T2.CNO = 'C2' AND T2.SCORE=(
                                SELECT MAX(SCORE)
                                FROM SC
                                WHERE CNO ='C2'
                                );
-- 4)查询选修C2课程成绩大于该课平均成绩的学生的姓名学号成绩
SELECT T1.SN,T1.SNO,T2.SCORE
FROM S AS T1
JOIN SC AS T2 ON T1.SNO =T2.SNO
WHERE T2.CNO = 'C2' AND T2.SCORE>(
                                SELECT AVG(SCORE)
                                FROM SC
                                WHERE CNO ='C2'
                                );


