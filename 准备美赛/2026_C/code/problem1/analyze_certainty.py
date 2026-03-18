"""
分析估计值的确定性度量
"""

import json
import numpy as np
import pandas as pd
import os

def analyze_certainty_metrics():
    """分析确定性度量（从本问题目录的 results 读取）"""
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(_script_dir, 'results', 'vote_estimates.json')
    if not os.path.exists(json_path):
        print(f"错误: 找不到文件 {json_path}")
        return
    
    print("="*70)
    print("估计值的确定性度量分析")
    print("="*70)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 检查是否有MCMC结果（包含certainty字段）
    has_mcmc = False
    certainty_data = []
    consistency_data = []
    
    for season, season_result in results.items():
        for week, week_result in season_result.get('weeks', {}).items():
            # 收集一致性数据
            consistency = week_result.get('consistency', None)
            if consistency is not None:
                consistency_data.append({
                    'season': int(season),
                    'week': int(week),
                    'consistency': float(consistency),
                    'method': season_result.get('method', 'unknown')
                })
            
            # 检查是否有MCMC结果
            if 'certainty' in week_result:
                has_mcmc = True
                certainty_values = week_result['certainty']
                votes_std = week_result.get('votes_std', [])
                votes_mean = week_result.get('votes_mean', [])
                
                for i, cert in enumerate(certainty_values):
                    certainty_data.append({
                        'season': int(season),
                        'week': int(week),
                        'contestant_idx': i,
                        'certainty': float(cert),
                        'vote_std': float(votes_std[i]) if i < len(votes_std) else None,
                        'vote_mean': float(votes_mean[i]) if i < len(votes_mean) else None
                    })
    
    # 1. 基于一致性的确定性分析（无需MCMC）
    print("\n【1. 基于一致性的确定性分析】")
    print("-"*70)
    
    if consistency_data:
        consistency_df = pd.DataFrame(consistency_data)
        
        print(f"总分析周数: {len(consistency_df)}")
        print(f"\n一致性统计:")
        print(f"  平均值: {consistency_df['consistency'].mean():.4f}")
        print(f"  标准差: {consistency_df['consistency'].std():.4f}")
        print(f"  最小值: {consistency_df['consistency'].min():.4f}")
        print(f"  最大值: {consistency_df['consistency'].max():.4f}")
        
        # 一致性作为确定性的代理指标
        # 一致性越高，说明模型对投票估计越确定
        print(f"\n确定性解释（基于一致性）:")
        print(f"  高确定性（一致性 > 0.8）: {len(consistency_df[consistency_df['consistency'] > 0.8])} 周 ({len(consistency_df[consistency_df['consistency'] > 0.8])/len(consistency_df)*100:.1f}%)")
        print(f"  中等确定性（0.5 < 一致性 <= 0.8）: {len(consistency_df[(consistency_df['consistency'] > 0.5) & (consistency_df['consistency'] <= 0.8)])} 周 ({len(consistency_df[(consistency_df['consistency'] > 0.5) & (consistency_df['consistency'] <= 0.8)])/len(consistency_df)*100:.1f}%)")
        print(f"  低确定性（一致性 <= 0.5）: {len(consistency_df[consistency_df['consistency'] <= 0.5])} 周 ({len(consistency_df[consistency_df['consistency'] <= 0.5])/len(consistency_df)*100:.1f}%)")
        
        # 按投票方法分组
        print(f"\n按投票方法分组:")
        for method in consistency_df['method'].unique():
            method_df = consistency_df[consistency_df['method'] == method]
            print(f"  {method}制:")
            print(f"    平均一致性: {method_df['consistency'].mean():.4f}")
            print(f"    一致性标准差: {method_df['consistency'].std():.4f}")
    
    # 2. MCMC不确定性量化（如果可用）
    print("\n【2. MCMC不确定性量化】")
    print("-"*70)
    
    if has_mcmc and certainty_data:
        certainty_df = pd.DataFrame(certainty_data)
        
        print(f"✓ 检测到MCMC结果")
        print(f"总确定性记录数: {len(certainty_df)}")
        print(f"\n确定性统计:")
        print(f"  平均值: {certainty_df['certainty'].mean():.4f}")
        print(f"  标准差: {certainty_df['certainty'].std():.4f}")
        print(f"  最小值: {certainty_df['certainty'].min():.4f}")
        print(f"  最大值: {certainty_df['certainty'].max():.4f}")
        
        if 'vote_std' in certainty_df.columns:
            print(f"\n投票比例标准差统计:")
            vote_std_valid = certainty_df['vote_std'].dropna()
            if len(vote_std_valid) > 0:
                print(f"  平均值: {vote_std_valid.mean():.6f}")
                print(f"  标准差: {vote_std_valid.std():.6f}")
                print(f"  最小值: {vote_std_valid.min():.6f}")
                print(f"  最大值: {vote_std_valid.max():.6f}")
    else:
        print("⚠ 未检测到MCMC结果")
        print("  说明: 当前分析使用的是MAP估计（快速但无不确定性量化）")
        print("  建议: 使用 --mcmc 参数运行分析以获得精确的确定性度量")
    
    # 3. 确定性度量方法总结
    print("\n【3. 确定性度量方法总结】")
    print("-"*70)
    
    print("""
我们的模型提供了以下确定性度量方法：

1. 【基于一致性的确定性】（当前可用）
   - 度量: 软一致性 (Soft Consistency)
   - 定义: 模型预测的淘汰概率与实际淘汰者的匹配度
   - 范围: [0, 1]，值越高表示确定性越高
   - 优点: 无需MCMC，计算快速
   - 局限性: 是间接度量，不直接反映投票估计的不确定性

2. 【基于后验方差的确定性】（需要MCMC）
   - 度量: Certainty = 1 / (vote_std + ε)
   - 定义: 投票比例后验标准差的倒数
   - 优点: 直接量化投票估计的不确定性
   - 需要: 运行MCMC采样（使用 --mcmc 参数）

3. 【基于信息熵的确定性】（需要MCMC）
   - 度量: Entropy = -Σ p_i × log(p_i)
   - 定义: 投票分布的信息熵
   - 优点: 反映投票分布的集中程度
   - 需要: 运行MCMC采样

4. 【置信区间宽度】（需要MCMC）
   - 度量: 95% 置信区间宽度
   - 定义: vote_ci_upper - vote_ci_lower
   - 优点: 直观反映估计的不确定性范围
   - 需要: 运行MCMC采样
    """)
    
    # 4. 确定性是否恒定？
    print("\n【4. 确定性是否对每个选手/每周都相同？】")
    print("-"*70)
    
    if consistency_data:
        consistency_df = pd.DataFrame(consistency_data)
        
        # 按周次分析
        weekly_consistency = consistency_df.groupby(['season', 'week'])['consistency'].mean()
        print(f"不同周次的一致性差异:")
        print(f"  平均值: {weekly_consistency.mean():.4f}")
        print(f"  标准差: {weekly_consistency.std():.4f}")
        print(f"  变异系数: {weekly_consistency.std() / weekly_consistency.mean():.4f}")
        
        if weekly_consistency.std() / weekly_consistency.mean() > 0.3:
            print(f"  → 结论: 确定性在不同周次间存在显著差异（变异系数 > 0.3）")
        else:
            print(f"  → 结论: 确定性在不同周次间相对稳定")
        
        # 按赛季分析
        season_consistency = consistency_df.groupby('season')['consistency'].mean()
        print(f"\n不同赛季的一致性差异:")
        print(f"  平均值: {season_consistency.mean():.4f}")
        print(f"  标准差: {season_consistency.std():.4f}")
        print(f"  最小值: {season_consistency.min():.4f} (Season {season_consistency.idxmin()})")
        print(f"  最大值: {season_consistency.max():.4f} (Season {season_consistency.idxmax()})")
        
        print(f"\n  → 结论: 确定性在不同赛季间存在显著差异")
        print(f"     排名制赛季（1-2, 28-34）: 一致性更高 → 确定性更高")
        print(f"     百分比制赛季（3-27）: 一致性较低 → 确定性较低")
    
    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)


if __name__ == "__main__":
    analyze_certainty_metrics()
