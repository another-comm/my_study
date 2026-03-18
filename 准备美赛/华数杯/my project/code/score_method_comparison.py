"""
得分计算方法对比分析
分析用户提供的"参考得分"是如何计算得到的
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 原始数据
data = {
    "Country": ["USA", "China", "UAE", "UK", "France", "South Korea", "Japan", "Germany", "Canada", "India"],
    # 维度一：人才
    "Top_Scholars": [56.4, 24.8, 0.6, 6.1, 4.0, 2.5, 1.7, 3.1, 4.2, 1.8],
    "Total_Prof": [142, 115, 7.2, 39, 26, 19, 27, 32, 21, 88],
    "STEM_Grads": [85, 485, 2.8, 19, 17, 16, 22, 22, 13, 265],
    "Migration_Idx": [0.91, 0.02, 0.96, 0.25, 0.32, -0.01, -0.10, 0.10, 0.45, -0.45],
    "Skill_Pen": [2.2, 1.5, 1.9, 1.8, 1.3, 1.6, 1.1, 1.4, 1.7, 3.3],
    # 维度二：科研
    "Papers": [22.1, 36.5, 0.5, 4.9, 3.6, 3.3, 2.7, 3.9, 3.0, 6.8],
    "FWCI": [1.88, 1.32, 1.25, 1.48, 1.55, 1.18, 1.02, 1.35, 1.65, 0.82],
    "Patents": [3.9, 13.2, 0.09, 0.6, 0.4, 2.2, 1.9, 0.8, 0.3, 1.3],
    # 维度三：基建
    "Compute_EFLOPS": [85.0, 42.0, 15.5, 4.5, 5.2, 8.8, 9.2, 3.8, 2.5, 3.2],
    "Power_MW": [21500, 20800, 6800, 2100, 2200, 3200, 4200, 1650, 1400, 1250],
    "GPU_Stock": [620, 210, 35, 12, 15, 22, 18, 9, 6, 8],
    "5G_Cover": [98.5, 99.2, 97.0, 92.0, 93.0, 99.5, 96.0, 95.0, 91.0, 88.0],
    # 维度四：经济
    "Investment": [105.2, 34.5, 13.8, 8.9, 6.5, 4.2, 3.5, 6.4, 4.8, 4.6],
    "Unicorns": [325, 172, 9, 30, 14, 10, 8, 16, 13, 16],
    "GDP_Contrib": [3.1, 2.9, 3.5, 2.1, 1.8, 2.2, 1.2, 1.7, 1.6, 1.4],
    "Adoption": [65, 75, 62, 48, 45, 51, 38, 55, 42, 68],
    # 维度五：政策
    "Policy_Score": [8.8, 9.7, 9.9, 9.0, 8.2, 8.8, 8.5, 7.8, 8.5, 7.5],
    "Data_Score": [9.4, 8.8, 7.8, 9.0, 8.0, 8.2, 8.0, 7.5, 8.5, 6.8]
}

df = pd.DataFrame(data)
countries = df['Country'].values
numeric_df = df.drop(columns=['Country'])

print("=" * 80)
print("得分计算方法对比分析")
print("=" * 80)

# 参考得分（用户提供）
reference_scores = {
    "USA": 97.2,
    "China": 86.5,
    "UAE": 73.4,
    "UK": 68.2,
    "France": 65.8,
    "South Korea": 64.1,
    "Japan": 61.5,
    "Germany": 59.8,
    "Canada": 57.3,
    "India": 53.6
}

print("\n参考得分（用户提供）：")
print("-" * 80)
for country in countries:
    if country in reference_scores:
        print(f"{country:15s}: {reference_scores[country]:.1f}")

# 方法1：按用户指定的维度权重计算
print("\n" + "=" * 80)
print("方法1：按维度权重计算（30%科研, 25%算力, 20%人才, 15%投资, 10%政策）")
print("=" * 80)

# 定义维度映射和权重
dim_map = {
    "人才": {
        "indicators": ["Top_Scholars", "Total_Prof", "STEM_Grads", "Migration_Idx", "Skill_Pen"],
        "weight": 0.20
    },
    "科研": {
        "indicators": ["Papers", "FWCI", "Patents"],
        "weight": 0.30
    },
    "基建": {
        "indicators": ["Compute_EFLOPS", "Power_MW", "GPU_Stock", "5G_Cover"],
        "weight": 0.25
    },
    "经济": {
        "indicators": ["Investment", "Unicorns", "GDP_Contrib", "Adoption"],
        "weight": 0.15
    },
    "政策": {
        "indicators": ["Policy_Score", "Data_Score"],
        "weight": 0.10
    }
}

# 标准化数据（Min-Max）
normalized_df = (numeric_df - numeric_df.min()) / (numeric_df.max() - numeric_df.min())

# 处理负值（Migration_Idx有负值）
# 对于Migration_Idx，单独处理
if 'Migration_Idx' in numeric_df.columns:
    migration_idx = numeric_df['Migration_Idx'].values
    migration_min = migration_idx.min()
    migration_max = migration_idx.max()
    normalized_migration = (migration_idx - migration_min) / (migration_max - migration_min)
    normalized_df['Migration_Idx'] = normalized_migration

# 计算每个维度的平均得分
dimension_scores = pd.DataFrame()
for dim_name, dim_info in dim_map.items():
    indicators = dim_info['indicators']
    # 计算该维度下各指标的平均标准化得分
    dimension_scores[dim_name] = normalized_df[indicators].mean(axis=1)

print("\n各维度标准化得分（0-1）：")
print(dimension_scores.round(4))

# 按权重计算最终得分（0-100分）
final_scores_method1 = pd.Series(index=countries, dtype=float)
for country_idx, country in enumerate(countries):
    score = 0
    for dim_name, dim_info in dim_map.items():
        score += dimension_scores.loc[country_idx, dim_name] * dim_info['weight']
    final_scores_method1[country] = score * 100

print("\n方法1结果（按维度权重）：")
print("-" * 80)
method1_sorted = final_scores_method1.sort_values(ascending=False)
for country in method1_sorted.index:
    ref_score = reference_scores.get(country, None)
    diff = method1_sorted[country] - ref_score if ref_score else None
    diff_str = f" (差异: {diff:+.1f})" if diff is not None else ""
    print(f"{country:15s}: {method1_sorted[country]:6.2f}{diff_str}")

# 方法2：使用对数变换后再标准化
print("\n" + "=" * 80)
print("方法2：对数变换后标准化（压缩极端值影响）")
print("=" * 80)

# 对原始数据取对数（只对正值，避免负值）
numeric_df_log = numeric_df.copy()
for col in numeric_df_log.columns:
    if numeric_df_log[col].min() > 0:  # 只对全为正值的列取对数
        numeric_df_log[col] = np.log1p(numeric_df_log[col])  # log1p = log(1+x)，避免log(0)

# Migration_Idx单独处理（有负值）
if 'Migration_Idx' in numeric_df_log.columns:
    migration_idx = numeric_df['Migration_Idx'].values
    migration_min = migration_idx.min()
    migration_max = migration_idx.max()
    normalized_migration = (migration_idx - migration_min) / (migration_max - migration_min)
    numeric_df_log['Migration_Idx'] = normalized_migration

# 标准化对数变换后的数据
normalized_df_log = (numeric_df_log - numeric_df_log.min()) / (numeric_df_log.max() - numeric_df_log.min())

# 计算维度得分
dimension_scores_log = pd.DataFrame()
for dim_name, dim_info in dim_map.items():
    indicators = dim_info['indicators']
    dimension_scores_log[dim_name] = normalized_df_log[indicators].mean(axis=1)

# 按权重计算最终得分
final_scores_method2 = pd.Series(index=countries, dtype=float)
for country_idx, country in enumerate(countries):
    score = 0
    for dim_name, dim_info in dim_map.items():
        score += dimension_scores_log.loc[country_idx, dim_name] * dim_info['weight']
    final_scores_method2[country] = score * 100

print("\n方法2结果（对数变换+维度权重）：")
print("-" * 80)
method2_sorted = final_scores_method2.sort_values(ascending=False)
for country in method2_sorted.index:
    ref_score = reference_scores.get(country, None)
    diff = method2_sorted[country] - ref_score if ref_score else None
    diff_str = f" (差异: {diff:+.1f})" if diff is not None else ""
    print(f"{country:15s}: {method2_sorted[country]:6.2f}{diff_str}")

# 方法3：百分位排名法
print("\n" + "=" * 80)
print("方法3：百分位排名法（更均匀的分布）")
print("=" * 80)

# 计算百分位排名（0-100）
percentile_df = numeric_df.copy()
for col in percentile_df.columns:
    # 计算百分位排名
    percentile_df[col] = numeric_df[col].rank(pct=True) * 100

# 归一化到0-1
normalized_percentile = percentile_df / 100

# 计算维度得分
dimension_scores_percentile = pd.DataFrame()
for dim_name, dim_info in dim_map.items():
    indicators = dim_info['indicators']
    dimension_scores_percentile[dim_name] = normalized_percentile[indicators].mean(axis=1)

# 按权重计算最终得分
final_scores_method3 = pd.Series(index=countries, dtype=float)
for country_idx, country in enumerate(countries):
    score = 0
    for dim_name, dim_info in dim_map.items():
        score += dimension_scores_percentile.loc[country_idx, dim_name] * dim_info['weight']
    final_scores_method3[country] = score * 100

print("\n方法3结果（百分位排名+维度权重）：")
print("-" * 80)
method3_sorted = final_scores_method3.sort_values(ascending=False)
for country in method3_sorted.index:
    ref_score = reference_scores.get(country, None)
    diff = method3_sorted[country] - ref_score if ref_score else None
    diff_str = f" (差异: {diff:+.1f})" if diff is not None else ""
    print(f"{country:15s}: {method3_sorted[country]:6.2f}{diff_str}")

# 方法4：当前熵权法（对比）
print("\n" + "=" * 80)
print("方法4：当前熵权法（对比）")
print("=" * 80)

def calculate_entropy_weights(df_norm):
    df_norm = df_norm + 1e-9
    p = df_norm / df_norm.sum(axis=0)
    k = 1 / np.log(len(df_norm))
    e = -k * (p * np.log(p)).sum(axis=0)
    d = 1 - e
    weights = d / d.sum()
    return np.array(weights)

entropy_weights = calculate_entropy_weights(normalized_df)
X_normalized = normalized_df.values
y_entropy = X_normalized @ entropy_weights * 100

print("\n方法4结果（熵权法）：")
print("-" * 80)
entropy_indices = np.argsort(y_entropy)[::-1]
for rank, idx in enumerate(entropy_indices, 1):
    country = countries[idx]
    ref_score = reference_scores.get(country, None)
    diff = y_entropy[idx] - ref_score if ref_score else None
    diff_str = f" (差异: {diff:+.1f})" if diff is not None else ""
    print(f"{country:15s}: {y_entropy[idx]:6.2f}{diff_str}")

# 对比分析
print("\n" + "=" * 80)
print("对比分析总结")
print("=" * 80)

comparison_df = pd.DataFrame({
    '参考得分': [reference_scores.get(c, None) for c in countries],
    '方法1_维度权重': final_scores_method1.values,
    '方法2_对数变换': final_scores_method2.values,
    '方法3_百分位排名': final_scores_method3.values,
    '方法4_熵权法': y_entropy
}, index=countries)

print("\n所有方法对比：")
print(comparison_df.round(2))

# 计算与参考得分的相关性
print("\n与参考得分的相关性（Pearson相关系数）：")
ref_scores_array = np.array([reference_scores.get(c, None) for c in countries])
for method_name, method_scores in [
    ("方法1_维度权重", final_scores_method1.values),
    ("方法2_对数变换", final_scores_method2.values),
    ("方法3_百分位排名", final_scores_method3.values),
    ("方法4_熵权法", y_entropy)
]:
    corr = np.corrcoef(ref_scores_array, method_scores)[0, 1]
    print(f"  {method_name}: {corr:.4f}")

# 计算与参考得分的RMSE
print("\n与参考得分的RMSE（均方根误差）：")
for method_name, method_scores in [
    ("方法1_维度权重", final_scores_method1.values),
    ("方法2_对数变换", final_scores_method2.values),
    ("方法3_百分位排名", final_scores_method3.values),
    ("方法4_熵权法", y_entropy)
]:
    rmse = np.sqrt(np.mean((ref_scores_array - method_scores) ** 2))
    print(f"  {method_name}: {rmse:.2f}")

# 可视化对比
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Score Calculation Methods Comparison", fontsize=16, fontweight="bold")

methods = [
    ("Reference Scores", [reference_scores.get(c, None) for c in countries]),
    ("Method 1: Dimension Weights", final_scores_method1.values),
    ("Method 2: Log Transform", final_scores_method2.values),
    ("Method 3: Percentile Ranking", final_scores_method3.values),
]

for idx, (method_name, method_scores) in enumerate(methods):
    ax = axes[idx // 2, idx % 2]
    sorted_indices = np.argsort(method_scores)[::-1] if method_scores[0] is not None else np.argsort(y_entropy)[::-1]
    sorted_countries = countries[sorted_indices]
    sorted_scores = np.array([method_scores[i] for i in sorted_indices]) if method_scores[0] is not None else y_entropy[sorted_indices]
    
    colors = ['red' if c in ['USA', 'China'] else 'steelblue' for c in sorted_countries]
    ax.barh(range(len(sorted_countries)), sorted_scores, color=colors, alpha=0.7)
    ax.set_yticks(range(len(sorted_countries)))
    ax.set_yticklabels(sorted_countries)
    ax.set_xlabel("Score")
    ax.set_title(method_name)
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim([0, 100])

plt.tight_layout()
plt.savefig('score_method_comparison.png', dpi=300, bbox_inches='tight')
print(f"\n对比图表已保存到: score_method_comparison.png")
plt.show()
