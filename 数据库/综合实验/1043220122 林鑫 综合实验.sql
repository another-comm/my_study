-- (4)为该实例选择mysql数据库管理系统，innodb存储引擎，utf8字符集，使用SQL的DDL语言建表、建库、选择合适的字段类型。
-- 彻底删除并重新创建数据库
DROP DATABASE IF EXISTS library_db;
CREATE DATABASE library_db DEFAULT CHARACTER SET UTF8;
USE library_db;

-- 1. 出版社表：区分 id(存储优化) 与 publisher_name(业务标识)
CREATE TABLE publisher (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '数据库主键ID',
    publisher_name VARCHAR(100) NOT NULL UNIQUE COMMENT '出版社名(业务主键)',
    zip_code CHAR(6) NOT NULL COMMENT '邮编',
    address VARCHAR(200) NOT NULL COMMENT '地址',
    phone VARCHAR(20) NOT NULL COMMENT '电话',
    email VARCHAR(50) NOT NULL COMMENT '电子邮箱'
) ENGINE=INNODB DEFAULT CHARSET=UTF8 COMMENT='出版社表';

-- 2. 借书人表：参考范例 rid 为主键，rcode 为业务证号
CREATE TABLE borrower (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '借书人数据库主键ID',
    card_id CHAR(20) NOT NULL UNIQUE COMMENT '借书证号(业务主键)',
    name VARCHAR(20) NOT NULL COMMENT '姓名',
    organization VARCHAR(100) NOT NULL COMMENT '单位'
) ENGINE=INNODB DEFAULT CHARSET=UTF8 COMMENT='借书人表';

-- 3. 图书表：使用数值类型 publisher_id 进行逻辑关联
CREATE TABLE book (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '图书数据库主键ID',
    title VARCHAR(100) NOT NULL COMMENT '书名',
    count SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '数量',
    location VARCHAR(100) NOT NULL COMMENT '位置',
    publisher_id INT UNSIGNED NOT NULL COMMENT '出版社ID(数值关联)',
    INDEX idx_publisher_id(publisher_id) COMMENT '出版社逻辑关联索引'
) ENGINE=INNODB DEFAULT CHARSET=UTF8 COMMENT='图书表';

-- 4. 借阅表：通过数值 ID 关联图书和借书人
CREATE TABLE borrow (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '借阅记录ID',
    borrower_id INT UNSIGNED NOT NULL COMMENT '借书人ID(逻辑关联)',
    book_id INT UNSIGNED NOT NULL COMMENT '图书ID(逻辑关联)',
    borrow_date DATE NOT NULL COMMENT '借书日期',
    return_date DATE DEFAULT NULL COMMENT '还书日期',
    INDEX idx_borrower_id(borrower_id) COMMENT '借书人索引',
    INDEX idx_book_id(book_id) COMMENT '图书索引'
) ENGINE=INNODB DEFAULT CHARSET=UTF8 COMMENT='借阅记录表';

-- (5)为该数据库创建用户exam1@localhost，密码为111，并授予SELECT权限；为该数据库创建用户exam2@localhost，密码为000，并授予CREATE,INSERT,UPDATE,DELETE权限和GRANT权限。


-- 创建用户 exam1 并授予 SELECT 权限
CREATE USER 'exam1'@'localhost' IDENTIFIED BY '111';
GRANT SELECT ON library_db.* TO 'exam1'@'localhost';

-- 创建用户 exam2 并授予 增删改查、建表 及 授权权限
CREATE USER 'exam2'@'localhost' IDENTIFIED BY '000';
GRANT SELECT, CREATE, INSERT, UPDATE, DELETE ON library_db.* TO 'exam2'@'localhost' WITH GRANT OPTION;

FLUSH PRIVILEGES;

-- （6）. 在出版社电话上创建唯一索引 
CREATE UNIQUE INDEX uk_publisher_phone ON publisher(phone);
-- (7)为每张表插入适当的测试数据。

-- 插入测试数据
-- 1. 插入出版社并获取 ID (假设为 1)
INSERT INTO publisher (publisher_name, zip_code, address, phone, email) 
VALUES ('人民邮电出版社', '100061', '北京市', '010-81055000', 'contact@ptpress.com.cn');

-- 2. 插入借书人，手动指定业务证号
INSERT INTO borrower (card_id, name, organization) VALUES 
('1043220122', '张三', '计算机系'),
('1043220124', '李四', '外语系'),
('1043220125', '王五', '数学系');

-- 3. 插入图书
INSERT INTO book (title, count, location, publisher_id) 
VALUES ('实分析', 10, 'A区01架', 1);

-- 4. 插入借阅记录 (使用自动生成的数据库 ID 进行关联)
-- 假设张三的 ID 为 1，李四的 ID 为 2
INSERT INTO borrow (borrower_id, book_id, borrow_date, return_date) VALUES 
(1, 1, '2025-12-01', '2025-12-10'), 
(2, 1, '2025-12-26', '2026-01-05');

       
-- (8)使用mysqldump备份该数据库。
mysqldump -u root -p library_db > bak_library_db_20251226.sql

-- (9)创建视图定义为显示借书人的借书证号、姓名、所借书的书名、借阅时间和还书时间

CREATE OR REPLACE VIEW v_borrow_info AS
SELECT 
    br.card_id AS '借书证号',
    br.name AS '姓名',
    bk.title AS '书名',
    bw.borrow_date AS '借阅时间',
    bw.return_date AS '还书时间'
FROM borrow AS bw
JOIN borrower AS br ON bw.borrower_id = br.id
JOIN book AS bk ON bw.book_id = bk.id;

-- (10)查询借书人信息的的前2条，然后使用php+html将查询出的结果展示在网页上。

-- 从视图中查询前 2 条完整的借阅记录
SELECT * FROM v_borrow_info LIMIT 2;