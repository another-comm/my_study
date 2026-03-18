import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os

# 定义两种标准化方法（5维度汇总）
normalization_methods = {
    "minmax": "Min-Max Normalization",
    "sigmoid": "Sigmoid Normalization (Logistic Mapping)",
}

# 定义维度映射
dim_map = {
    "Talent": ["Top_Scholars", "Total_Prof", "STEM_Grads", "Migration_Idx", "Skill_Pen"],
    "Research": ["Papers", "FWCI", "Patents"],
    "Infrastructure": ["Compute_EFLOPS", "Power_MW", "GPU_Stock", "5G_Cover"],
    "Economy": ["Investment", "Unicorns", "GDP_Contrib", "Adoption"],
    "Policy": ["Policy_Score", "Data_Score"]
}

# Use a common font fallback for English plots
plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

print("=" * 80)
print("相关性分析 - 5维度（两种标准化方法对比）")
print("=" * 80)

# 循环处理两种标准化方法（5维度文件）
for method_key, method_name in normalization_methods.items():
    excel_filename = f"normalized_data_{method_key}_5dims.xlsx"
    
    print(f"\n{'='*80}")
    print(f"方法: {method_name} ({method_key})")
    print(f"{'='*80}")
    
    if not os.path.exists(excel_filename):
        print(f"⚠️  未找到标准化数据文件: {excel_filename}")
        print(f"   请先运行 EWM_Analysis.py 生成标准化数据。")
        continue
    
    print(f"正在从 {excel_filename} 读取 5 维度得分数据...")
    df = pd.read_excel(excel_filename, sheet_name='五维度得分')
    print(f"成功读取数据: {df.shape[0]} 个国家, 5 个维度 + Total")
    
    dims = ["Talent", "Research", "Infrastructure", "Economy", "Policy"]
    df_dims = df[dims]
    
    # 计算维度间的相关性
    dim_corr = df_dims.corr()
    
    # --- 绘图部分 ---
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    sns.heatmap(dim_corr, annot=True, cmap='YlGnBu', fmt='.3f', ax=ax)
    ax.set_title(f"Correlation Heatmap of Five Core Dimensions (5x5)\n[{method_name}]", fontsize=14)
    
    plt.tight_layout()
    
    # 保存图表
    output_filename = f"correlation_{method_key}.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"\n✓ 图表已保存到: {output_filename}")
    plt.close()  # 关闭图表，避免内存占用
    
    print("\n维度间相关系数矩阵:")
    print(dim_corr)
    
    # 分析结论输出
    print("\n关键发现:")
    print(f"1. 经济与基建的相关性: {dim_corr.loc['Economy', 'Infrastructure']:.3f}，体现资本对硬件的直接驱动。")
    print(f"2. 人才与科研的相关性: {dim_corr.loc['Talent', 'Research']:.3f}，证实智力资源是创新的源泉。")
    print(f"3. 政策与其他维度的相关性:")
    for dim in ['Talent', 'Research', 'Infrastructure', 'Economy']:
        if dim != 'Policy':
            print(f"   - Policy vs {dim}: {dim_corr.loc['Policy', dim]:.3f}")

print(f"\n{'='*80}")
print("所有标准化方法的相关性分析完成！")
print("="*80)
print("\n生成的文件：")
for method_key in normalization_methods.keys():
    print(f"  - correlation_{method_key}.png")
