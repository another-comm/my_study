-- 创建数据库
CREATE DATABASE IF NOT EXISTS Student;
USE Student;

-- 学生表
CREATE TABLE S (
    `S#` INT PRIMARY KEY,
    SNAME VARCHAR(20),
    AGE INT,
    SEX CHAR(2)
);

-- 课程表
CREATE TABLE C (
    `C#` INT PRIMARY KEY,
    CNAME VARCHAR(30),
    TEACHER VARCHAR(20)
);

-- 选课表
CREATE TABLE SC (
    `S#` INT,
    `C#` INT,
    GRADE DECIMAL(5,2),
    PRIMARY KEY(`S#`, `C#`),
    FOREIGN KEY(`S#`) REFERENCES S(`S#`),
    FOREIGN KEY(`C#`) REFERENCES C(`C#`)
);

-- 学生表数据
INSERT INTO S VALUES
(1,'张三',20,'男'),
(2,'李四',21,'女'),
(3,'王五',20,'男'),
(4,'赵六',22,'女');

-- 课程表数据
INSERT INTO C VALUES
(1,'高等数学','程军'),
(2,'大学英语','王霞'),
(3,'数据库','程军'),
(4,'线性代数','李明');

-- 选课表数据
INSERT INTO SC VALUES
(1,1,88),(1,2,90),(1,3,92),
(2,1,85),(2,3,80),
(3,1,75),(3,2,60),(3,3,78),(3,4,81),
(4,2,88),(4,3,85);


-- (1)检索至少选修“程军”老师所授全部课程的学生姓名(SNAME)。-- (不存在程军老师教授但是没选的课程)
SELECT SNAME
FROM S
WHERE NOT EXISTS (
    SELECT `C#`
    FROM C
    WHERE TEACHER = '程军'  AND NOT EXISTS (
          SELECT *
          FROM SC
          WHERE SC.`S#` = S.`S#`
            AND SC.`C#` = C.`C#`
      )
);

-- (2)检索选修课程包含“程军”老师所授课程之一的学生学号(S#)。
SELECT `S#`
FROM S
WHERE EXISTS(
    SELECT *
    FROM C
    WHERE TEACHER = '程军' AND EXISTS(
        SELECT *
          FROM SC
          WHERE SC.`S#` = S.`S#`
            AND SC.`C#` = C.`C#`
            )
    );
-- (3)检索全部学生都选修的课程的课程号(C#)和课程名(CNAME)。(这个课程不存在有学生没选)
SELECT `C#`,CNAME
FROM C
WHERE NOT EXISTS(
    SELECT `S#`
    FROM S
    WHERE NOT EXISTS(
        SELECT *
        FROM SC
        WHERE SC.`S#` = S.`S#`
            AND SC.`C#` = C.`C#`
            )
    );
-- (4)检索选修课程包含学号为2的学生所修课程的学生学号(S#)。

SELECT DISTINCT SC1.`S#`
FROM SC AS SC1
WHERE NOT EXISTS (
    SELECT *
    FROM SC AS SC2
    WHERE SC2.`S#` = 2
      AND SC2.`C#` NOT IN (
          SELECT SC3.`C#`
          FROM SC AS SC3
          WHERE SC3.`S#` = SC1.`S#`
      )
);

-- (5)检索选修了全部课程的学生的姓名（SNAME）。(没有一门课程不选修)
SELECT SNAME
FROM S
WHERE NOT EXISTS (
    SELECT *
    FROM C
    WHERE NOT EXISTS(
        SELECT *
        FROM SC
        WHERE SC.`S#` = S.`S#` AND SC.`C#` = C.`C#`
        )
    );


-- 2. 创建一个和第一题中S完全一样的表命名为user表，并将上面S表的数据复制到user表中。
-- (1) 创建一个和 S 表结构完全相同的 user 表
CREATE TABLE `user` LIKE S;

-- (2) 将 S 表中的所有数据复制到 user 表
INSERT INTO `user` SELECT * FROM S;

-- 3. 创建如下无限极商品分类表，完成如下查询
CREATE TABLE category (
    id INT PRIMARY KEY,
    cateName VARCHAR(50),
    pId INT
);

-- 2. 插入数据
INSERT INTO category VALUES
(1,'服装',0),
(2,'数码',0),
(3,'箱包',0),
(4,'男装',1),
(5,'女装',1),
(6,'内衣',1),
(7,'电视',2),
(8,'冰箱',2),
(9,'洗衣机',2),
(10,'爱马仕',3),
(11,'LV',3),
(12,'GUCCI',3),
(13,'夹克',4),
(14,'衬衫',4),
(15,'裤子',4),
(16,'液晶电视',7),
(17,'等离子电视',7),
(18,'背投电视',7);


-- (1)查询所有的分类信息，并且得到其父分类；
SELECT a.id,a.cateName,a.pId,b.cateName AS parentName
FROM category a
LEFT JOIN category b ON a.pId=b.Id;

-- (2)查询所有的分类及其子分类；
SELECT  a.id, a.cateName,b.id AS childId,b.cateName AS childName
FROM category a
LEFT JOIN category b ON a.id = b.pId;
-- (3)查询所有的分类并且得到子分类的数目。
SELECT a.id,a.cateName,COUNT(b.id) AS childCount
FROM category a
LEFT JOIN category b ON a.id=b.pId
GROUP BY a.id;