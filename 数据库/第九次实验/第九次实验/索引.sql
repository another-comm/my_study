CREATE TABLE provinces(
id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY key,
pname VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE users(
id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY key,
username VARCHAR(10) NOT NULL,
sex ENUM('男','女'),
age TINYINT,
email VARCHAR(50),
pid SMALLINT UNSIGNED,
FOREIGN KEY (pid) REFERENCES provinces (id),
INDEX index_name(username)
);

INSERT provinces(pname) VALUES('江苏'),
                              ('浙江'),
                              ('北京'),
                              ('上海'),
                              ('湖南'),
                              ('广东'),
                              ('河北'),
                              ('广西'),
                              ('海南');
INSERT users(username,sex,age,email,pid)Values('king','男',23,'45632@qq.com',1),
                                              ('queen','女',19,'29780909@qq.com',3),
                                              ('rose','女',20,'9773647785@qq.com',4),
                                              ('mike','男',22,'86778634@qq.com',5),
                                              ('linda','女',24,'67563845@qq.com',7),
                                              ('amy','女',28,'dfeioet@163.com',6);

--1 查看索引
SHOW INDEX FROM users\G
SHOW INDEX FROM provinces\G
/*
        Table: users        （ 表名称）
   Non_unique: 0            （索引能不能包括重复词，不能为0，能则为1）
     Key_name: PRIMARY      （索引名称）
 Seq_in_index: 1            （索引中的列序号，从1开始）
  Column_name: id           （列名称）
    Collation: A             (列以什么方式存储在索引中。A表示升序或NULL无分类)
  Cardinality: 6            （索引中唯一值的数目的估计值）
     Sub_part: NULL         （如果列只是部分地被编入索引，则为被编入索引的字符的数目）
       Packed: NULL         （指关键字如何被压缩，如果没有被压缩，则为NULL）
         Null:               (如果列含有null，则显示YES,否则不显示)
   Index_type: BTREE        （索引类型：BTREE,HASH)
      Comment:               (评注)
Index_comment:

*/


--2 创建索引
--（1）普通索引

--在users表上为username字段创建长度为5的，名为index_name5的索引
CREATE INDEX index_name5 ON users(username(5));

--查看mysql执行计划
EXPLAIN SELECT * FROM users WHERE username='king'\G

--强制使用index_name5来执行查询
SELECT * FROM users USE INDEX FOR JOIN(index_name5) WHERE username='king';

--查看执行计划
EXPLAIN SELECT * FROM users USE INDEX FOR JOIN(index_name5) WHERE username='king'\G

--在provinces上为pname字段创建普通索引。
ALTER TABLE provinces ADD INDEX index_name ( pname);



--（2）唯一索引 （主键约束和唯一约束上的字段会自动添加唯一索引）
CREATE UNIQUE INDEX index_age ON users(age);

--（3）全文索引（fulltext index)——只能加在char,varchar,text类型的字段上
CREATE FULLTEXT INDEX index_email ON users(email);

--（4）多列索引（联合索引）
CREATE INDEX index_name_age ON users(username,age);

--3 删除索引
DROP INDEX index_name5 ON users;
ALTER TABLE users DROP INDEX index_age;
