-- 测试分组
-- 按照性别分组sex
SELECT id,username,age,sex FROM user
GROUP BY sex;

-- 按照addr分组
SELECT username,age,sex,addr FROM user
GROUP BY addr;

-- 按照性别分组，查询组中的用户名有哪些
SELECT GROUP_CONCAT(username),age,sex,addr FROM user
GROUP BY sex;

SELECT GROUP_CONCAT(username),age,sex,GROUP_CONCAT(addr) FROM user
GROUP BY sex;

-- 测试COUNT()
SELECT COUNT(*) FROM user;

SELECT COUNT(id) FROM user;

-- 按照sex分组，得到用户名详情，并且分别组中的总人数
SELECT sex,GROUP_CONCAT(username) AS usersDetail,COUNT(*) AS totalUsers FROM user
GROUP BY sex;

-- 按照addr分组，得到用户名的详情，总人数，得到组中年龄的总和，年龄的最大值、最小值、平均值和
SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(age) AS sum_age,
MAX(age) AS max_age,
MIN(age) AS min_age,
AVG(age) AS avg_age
FROM user
GROUP BY addr;

-- 按照sex分组，统计组中总人数、用户名详情，得到薪水总和，薪水最大值、最小值、平均值
SELECT sex,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(salary) AS sum_salary,
MAX(salary) AS max_salary,
MIN(salary) AS min_salary,
AVG(salary) AS avg_salary
FROM user
GROUP BY sex;

SELECT GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers
FROM user
GROUP BY sex
WITH ROLLUP;

-- 按照字段的位置来分组
SELECT id,sex,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(salary) AS sum_salary,
MAX(salary) AS max_salary,
MIN(salary) AS min_salary,
AVG(salary) AS avg_salary
FROM user
GROUP BY 2;

-- 查询age>=30的用户并且按照sex分组
SELECT sex,GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers
FROM user
WHERE age>=30
GROUP BY sex;

-- 按照addr分组，统计总人数
SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers
FROM user
GROUP BY addr;

-- 对于分组结果进行二次筛选，条件是组中总人数>=3
SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers
FROM user
GROUP BY addr
HAVING COUNT(*)>=3;

SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers
FROM user
GROUP BY addr
HAVING totalUsers>=3;

-- 按照addr分组，
SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(salary) AS sum_salary,
MAX(salary) AS max_salary,
MIN(salary) AS min_salary,
AVG(salary) AS avg_salary
FROM user
GROUP BY addr;

-- 要求平均薪水>=40000
SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(salary) AS sum_salary,
MAX(salary) AS max_salary,
MIN(salary) AS min_salary,
AVG(salary) AS avg_salary
FROM user
GROUP BY addr
HAVING avg_salary>=40000;

-- 测试排序
-- 按照id降序排列
SELECT id,username,age
FROM user
ORDER BY id DESC;

-- 按照age升序
SELECT id,username,age
FROM user
ORDER BY age ;

-- 按照多个字段排序
SELECT id,username,age
FROM user
ORDER BY age ASC,id ASC;

-- 测试条件+排序
SELECT id,username,age
FROM user
WHERE age>=30;

SELECT id,username,age
FROM user
WHERE age>=30
ORDER BY age DESC;

-- 实现随机记录
SELECT id,username,age
FROM user
ORDER BY RAND();

-- 测试LIMIT语句
-- 显示结果集的前5条记录
SELECT id,username,age,sex
FROM user
LIMIT 5;

SELECT id,username,age,sex
FROM user
LIMIT 0,5;

-- 显示前3条记录
SELECT id,username,age,sex
FROM user
LIMIT 0,3;

SELECT id,username,age,sex
FROM user
LIMIT 3,3;

-- 更新前3条记录，将age+5
UPDATE user SET age=age+5 LIMIT 3;

-- 按照id降序排列，更新前三条记录，将age-10
UPDATE user SET age=age-10 ORDER BY id DESC LIMIT 3;

-- 删除前三条记录

DELETE FROM user
LIMIT 3;

DELETE FROM user
ORDER BY id DESC
LIMIT 3;

-- 测试完整SELECT 语句的形式
SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(age) AS sum_age,
MAX(age) AS max_age,
MIN(age) AS min_age,
AVG(age) AS avg_age
FROM user1
WHERE id>=2
GROUP BY addr;

SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(age) AS sum_age,
MAX(age) AS max_age,
MIN(age) AS min_age,
AVG(age) AS avg_age
FROM user1
WHERE id>=2
GROUP BY addr
HAVING totalUsers>=2;


SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(age) AS sum_age,
MAX(age) AS max_age,
MIN(age) AS min_age,
AVG(age) AS avg_age
FROM user1
WHERE id>=2
GROUP BY addr
HAVING totalUsers>=2
ORDER BY totalUsers ASC;

SELECT addr,
GROUP_CONCAT(username) AS usersDetail,
COUNT(*) AS totalUsers,
SUM(age) AS sum_age,
MAX(age) AS max_age,
MIN(age) AS min_age,
AVG(age) AS avg_age
FROM user1
WHERE id>=2
GROUP BY addr
HAVING totalUsers>=2
ORDER BY totalUsers ASC
LIMIT 0,2;
