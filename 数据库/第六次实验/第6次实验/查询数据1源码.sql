-- 测试查询操作
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

-- 查询表中所有记录
SELECT * FROM user;

-- username,addr,age
SELECT username,addr,age FROM user;

-- 查询mysql数据库下user表中的所有记录
SELECT * FROM mysql.user;

-- 查询user表中的id 编号 username 用户名 sex 性别
SELECT id AS '编号',username AS '用户名', sex AS '性别'
FROM user;



-- 给表起别名
SELECT id,username FROM user AS u;

-- 测试表名.字段名
SELECT user.id,user.username,user.age FROM user ;

SELECT u.id,u.username,u.addr,u.sex FROM user AS u;

-- 测试WHERE 条件的比较运算符
-- 查询id,username,age id=5的用户
SELECT id,username,age FROM user
WHERE id=5;

SELECT id,username,age FROM user
WHERE id=50;

-- 添加desc字段 VARCHAR(100)
ALTER TABLE user
ADD userDesc VARCHAR(100);

-- 更新id<=9的用户 userDesc='this is a test'

UPDATE user SET userDesc='this is a test'
WHERE id<=9;

-- 查询用户userDesc 为NULL的用户
SELECT id,username,age,userDesc FROM user
WHERE userDesc=NULL;(错误)

-- 检测NULL值
SELECT id,username,age,userDesc FROM user
WHERE userDesc<=>NULL;
SELECT id,username,age,userDesc FROM user
WHERE userDesc  IS NULL;
-- IS [NOT] NULL检测NULL值
SELECT id,username,age,userDesc FROM user
WHERE userDesc IS NOT NULL;

-- 测试范围BETWEEN AND
-- 查询年龄在18~30之间的用户
SELECT id,username,age,sex FROM user
WHERE age BETWEEN 18 AND 30;

-- 查询薪水在10000~50000之间的用户
SELECT id,username,age,salary FROM user
WHERE salary BETWEEN 10000 AND 50000;

SELECT id,username,age,salary FROM user
WHERE salary NOT BETWEEN 10000 AND 50000;

-- 测试指定集合 IN

-- 查询编号为1,3,5,7,9
SELECT id,username,age FROM user
WHERE id IN(1,3,5,7,9);

SELECT id,username,age FROM user
WHERE username IN('king','queen','lily','rose');

-- 测试逻辑运算符
-- 查询性别为男并且年龄>=20的用户
SELECT id,username,age,sex FROM user
WHERE sex='男' AND age>=20;

-- id>=5 && age<=30
SELECT id,username,age,sex FROM user
WHERE id>=5 AND age<=30;

SELECT id,username,age,sex FROM user
WHERE id>=5 AND age<=30 AND sex='男';

-- 要求sex='女' 并且 addr='北京'
SELECT id,username,age,sex,addr FROM user
WHERE sex='女' AND addr='北京';

-- 查询薪水范围在60000~10000并且性别为男 addr='北京'
SELECT id,username,age,sex,salary,addr FROM user
WHERE salary BETWEEN 60000 AND 100000 AND sex='男' AND addr='北京';

-- 查询id=1 或者 用户名为queen

SELECT id,username,age FROM user
WHERE id=1 OR username='queen';

-- 测试模糊查询
SELECT id,username,age FROM user
WHERE username='king';

SELECT id,username,age FROM user
WHERE username LIKE 'king';

-- 要求用户名中包含三
SELECT id,username,age,sex FROM user
WHERE username LIKE '%三%';

-- 用户名中包含In
SELECT id,username,age FROM user
WHERE username LIKE '%in%';

-- 要求查询出姓张的用户
SELECT id,username,age FROM user
WHERE username LIKE '张%';

-- 查询以风结尾的用户
SELECT id,username,age FROM user
WHERE username LIKE '%风';


-- 用户名长度为三位的用户
SELECT id,username,age,sex FROM user
WHERE username LIKE '___';

SELECT id,username,age,sex FROM user
WHERE username LIKE '张_';

SELECT id,username,age,sex FROM user
WHERE username LIKE '张_%';

 