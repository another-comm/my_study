-- 1）将grade表的course字段的数据类型改为VARCHAR(20).
ALTER TABLE grade MODIFY Course VARCHAR(20);

-- 2）将grade表的Uid字段的位置改到course字段的前面。(改到Cid后面)
ALTER TABLE grade MODIFY Uid INT NOT NULL AFTER Cid;

-- 3）将grade字段改名为score。
ALTER TABLE grade CHANGE Grade Score SMALLINT;

-- 4）删除grade表的外键约束
SHOW CREATE TABLE grade;          -- 找到外键名称为grade_ibfk_1
ALTER TABLE grade DROP FOREIGN KEY grade_ibfk_1;

-- 5）将grade表的存储引擎改为MYISAM类型。
ALTER TABLE grade ENGINE=MYISAM;

-- 6）将student表的address字段删除。
ALTER TABLE student DROP address;

-- 7）在student表中增加名为phone的字段。
ALTER TABLE student ADD phone VARCHAR(20);

-- 8）给 student表的sex字段添加默认值女。
ALTER TABLE student ALTER sex SET DEFAULT '女';

-- 9）将grade表名改为gradeinfo。
ALTER TABLE grade RENAME TO gradeinfo;

-- 10）删除student表。
DROP TABLE IF EXISTS student;


-- 创建food表
CREATE TABLE Food (
    id INT PRIMARY KEY AUTO_INCREMENT  COMMENT '食品编号',
    Name VARCHAR(20) NOT NULL COMMENT '食品名称',
    Company VARCHAR(30) NOT NULL COMMENT '生产厂商',
    Price FLOAT NOT NULL COMMENT '价格（单位：元）',
    Product_time YEAR COMMENT '生产年份',
    Validity_time INT COMMENT '保质期（单位：年）',
    address VARCHAR(50) COMMENT '厂址'
) ENGINE=INNODB CHARSET=utf8mb4;

-- 1）采用三种方式，将表的记录插入到Food表中。
-- 方法一：不指定具体的字段，插入数据：’QQ饼干’,’QQ饼干厂’,2.5,’2017’,3,’北京’。
INSERT Food VALUES (NULL, 'QQ饼干', 'QQ饼干厂', 2.5, '2017', 3, '北京');

-- 方法二：依次指定Food表的字段，插入数据：’MN牛奶’,’MN牛奶厂’,3.5,’2019’,1,’北京河北’。
INSERT Food (Name, Company, Price, Product_time, Validity_time, address)
VALUES ('MN牛奶', 'MN牛奶厂', 3.5, '2019', 1, '北京河北');

-- 方法三：同时插入多条记录，插入数据：
-- ’EF果冻’,’EF果冻厂’,1.5,’2018’,2,’北京’,
-- ’FF咖啡’,’FF咖啡厂’,20,’2017’,5,’天津’，
-- ’GG奶糖’,’ GG奶糖厂’,14,’2016’,2,’广东’；
INSERT Food (Name, Company, Price, Product_time, Validity_time, address) VALUES
('EF果冻', 'EF果冻厂', 1.5, '2018', 2, '北京'),
('FF咖啡', 'FF咖啡厂', 20, '2017', 5, '天津'),
('GG奶糖', 'GG奶糖厂', 14, '2016', 2, '广东');

-- 2) 将“MN牛奶厂”的厂址（address）改为“内蒙古”，并且将价格改为3.2.
UPDATE Food SET address = '内蒙古', Price=3.2 WHERE Company = 'MN牛奶厂';

-- 3 将厂址在北京的公司的保质期（Validity_time）都改为5年。
UPDATE Food SET Validity_time = 5 WHERE address = '北京';

-- 4）删除厂址为“北京”的食品记录。
DELETE FROM Food WHERE address = '北京';