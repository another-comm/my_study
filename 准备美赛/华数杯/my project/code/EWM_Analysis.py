import pandas as pd
import numpy as np

# 1. 原始数据录入 (基于 Global_AI_Matrix_2025.md)
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

# 国家人口（亿），用于人才维度三项的复合得分
population = {
    "USA": 342.3,
    "China": 1408.2,
    "India": 1445.5,
    "Japan": 122.8,
    "Germany": 83.2,
    "UK": 68.2,
    "France": 65.5,
    "South Korea": 51.5,
    "Canada": 39.8,
    "UAE": 10.3
}
pop_series = df["Country"].map(population)
if pop_series.isnull().any():
    missing = df.loc[pop_series.isnull(), "Country"].unique()
    raise ValueError(f"缺少人口数据: {missing}")

# 人才维度三项：用复合得分替换
# 复合得分 = 0.3*(该国该指标 / 10国总和) + 0.7*(该国该指标 / 该国人口)
talent_cols = ["Top_Scholars", "Total_Prof", "STEM_Grads"]
for col in talent_cols:
    total_sum = df[col].sum()
    df[col] = 0.3 * (df[col] / total_sum) + 0.7 * (df[col] / pop_series)

# 更新 numeric_df（已包含复合后的人才三项）
numeric_df = df.drop(columns=['Country'])

# 定义两种标准化方法（保留 Min-Max 与 Sigmoid）
normalization_methods = {
    'minmax': {
        'name': 'Min-Max标准化',
        'description': '直接使用原始数据进行标准化'
    },
    'sigmoid': {
        'name': 'Sigmoid归一化（逻辑斯蒂映射）',
        'description': '使用Sigmoid函数映射，压制极端值，放大中端区域细微差距'
    }
}

print("=" * 80)
print("数据标准化处理 - 三种方法对比")
print("=" * 80)

# 3. 熵权法计算函数
def calculate_entropy_weights(df_norm):
    # 避免log(0)，对数据进行微小偏移
    df_norm = df_norm + 1e-9
    
    # 计算各项指标下第i个样本所占比重 p_ij
    p = df_norm / df_norm.sum()
    
    # 计算熵值 e_j
    k = 1 / np.log(len(df_norm))
    e = -k * (p * np.log(p)).sum()
    
    # 计算差异系数 d_j
    d = 1 - e
    
    # 计算权重 w_j
    weights = d / d.sum()
    return weights

# 定义维度映射
dim_map = {
    "Talent": ["Top_Scholars", "Total_Prof", "STEM_Grads", "Migration_Idx", "Skill_Pen"],
    "Research": ["Papers", "FWCI", "Patents"],
    "Infrastructure": ["Compute_EFLOPS", "Power_MW", "GPU_Stock", "5G_Cover"],
    "Economy": ["Investment", "Unicorns", "GDP_Contrib", "Adoption"],
    "Policy": ["Policy_Score", "Data_Score"]
}

# 循环处理三种标准化方法
all_results = {}

