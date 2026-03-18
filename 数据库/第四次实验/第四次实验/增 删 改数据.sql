-- 测试添加记录
CREATE DATABASE IF NOT EXISTS king DEFAULT CHARACTER SET 'UTF8';
USE king;
CREATE TABLE IF NOT EXISTS user(
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '编号',
    username VARCHAR(20) NOT NULL UNIQUE COMMENT '用户名',
    age TINYINT UNSIGNED DEFAULT 18 COMMENT '年龄',
    email VARCHAR(50) NOT NULL DEFAULT 'imooc@qq.com' COMMENT '邮箱'
)ENGINE=INNODB CHARSET=UTF8;

-- 不指定字段名称
INSERT user VALUES(1,24,'king','382771946@qq.com');
INSERT user VALUES(NULL,'queen',25,'queen@qq.com');
INSERT user VALUES(DEFAULT,'lily',26,'lily@qq.com');

-- 列出指定字段的形式
INSERT user(username,email) VALUES('rose','rose@qq.com');
INSERT user(age,email,id,username) VALUES(34,'imooc@qq.com',5,'imooc');

-- 一次插入3条记录
INSERT user VALUES(NULL,'a',DEFAULT,DEFAULT),
(NULL,'b',56,'b@qq.com'),
(NULL,'c',14,'c@qq.com');

-- INSERT ...SET 的形式
INSERT user SET username='d',age=45,email='d@qq.com';

-- INSERT SELECT
INSERT user(username) SELECT username FROM member.info WHERE id>3;
-- 测试更新语句
-- 修改第一个用户的信息 id=1
UPDATE user SET age=29 WHERE id=1;

-- 修改id=3的用户，username age email
UPDATE user SET age=47,email='lilys@qq.com',username='lilys' WHERE id=3;

-- 所有用户年龄+10
UPDATE user SET age=age+10;

-- 将id<=5的用户年龄改为-10，将邮箱改为默认值
UPDATE user SET age=age-10,email=DEFAULT WHERE id<=5;

-- 测试删除语句
-- 删除用户名为king
DELETE FROM user WHERE username='king';

-- 删除年龄为24的用户
DELETE FROM user WHERE age=24;

-- 删除表中所有记录
DELETE FROM user;

INSERT user VALUES(NULL,'queen',25,'queen@qq.com');
INSERT user VALUES(DEFAULT,'lily',26,'lily@qq.com');

--重置auto
-- 1.
-- 直接重置autoIncrement的值 ALTER TABLE table_name AUTO_INCREMENT =1;

ALTER TABLE user AUTO_INCREMENT=1;
INSERT INTO user(username,age)VALUES('kitty',20);
-- 2.
-- 通过truncate table 完成 TRUNCATE TABLE table_name;
TRUNCATE TABLE user;