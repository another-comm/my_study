import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

try:
    df = pd.read_csv('juneau_data_processed.csv')
except FileNotFoundError:
    print("错误：未找到 'juneau_data_processed.csv'。请确保已运行第一步的数据预处理脚本。")
    exit()

hpi_data = np.array([
    142.5, 148.2, 155.8, 165.4, 178.9, 201.3, 215.6, 228.4, 235.1, 238.9, 
    242.1, 245.8, 251.2, 258.4, 262.1, 268.5, 275.2, 282.4, 291.8, 305.6, 
    320.1, 358.9, 412.5, 438.2, 455.8
])

if len(df) == len(hpi_data):
    df['HPI'] = hpi_data
else:
    print(f"警告：数据行数不匹配 (CSV: {len(df)}, HPI: {len(hpi_data)})")

cols = ['Visitors_Smoothed', 'Glacier_Retreat', 'Temperature', 'HPI']
labels = ['Visitors ($V$)', 'Glacier Retreat ($G$)', 'Temperature ($T$)', 'Housing Index ($HPI$)']

corr_matrix = df[cols].corr(method='pearson')
corr_matrix.columns = labels
corr_matrix.index = labels

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(7, 6), dpi=300)

sns.heatmap(
    corr_matrix, 
    annot=True,
    fmt=".2f",
    cmap='RdBu_r',
    center=0,
    vmin=-1, vmax=1,
    square=True,
    linewidths=1.5,
    linecolor='white',
    cbar_kws={"shrink": 0.8, "label": "Pearson Correlation Coefficient ($r$)"},
    annot_kws={"size": 12, "weight": "bold"}
)

plt.title('Correlation Matrix of Key Variables', fontsize=14, weight='bold', pad=20)
plt.xticks(rotation=45, ha='right', fontsize=11)
plt.yticks(rotation=0, fontsize=11)

plt.tight_layout()
plt.savefig('nature_correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.savefig('nature_correlation_matrix.pdf', bbox_inches='tight')

print("------------------------------------------------")
print("相关性分析结果 (Correlation Matrix):")
print(corr_matrix)
print("\n图表已保存为: nature_correlation_matrix.png")
print("------------------------------------------------")
print("分析提示：")
print("1. 观察 V 与 G 的相关系数：如果接近 1，说明游客增长与冰川退缩高度同步（但不代表因果）。")
print("2. 观察 V 与 HPI 的相关系数：这反映了旅游业对本地生活成本的潜在压力。")
