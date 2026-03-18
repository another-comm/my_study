"""
分析本问题目录下 results/analysis_results.xlsx 文件
"""

import pandas as pd
import numpy as np
import os

def analyze_results_excel(excel_path=None):
    """分析结果Excel文件（默认: 本问题目录的 results/analysis_results.xlsx）"""
    if excel_path is None:
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        excel_path = os.path.join(_script_dir, 'results', 'analysis_results.xlsx')
    if not os.path.exists(excel_path):
        print(f"错误: 找不到文件 {excel_path}")
        return
    
    print("="*70)
    print("分析结果 Excel 文件")
    print("="*70)
    
    xls = pd.ExcelFile(excel_path, engine='openpyxl')
    
    print(f"\n文件: {excel_path}")
    print(f"包含 {len(xls.sheet_names)} 个 Sheet:")
    for i, sheet in enumerate(xls.sheet_names, 1):
        print(f"  {i}. {sheet}")
    
    # 1. 评估指标
    print("\n" + "="*70)
    print("【1. 评估指标】")
    print("="*70)
    metrics_df = pd.read_excel(xls, sheet_name='评估指标')
    print(metrics_df.to_string(index=False))
    
    # 2. 投票估计汇总统计
    print("\n" + "="*70)
    print("【2. 投票估计汇总 - 统计信息】")
    print("="*70)
    vote_df = pd.read_excel(xls, sheet_name='投票估计汇总')
    print(f"总记录数: {len(vote_df)}")
    print(f"分析的赛季: {sorted(vote_df['赛季'].unique())}")
    print(f"分析的周数范围: {vote_df['周次'].min()} - {vote_df['周次'].max()}")
    print(f"\n各赛季分析周数:")
    season_weeks = vote_df.groupby('赛季')['周次'].nunique().sort_index()
    for season, n_weeks in season_weeks.items():
        print(f"  Season {season}: {n_weeks} 周")
    
    print(f"\n投票比例统计:")
    print(f"  平均值: {vote_df['估计投票比例'].mean():.4f}")
    print(f"  标准差: {vote_df['估计投票比例'].std():.4f}")
    print(f"  最小值: {vote_df['估计投票比例'].min():.4f}")
    print(f"  最大值: {vote_df['估计投票比例'].max():.4f}")
    
    print(f"\n一致性统计:")
    consistency_valid = vote_df['一致性'].dropna()
    if len(consistency_valid) > 0:
        print(f"  平均值: {consistency_valid.mean():.4f}")
        print(f"  标准差: {consistency_valid.std():.4f}")
        print(f"  最小值: {consistency_valid.min():.4f}")
        print(f"  最大值: {consistency_valid.max():.4f}")
    
    # 3. 各赛季一致性
    print("\n" + "="*70)
    print("【3. 各赛季一致性统计】")
    print("="*70)
    season_consistency_df = pd.read_excel(xls, sheet_name='各赛季一致性')
    print(season_consistency_df.to_string(index=False))
    
    # 分析最佳和最差表现的赛季
    if len(season_consistency_df) > 0:
        best_season = season_consistency_df.loc[season_consistency_df['平均一致性'].idxmax()]
        worst_season = season_consistency_df.loc[season_consistency_df['平均一致性'].idxmin()]
        print(f"\n最佳表现: Season {int(best_season['赛季'])} (一致性={best_season['平均一致性']:.4f})")
        print(f"最差表现: Season {int(worst_season['赛季'])} (一致性={worst_season['平均一致性']:.4f})")
    
    # 4. 争议案例分析
    print("\n" + "="*70)
    print("【4. 争议案例分析】")
    print("="*70)
    controversy_df = pd.read_excel(xls, sheet_name='争议案例分析')
    if len(controversy_df) > 0:
        print(controversy_df.to_string(index=False))
        
        print("\n关键发现:")
        for idx, row in controversy_df.iterrows():
            name = row['选手姓名']
            season = int(row['赛季'])
            placement = int(row['最终名次'])
            avg_judge_rank = row['平均评委排名']
            avg_vote_rank = row['平均投票排名']
            gap = row['粉丝票弥补程度']
            
            print(f"\n  {name} (Season {season}):")
            print(f"    最终名次: {placement}")
            print(f"    平均评委排名: {avg_judge_rank:.2f}")
            print(f"    平均投票排名: {avg_vote_rank:.2f}")
            print(f"    粉丝票弥补程度: {gap:+.2f} (正值=粉丝更支持)")
            
            if gap > 0:
                print(f"    → 粉丝投票显著弥补了评委分的劣势")
            elif gap < 0:
                print(f"    → 粉丝投票甚至低于评委排名")
    else:
        print("无争议案例数据")
    
    # 5. 方法对比
    print("\n" + "="*70)
    print("【5. 方法对比结果】")
    print("="*70)
    comparison_df = pd.read_excel(xls, sheet_name='方法对比')
    if len(comparison_df) > 0:
        print(comparison_df.to_string(index=False))
        
        total_weeks = comparison_df['分析周数'].sum()
        total_different = comparison_df['结果不同周数'].sum()
        overall_diff_rate = (total_different / total_weeks * 100) if total_weeks > 0 else 0
        
        print(f"\n总体统计:")
        print(f"  总分析周数: {total_weeks}")
        print(f"  结果不同周数: {total_different}")
        print(f"  总体差异率: {overall_diff_rate:.2f}%")
        
        if overall_diff_rate > 10:
            print(f"  → 两种投票方法存在显著差异")
        elif overall_diff_rate > 5:
            print(f"  → 两种投票方法存在一定差异")
        else:
            print(f"  → 两种投票方法结果基本一致")
    else:
        print("无方法对比数据")
    
    # 6. 详细数据样本（前10条）
    print("\n" + "="*70)
    print("【6. 投票估计汇总 - 数据样本（前10条）】")
    print("="*70)
    print(vote_df.head(10).to_string(index=False))
    
    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)


if __name__ == "__main__":
    analyze_results_excel()