for method_key, method_info in normalization_methods.items():
    print(f"\n{'='*80}")
    print(f"方法: {method_info['name']} ({method_key})")
    print(f"{'='*80}")
    print(f"说明: {method_info['description']}")
    print("-" * 80)
    
    # 根据方法进行标准化
    if method_key == 'minmax':
        # 方法1: Min-Max标准化
        normalized_df = (numeric_df - numeric_df.min()) / (numeric_df.max() - numeric_df.min())
        
    elif method_key == 'sigmoid':
        # 方法3: Sigmoid归一化（逻辑斯蒂映射）
        # z_ij = 1 / (1 + exp(-alpha * (x_ij - mean) / std))
        normalized_df = numeric_df.copy()
        alpha = 2.0  # Sigmoid曲线陡峭程度参数，可以调整（1.0-3.0之间）
        
        for col in normalized_df.columns:
            col_data = numeric_df[col].values
            # 计算均值和标准差
            mean_val = col_data.mean()
            std_val = col_data.std()
            
            # 避免除零
            if std_val == 0:
                # 如果标准差为0（所有值相同），则标准化为0.5
                normalized_df[col] = 0.5
            else:
                # 标准化：(x - mean) / std
                standardized = (col_data - mean_val) / std_val
                # Sigmoid映射：1 / (1 + exp(-alpha * standardized))
                normalized_df[col] = 1 / (1 + np.exp(-alpha * standardized))
    
    # 处理负值指标（Migration_Idx）
    # 注意：Sigmoid归一化可以处理负值，因为它是基于均值和标准差的标准化
    # 所以不需要特殊处理
    
    # 显示标准化后的数据分布
    print(f"标准化后数据范围: [{normalized_df.min().min():.4f}, {normalized_df.max().max():.4f}]")
    print(f"标准化后数据均值: {normalized_df.mean().mean():.4f}")
    
    # 计算熵权法权重
    weights = calculate_entropy_weights(normalized_df)
    
    # 输出结果
    results = pd.DataFrame({
        "Indicator": weights.index,
        "Weight": weights.values
    }).sort_values(by="Weight", ascending=False)
    
    print("\n各指标权重分布（前10名）：")
    print(results.head(10))
    
    # 计算各维度总权重
    dim_weights = {}
    for dim, indicators in dim_map.items():
        dim_weights[dim] = results[results['Indicator'].isin(indicators)]['Weight'].sum()
    
    print("\n各维度总权重：")
    for k, v in dim_weights.items():
        print(f"  {k}: {v:.4f}")
    
    # ===== 新增：19 -> 5 维度汇总（对齐后续问题2/3） =====
    # 1) 维度内熵权
    dim_inner_weights = {}
    for dim, cols in dim_map.items():
        sub_df = normalized_df[cols]
        dim_inner_weights[dim] = calculate_entropy_weights(sub_df)
    
    # 2) 计算每个维度得分（按维度内熵权加权，0-100）
    dim_scores = {}
    for dim, cols in dim_map.items():
        w_in = dim_inner_weights[dim].values
        dim_scores[dim] = (normalized_df[cols].values @ w_in) * 100
    dim_scores_df = pd.DataFrame(dim_scores)
    
    # 3) 维度间权重（客观熵权，可选用固定权重时替换此处）
    w_dim = calculate_entropy_weights(dim_scores_df)
    print("\n维度间熵权权重：")
    for d, v in w_dim.items():
        print(f"  {d}: {v:.4f}")
    
    # 4) 综合总分（5维加权）
    total_score = (dim_scores_df.values @ w_dim.values)  # 0-100
    five_dims_with_country = pd.concat([df[['Country']], dim_scores_df], axis=1)
    five_dims_with_country['Total_Score'] = total_score
    
    # 只保存 5 维度汇总结果
    excel_filename_5d = f"normalized_data_{method_key}_5dims.xlsx"
    five_dims_with_country.to_excel(excel_filename_5d, index=False, sheet_name='五维度得分')
    print(f"\n✓ 5维度汇总数据已保存到: {excel_filename_5d}")
    
    # 额外导出权重信息（指标/维度）
    weight_output = f"weights_{method_key}.xlsx"
    with pd.ExcelWriter(weight_output, engine="openpyxl") as writer:
        # 指标熵权（19项）
        results.to_excel(writer, index=False, sheet_name="指标熵权")
        # 维度总权重（5项）
        pd.DataFrame([
            {"Dimension": k, "Weight": v} for k, v in dim_weights.items()
        ]).to_excel(writer, index=False, sheet_name="维度权重")
        # 维度内权重（各维度单独sheet）
        for dim, w_in in dim_inner_weights.items():
            w_df = pd.DataFrame({"Indicator": w_in.index, "Weight": w_in.values})
            w_df.to_excel(writer, index=False, sheet_name=f"内权重_{dim}")
        # 维度间权重
        pd.DataFrame({
            "Dimension": w_dim.index,
            "Weight": w_dim.values
        }).to_excel(writer, index=False, sheet_name="维度间权重")
    print(f"✓ 权重信息已保存到: {weight_output}")
    
    # 保存结果
    all_results[method_key] = {
        'weights': weights,
        'dim_weights': dim_weights,
        'normalized_df': normalized_df
    }

print(f"\n{'='*80}")
print("所有标准化方法处理完成！")
print("="*80)
print("\n生成的Excel文件：")
for method_key in normalization_methods.keys():
    print(f"  - normalized_data_{method_key}_5dims.xlsx")
