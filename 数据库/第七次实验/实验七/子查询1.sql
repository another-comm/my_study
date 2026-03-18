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
-- 查询与“张立伟”在同一个系学习的学生
SELECT SNO,SN,DEPT
FROM S WHERE DEPT=
(SELECT DEPT FROM S WHERE SN='张立伟');

SELECT S1.SNO,S1.SN,S1.DEPT
FROM S AS S1
JOIN S AS S2
ON S1.DEPT=S2.DEPT
WHERE S2.SN='张立伟';

-- 查询选修了课程名为“数据库”的学生学号和姓名 
SELECT SNO,SN 
FROM S 
WHERE SNO IN 
(SELECT SNO 
  FROM SC 
  WHERE CNO IN
  (SELECT CNO 
    FROM C
    WHERE CN='数据库')
);

SELECT S.SNO,S.SN FROM S
JOIN SC
ON SC.SNO=S.SNO
JOIN C
ON C.CNO=SC.CNO
WHERE C.CN='数据库';

-- 找出每个学生超过他选修课程平均成绩的课程号
SELECT SNO,CNO FROM SC AS X
WHERE SCORE>=(
  SELECT AVG(SCORE)
  FROM SC AS Y 
  GROUP BY Y.SNO 
  HAVING Y.SNO=X.SNO);

-- 查询选修了C1课程的学生的学号姓名
SELECT SNO,SN 
FROM S WHERE EXISTS
(SELECT * FROM SC 
  WHERE SC.SNO=S.SNO AND CNO='C1');

SELECT S.SNO,S.SN
FROM S 
JOIN SC
ON S.SNO=SC.SNO
WHERE SC.CNO='C1';

-- 查询没有选修1号课程的学生姓名
SELECT SNO,SN 
FROM S WHERE NOT EXISTS
(SELECT * FROM SC 
  WHERE SC.SNO=S.SNO AND CNO='C1');



-- 其它
-- 创建一个user1表,id username
CREATE TABLE user1(
    id int UNSIGNED AUTO_INCREMENT KEY,
    username VARCHAR(20)
)SELECT id,username FROM emp;

-- 将stu表中id=3的用户名写入到user1表中
INSERT user1(username) SELECT username FROM stu where id=3;

-- 创建象user1一样的表user2
CREATE TABLE user2 LIKE user1;
INSERT user2(username) SELECT username FROM stu;

-- 将stu表中的tiancai用户名添加到user2表中
INSERT user2 SET username=(SELECT username FROM stu WHERE id=5);

-- 去掉字段的重复值
SELECT DISTINCT(username) FROM user2;

-- 将user1和user2数据合并到一起
--去重
SELECT username FROM user1
UNION
SELECT username FROM user2;
--不去重
SELECT username FROM user1
UNION ALL
SELECT username FROM user2;