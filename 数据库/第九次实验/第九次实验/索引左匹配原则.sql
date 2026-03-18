
--最左前缀原理
--情况一：全列匹配
EXPLAIN SELECT * FROM titles WHERE emp_no='10001' AND title='Senior Engineer' AND from_date='1986-06-26'\G

EXPLAIN SELECT * FROM titles WHERE from_date='1986-06-26'AND title='Senior Engineer' AND emp_no='10001' \G

--情况二 ：最左前缀匹配
EXPLAIN SELECT * FROM titles WHERE emp_no='10001'\G

--情况三：查询条件用到了索引中列的精确匹配，但中间某个条件未提供
EXPLAIN SELECT * FROM titles WHERE emp_no='10001'AND from_date='1986-06-26'\G


--情况四：查询条件中没有指定索引第一列
EXPLAIN SELECT * FROM titles WHERE from_date='1986-06-26' \G

--情况五：匹配某列的前缀字符串
EXPLAIN SELECT * FROM titles WHERE emp_no='10001' AND title='Senior%' \G

--情况六：范围查询
EXPLAIN SELECT * FROM titles WHERE emp_no<'10001' AND title='Senior Engineer'\G

--情况七：查询条件中含有函数或表达式
EXPLAIN SELECT * FROM titles WHERE emp_no<'10001' AND left(title,6)='Senior'\G
EXPLAIN SELECT * FROM titles WHERE emp_no-1='10000'\G

