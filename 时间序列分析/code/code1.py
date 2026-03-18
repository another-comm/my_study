#!/usr/bin/env python
# coding: utf-8

# In[66]:


import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

# 设置中文字体为黑体，解决中文显示问题
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  
matplotlib.rcParams['axes.unicode_minus'] = False 

# 1.读取数据
file_path = r"C:\study\时间序列分析\时间序列分析——部分习题数据\A1_1.xlsx"
yields = pd.read_excel(file_path, sheet_name=0, parse_dates=True, index_col=0)
print("数据预览")
print(yields.head())

# 给索引命名，导出时在 Excel 里显示“日期”
yields.index.name = "日期"

# 2.画时序图
plt.figure(figsize=(15,4), dpi=100)
yields.plot(title="原始时序图")
plt.ylabel("value")
plt.grid(True)
plt.show()

# 3.序列变换（对数）
yields_log = np.log(yields)
plt.figure(figsize=(15,4), dpi=100)
yields_log.plot(title="对数变换后的序列")
plt.show()

# 4.差分运算
yields_diff = yields.diff().dropna()
plt.figure(figsize=(15,4), dpi=100)
yields_diff.plot(title="一阶差分序列")
plt.show()

# 5.生成子序列(1920年之后的数据)
sub_series = yields[yields.index >= "1920-01-01"]
print("子序列预览: ")
print(sub_series.head())

# 6.生成低频序列（年度均值）
low_freq = yields.resample("YE").mean()
plt.figure(figsize=(15,4), dpi=100)
low_freq.plot(title="年度平均序列")
plt.show()

# 7.缺失值插补（线性插值）
yields_missing = yields.copy()
yields_missing.iloc[5:10] = np.nan  # 人为制造缺失
print("含缺失值：")
print(yields_missing.head(12))

yields_filled = yields_missing.interpolate(method="linear")
print("插补后的数据：")
print(yields_filled.head(12))

# 8. 数据导出（带日期索引）
with pd.ExcelWriter(
    r"C:\study\时间序列分析\时间序列分析——部分习题数据\yields_filled.xlsx",
    datetime_format="yyyy-mm-dd"
) as writer:
    yields_filled.to_excel(writer, index=True)

# 9. 生成图片并保存
plt.figure(figsize=(8, 4))
plt.plot(yields, label="原始数据")
plt.plot(yields_log, label="对数变换")
plt.legend()
plt.title("时序图对比")
plt.savefig(r"C:\study\时间序列分析\时间序列分析——部分习题数据\time_series.png", dpi=300)
plt.close()



# In[ ]:




