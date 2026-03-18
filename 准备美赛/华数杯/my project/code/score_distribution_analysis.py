"""
得分分布分析：解释为什么美国和中国的得分远高于其他国家
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 读取原始数据
data = {
    "Country": ["USA", "China", "UAE", "UK", "France", "South Korea", "Japan", "Germany", "Canada", "India"],
    "Top_Scholars": [56.4, 24.8, 0.6, 6.1, 4.0, 2.5, 1.7, 3.1, 4.2, 1.8],
    "Total_Prof": [142, 115, 7.2, 39, 26, 19, 27, 32, 21, 88],
    "STEM_Grads": [85, 485, 2.8, 19, 17, 16, 22, 22, 13, 265],
    "Migration_Idx": [0.91, 0.02, 0.96, 0.25, 0.32, -0.01, -0.10, 0.10, 0.45, -0.45],
    "Skill_Pen": [2.2, 1.5, 1.9, 1.8, 1.3, 1.6, 1.1, 1.4, 1.7, 3.3],
    "Papers": [22.1, 36.5, 0.5, 4.9, 3.6, 3.3, 2.7, 3.9, 3.0, 6.8],
    "FWCI": [1.88, 1.32, 1.25, 1.48, 1.55, 1.18, 1.02, 1.35, 1.65, 0.82],
    "Patents": [3.9, 13.2, 0.09, 0.6, 0.4, 2.2, 1.9, 0.8, 0.3, 1.3],
    "Compute_EFLOPS": [85.0, 42.0, 15.5, 4.5, 5.2, 8.8, 9.2, 3.8, 2.5, 3.2],
    "Power_MW": [21500, 20800, 6800, 2100, 2200, 3200, 4200, 1650, 1400, 1250],
    "GPU_Stock": [620, 210, 35, 12, 15, 22, 18, 9, 6, 8],
    "5G_Cover": [98.5, 99.2, 97.0, 92.0, 93.0, 99.5, 96.0, 95.0, 91.0, 88.0],
    "Investment": [105.2, 34.5, 13.8, 8.9, 6.5, 4.2, 3.5, 6.4, 4.8, 4.6],
    "Unicorns": [325, 172, 9, 30, 14, 10, 8, 16, 13, 16],
    "GDP_Contrib": [3.1, 2.9, 3.5, 2.1, 1.8, 2.2, 1.2, 1.7, 1.6, 1.4],
    "Adoption": [65, 75, 62, 48, 45, 51, 38, 55, 42, 68],
    "Policy_Score": [8.8, 9.7, 9.9, 9.0, 8.2, 8.8, 8.5, 7.8, 8.5, 7.5],
    "Data_Score": [9.4, 8.8, 7.8, 9.0, 8.0, 8.2, 8.0, 7.5, 8.5, 6.8]
}

df = pd.DataFrame(data)
countries = df['Country'].values
numeric_df = df.drop(columns=['Country'])

print("=" * 80)
print("问题诊断：为什么美国和中国的得分远高于其他国家？")
print("=" * 80)

# 1. 检查原始数据的分布
print("\n1. 原始数据分布特征分析")
print("-" * 80)

# 计算每个指标的最大值/最小值比例（离散度）
disparity_ratios = {}
for col in numeric_df.columns:
    max_val = numeric_df[col].max()
    min_val = numeric_df[col].min()
    ratio = max_val / min_val if min_val > 0 else float('inf')
    disparity_ratios[col] = {
        'max': max_val,
        'min': min_val,
        'ratio': ratio,
        'max_country': countries[numeric_df[col].argmax()],
        'min_country': countries[numeric_df[col].argmin()]
    }

# 找出离散度最大的指标
disparity_df = pd.DataFrame(disparity_ratios).T
disparity_df = disparity_df.sort_values('ratio', ascending=False)

print("\n离散度最大的前10个指标（最大值/最小值）：")
print(disparity_df[['max', 'min', 'ratio', 'max_country', 'min_country']].head(10))

# 2. 标准化后的数据分布
print("\n2. Min-Max标准化后的数据分布")
print("-" * 80)
normalized_df = (numeric_df - numeric_df.min()) / (numeric_df.max() - numeric_df.min())

# 计算每个国家的平均标准化得分
country_avg_normalized = normalized_df.mean(axis=1)
print("\n各国平均标准化得分（标准化后各指标的均值）：")
for i, country in enumerate(countries):
    print(f"{country:15s}: {country_avg_normalized.iloc[i]:.4f}")

# 3. 计算熵权法得分
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

print("\n3. 熵权法最终得分")
print("-" * 80)
print("\n排名\t国家\t\t得分\t\t与第1名差距")
sorted_indices = np.argsort(y_entropy)[::-1]
for rank, idx in enumerate(sorted_indices, 1):
    gap = y_entropy[sorted_indices[0]] - y_entropy[idx]
    print(f"{rank}\t{countries[idx]:15s}\t{y_entropy[idx]:.2f}\t\t{gap:.2f}")

# 4. 分析关键指标的贡献
print("\n4. 关键指标对最终得分的贡献分析")
print("-" * 80)

# 找出权重最大的指标
weight_df = pd.DataFrame({
    'Indicator': numeric_df.columns,
    'Weight': entropy_weights
}).sort_values('Weight', ascending=False)

print("\n权重最大的前10个指标：")
print(weight_df.head(10).to_string(index=False))

# 计算每个国家在这些高权重指标上的表现
top5_indicators = weight_df.head(5)['Indicator'].values
print(f"\n前5大权重指标：{', '.join(top5_indicators)}")

print("\n各国在前5大权重指标上的标准化得分：")
top5_scores = normalized_df[top5_indicators]
for i, country in enumerate(countries):
    avg_top5 = top5_scores.iloc[i].mean()
    print(f"{country:15s}: {avg_top5:.4f}")

# 5. 根本原因分析
print("\n" + "=" * 80)
print("根本原因分析")
print("=" * 80)

print("\n【原因1】原始数据存在极端差距")
print("-" * 80)
print("例如：")
print(f"  - Unicorns: 美国{data['Unicorns'][0]} vs 阿联酋{data['Unicorns'][2]}，差距 {data['Unicorns'][0]/data['Unicorns'][2]:.1f}倍")
print(f"  - Investment: 美国{data['Investment'][0]} vs 加拿大{data['Investment'][8]}，差距 {data['Investment'][0]/data['Investment'][8]:.1f}倍")
print(f"  - Power_MW: 美国{data['Power_MW'][0]} vs 加拿大{data['Power_MW'][8]}，差距 {data['Power_MW'][0]/data['Power_MW'][8]:.1f}倍")

print("\n【原因2】Min-Max标准化放大差距")
print("-" * 80)
print("Min-Max标准化公式：(x - min) / (max - min)")
print("当原始数据差距很大时：")
print("  - 最大值国家 → 标准化后接近 1.0")
print("  - 最小值国家 → 标准化后接近 0.0")
print("  - 中间国家 → 标准化后在 0.0-1.0 之间，但往往集中在低端")

print("\n【原因3】熵权法关注方差大的指标")
print("-" * 80)
print("熵权法的特点：")
print("  - 数据离散度越大的指标，权重越高")
print("  - 美中占优的指标（如Unicorns, Investment）权重很高")
print("  - 其他国家在这些高权重指标上得分接近0，导致最终得分很低")

print("\n【原因4】线性加权组合")
print("-" * 80)
print("最终得分 = Σ(标准化值 × 权重)")
print("如果某国在多个高权重指标上都接近0，最终得分自然很低")

# 6. 这是问题还是真实反映？
print("\n" + "=" * 80)
print("结论：这是数学上的正常现象，还是需要调整？")
print("=" * 80)

print("\n✅ 如果这是真实的AI发展能力差距，则结果是合理的：")
print("  - 美国和中国的AI发展确实远超其他国家")
print("  - 这种两极分化在现实中确实存在")
print("  - 模型准确反映了数据的客观特征")

print("\n⚠️  如果希望得分更均匀分布（例如便于排名展示），可以考虑：")
print("  1. 使用对数变换标准化")
print("  2. 使用百分位排名代替Min-Max标准化")
print("  3. 对指标进行对数变换后再标准化")
print("  4. 使用等权重代替熵权法（但这会丢失客观权重信息）")

# 可视化
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Why Are the Top Scores So High? (Distribution Analysis)", fontsize=16, fontweight="bold")

# 图1: 原始数据分布（选择几个关键指标）
ax1 = axes[0, 0]
key_indicators = ['Unicorns', 'Investment', 'Power_MW', 'GPU_Stock']
for indicator in key_indicators:
    ax1.plot(range(len(countries)), numeric_df[indicator], 'o-', label=indicator, alpha=0.7)
ax1.set_xticks(range(len(countries)))
ax1.set_xticklabels(countries, rotation=45, ha='right')
ax1.set_title("Raw Data Distribution (Key Indicators)")
ax1.set_ylabel("Raw Value")
ax1.legend()
ax1.grid(True, alpha=0.3)

# 图2: 标准化后的数据分布
ax2 = axes[0, 1]
for indicator in key_indicators:
    ax2.plot(range(len(countries)), normalized_df[indicator], 'o-', label=indicator, alpha=0.7)
ax2.set_xticks(range(len(countries)))
ax2.set_xticklabels(countries, rotation=45, ha='right')
ax2.set_title("Distribution After Min-Max Normalization")
ax2.set_ylabel("Normalized Value (0–1)")
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_ylim([0, 1])

# 图3: 权重分布
ax3 = axes[1, 0]
top10_weights = weight_df.head(10)
ax3.barh(range(len(top10_weights)), top10_weights['Weight'], color='steelblue')
ax3.set_yticks(range(len(top10_weights)))
ax3.set_yticklabels(top10_weights['Indicator'])
ax3.set_xlabel("Entropy Weight")
ax3.set_title("Top 10 Indicator Weights")
ax3.grid(True, alpha=0.3, axis='x')

# 图4: 最终得分
ax4 = axes[1, 1]
sorted_scores = y_entropy[sorted_indices]
sorted_countries = countries[sorted_indices]
colors = ['red' if c in ['USA', 'China'] else 'steelblue' for c in sorted_countries]
ax4.barh(range(len(sorted_countries)), sorted_scores, color=colors, alpha=0.7)
ax4.set_yticks(range(len(sorted_countries)))
ax4.set_yticklabels(sorted_countries)
ax4.set_xlabel("Final Score")
ax4.set_title("Final Score Ranking by Country")
ax4.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('score_distribution_analysis.png', dpi=300, bbox_inches='tight')
print(f"\n分析图表已保存到: score_distribution_analysis.png")
plt.show()
