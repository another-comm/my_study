"""
DWTS 粉丝投票估计 - 完整分析脚本
MCM 2026 Problem C

使用方法:
    python run_analysis.py --data <数据文件路径> [--seasons 1 2 3] [--mcmc]

此脚本将:
1. 加载并预处理数据
2. 使用IDM模型估计粉丝投票
3. 计算一致性和确定性指标
4. 对比排名制和百分比制
5. 分析争议案例
6. 生成可视化和报告
"""

import argparse
import json
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 导入自定义模块
from idm_fan_vote_model import (
    load_and_preprocess_data, 
    get_season_data,
    get_week_contestants,
    DWTSFanVoteEstimator,
    InverseDecisionModel,
    ForwardModel,
    VotingCombiner,
    MCMCSampler,
    ModelEvaluator
)

from visualization_analysis import (
    plot_week_votes,
    plot_week_votes_with_uncertainty,
    plot_season_consistency,
    VotingMethodComparator,
    plot_method_comparison,
    ControversyAnalyzer,
    plot_controversy_analysis,
    generate_summary_report,
    plot_paper_consistency_summary,
    plot_paper_controversy_summary,
    plot_paper_voting_method_difference,
    plot_paper_certainty_summary,
    plot_paper_vote_example,
)


def parse_args():
    """解析命令行参数。默认数据在项目根目录，输出在本问题目录的 results 下。"""
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.dirname(_script_dir)
    _default_data = os.path.join(_project_root, '2026_MCM_Problem_C_Data_processed.xlsx')
    _default_output = os.path.join(_script_dir, 'results')
    parser = argparse.ArgumentParser(description='DWTS 粉丝投票估计分析')
    parser.add_argument('--data', type=str, default=_default_data,
                        help='数据文件路径（默认: 项目根目录下的 _processed.xlsx）')
    parser.add_argument('--seasons', nargs='+', type=int, default=None,
                        help='要分析的赛季列表（默认全部）')
    parser.add_argument('--mcmc', action='store_true',
                        help='使用MCMC进行不确定性量化')
    parser.add_argument('--output', type=str, default=_default_output,
                        help='输出目录（默认: 本问题目录下的 results）')
    parser.add_argument('--verbose', action='store_true', default=True,
                        help='显示详细输出')
    return parser.parse_args()


def ensure_output_dir(output_dir):
    """确保输出目录存在"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def run_main_analysis(df, seasons, use_mcmc=False, verbose=True):
    """
    运行主要分析
    
    Parameters:
    -----------
    df : pd.DataFrame
        数据
    seasons : list
        赛季列表
    use_mcmc : bool
        是否使用MCMC
    verbose : bool
        是否显示详细输出
        
    Returns:
    --------
    results : dict
        估计结果
    metrics : dict
        评估指标
    """
    estimator = DWTSFanVoteEstimator(
        softmax_temp=1.0,
        likelihood_temp=0.1
    )
    
    results = estimator.estimate_all_seasons(
        df, 
        seasons=seasons,
        use_mcmc=use_mcmc,
        verbose=verbose
    )
    
    metrics = estimator.compute_overall_metrics(results)
    
    return results, metrics


def run_controversy_analysis(df, results, verbose=True):
    """
    运行争议案例分析
    
    Parameters:
    -----------
    df : pd.DataFrame
        数据
    results : dict
        投票估计结果
    verbose : bool
        是否显示详细输出
        
    Returns:
    --------
    controversy_results : list
        争议案例分析结果
    """
    analyzer = ControversyAnalyzer(df)
    
    # 定义要分析的争议案例
    controversy_cases = [
        ('Jerry Rice', 2),      # Season 2: 评委分最低但获得亚军
        ('Billy Ray Cyrus', 4), # Season 4: 评委分最低6次但获第5
        ('Bristol Palin', 11),  # Season 11: 评委分最低12次但获第3
        ('Bobby Bones', 27),    # Season 27: 评委分持续低但获冠军
    ]
    
    controversy_results = []
    
    for name, season in controversy_cases:
        if verbose:
            print(f"\n分析争议案例: {name} (Season {season})")
        
        # 检查该赛季是否在结果中
        if season not in results:
            if verbose:
                print(f"  警告: Season {season} 不在分析结果中，跳过")
            continue
        
        # 分析
        analysis = analyzer.analyze_controversy_case(name, season, results)
        simulation = analyzer.simulate_alternative_outcomes(name, season, results)
        
        controversy_results.append({
            'analysis': analysis,
            'simulation': simulation
        })
        
        if verbose and 'error' not in analysis:
            print(f"  最终名次: {analysis['final_placement']}")
            print(f"  平均评委排名: {analysis['avg_judge_rank']:.2f}")
            print(f"  平均投票排名: {analysis['avg_vote_rank']:.2f}")
            print(f"  粉丝弥补程度: {analysis['judge_vote_gap']:+.2f}")
    
    return controversy_results


def run_method_comparison(df, results, verbose=True):
    """
    运行两种投票方法的对比分析
    
    Parameters:
    -----------
    df : pd.DataFrame
        数据
    results : dict
        投票估计结果
    verbose : bool
        是否显示详细输出
        
    Returns:
    --------
    comparison_results : dict
        对比分析结果
    """
    comparator = VotingMethodComparator()
    comparison_results = {}
    
    for season, season_result in results.items():
        season_comparisons = []
        
        for week, week_result in season_result['weeks'].items():
            judge_scores = np.array(week_result['judge_scores'])
            votes = np.array(week_result['votes_map'])
            
            comparison = comparator.compare_methods(judge_scores, votes)
            bias = comparator.analyze_method_bias(judge_scores, votes)
            
            season_comparisons.append({
                'week': week,
                'comparison': comparison,
                'bias': bias
            })
        
        # 统计该赛季的整体差异
        n_different = sum(1 for c in season_comparisons if c['comparison']['any_difference'])
        
        comparison_results[season] = {
            'weeks': season_comparisons,
            'n_weeks': len(season_comparisons),
            'n_different_outcomes': n_different,
            'difference_rate': n_different / len(season_comparisons) if season_comparisons else 0
        }
        
        if verbose:
            print(f"\nSeason {season}: "
                  f"{n_different}/{len(season_comparisons)} 周存在方法差异 "
                  f"({comparison_results[season]['difference_rate']*100:.1f}%)")
    
    return comparison_results


def generate_visualizations(results, controversy_results, comparison_results, output_dir):
    """
    生成适合放入论文的汇总图（英文标注，少量高质量图）。
    输出：一致性、争议案例、投票方法差异、确定性 Φ 汇总（有 MCMC 时）、4 张单周案例。
    """
    print("\n生成可视化图表（论文用汇总图）...")
    
    # 1. 一致性汇总：所有赛季的软一致性 + 硬准确率（一张图两子图）
    fig = plot_paper_consistency_summary(results)
    if fig:
        fig.savefig(os.path.join(output_dir, 'paper_fig_consistency_summary.png'),
                    dpi=200, bbox_inches='tight')
        plt.close(fig)
        print("  - paper_fig_consistency_summary.png")
    
    # 2. 争议案例汇总：四例 2x2 子图（评委 vs 投票排名随周变化）
    fig = plot_paper_controversy_summary(controversy_results)
    if fig:
        fig.savefig(os.path.join(output_dir, 'paper_fig_controversy_summary.png'),
                    dpi=200, bbox_inches='tight')
        plt.close(fig)
        print("  - paper_fig_controversy_summary.png")
    
    # 3. 投票方法差异：各赛季「排名制 vs 百分比制」差异率
    fig = plot_paper_voting_method_difference(comparison_results)
    if fig:
        fig.savefig(os.path.join(output_dir, 'paper_fig_voting_method_difference.png'),
                    dpi=200, bbox_inches='tight')
        plt.close(fig)
        print("  - paper_fig_voting_method_difference.png")
    
    # 4. 确定性 Φ 汇总：各赛季平均 Φ、全样本 Φ 分布（仅当使用 MCMC 时有数据）
    fig = plot_paper_certainty_summary(results)
    if fig:
        fig.savefig(os.path.join(output_dir, 'paper_fig_certainty_summary.png'),
                    dpi=200, bbox_inches='tight')
        plt.close(fig)
        print("  - paper_fig_certainty_summary.png")
    
    # 5. 单周投票估计示例：输出 4 张案例图（不同赛季/周）；有 MCMC 时含确定性 Φ 子图
    seasons_with_weeks = [(s, r) for s, r in sorted(results.items()) if len(r.get('weeks', {})) > 0]
    n_examples = 4
    if len(seasons_with_weeks) >= n_examples:
        # 均匀选取 4 个赛季（前、中前、中后、后）
        indices = [int(i * (len(seasons_with_weeks) - 1) / (n_examples - 1)) for i in range(n_examples)]
        for i, idx in enumerate(indices):
            season, season_result = seasons_with_weeks[idx]
            weeks = sorted(season_result['weeks'].keys())
            mid_week = weeks[len(weeks) // 2]
            week_result = season_result['weeks'][mid_week]
            fig = plot_paper_vote_example(week_result, season, mid_week)
            if fig:
                fname = f'paper_fig_vote_example_{i+1}_s{season}_w{mid_week}.png'
                fig.savefig(os.path.join(output_dir, fname), dpi=200, bbox_inches='tight')
                plt.close(fig)
                print(f"  - {fname}")
    else:
        # 赛季不足 4 个时，每个赛季取中间周
        for i, (season, season_result) in enumerate(seasons_with_weeks[:n_examples]):
            weeks = sorted(season_result['weeks'].keys())
            mid_week = weeks[len(weeks) // 2]
            week_result = season_result['weeks'][mid_week]
            fig = plot_paper_vote_example(week_result, season, mid_week)
            if fig:
                fname = f'paper_fig_vote_example_{i+1}_s{season}_w{mid_week}.png'
                fig.savefig(os.path.join(output_dir, fname), dpi=200, bbox_inches='tight')
                plt.close(fig)
                print(f"  - {fname}")
    
    print(f"  论文用图表已保存到 {output_dir}/（汇总图 + 4 张单周案例；使用 --mcmc 时含确定性 Φ 图）")


def save_results(results, metrics, controversy_results, comparison_results, output_dir):
    """
    保存所有结果到文件（JSON + Excel）
    """
    print("\n保存结果...")
    
    # 转换函数（用于JSON序列化）
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)  # np.bool_ 不是 JSON 可序列化，转为 Python bool
        elif isinstance(obj, dict):
            # 字典的 key 也必须是 str/int/float/bool/None，不能是 int64
            def key_convert(k):
                if isinstance(k, (np.integer, np.int64)):
                    return int(k)
                if isinstance(k, (np.floating, np.float64)):
                    return float(k)
                if isinstance(k, (np.bool_, bool)):
                    return bool(k)
                return k
            return {key_convert(k): convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        return obj
    
    # 1. 保存指标（JSON）
    with open(os.path.join(output_dir, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    # 2. 保存详细结果（JSON）
    results_serializable = convert_to_serializable(results)
    with open(os.path.join(output_dir, 'vote_estimates.json'), 'w', encoding='utf-8') as f:
        json.dump(results_serializable, f, indent=2, ensure_ascii=False)
    
    # 3. 保存争议案例分析（JSON）
    controversy_serializable = convert_to_serializable(controversy_results)
    with open(os.path.join(output_dir, 'controversy_analysis.json'), 'w', encoding='utf-8') as f:
        json.dump(controversy_serializable, f, indent=2, ensure_ascii=False)
    
    # 4. 生成文本报告
    analyses = [c['analysis'] for c in controversy_results if 'error' not in c.get('analysis', {})]
    report = generate_summary_report(results, metrics, analyses)
    with open(os.path.join(output_dir, 'summary_report.txt'), 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 5. 保存到 Excel（新增）
    excel_path = os.path.join(output_dir, 'analysis_results.xlsx')
    print(f"\n保存结果到 Excel: {excel_path}")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Sheet 1: 评估指标
        metrics_df = pd.DataFrame([
            ['分析的周数', metrics.get('n_weeks_analyzed', 0)],
            ['平均一致性（软）', f"{metrics.get('mean_consistency', 0):.4f}"],
            ['一致性标准差', f"{metrics.get('std_consistency', 0):.4f}"],
            ['硬一致性准确率', f"{metrics.get('hard_accuracy', 0)*100:.2f}%"],
        ], columns=['指标', '数值'])
        metrics_df.to_excel(writer, sheet_name='评估指标', index=False)
        
        # Sheet 2: 投票估计汇总（按赛季和周）
        vote_summary_rows = []
        for season, season_result in results.items():
            method = season_result.get('method', 'unknown')
            for week, week_result in season_result.get('weeks', {}).items():
                contestants = week_result.get('contestants', [])
                judge_scores = week_result.get('judge_scores', [])
                votes_map = week_result.get('votes_map', [])
                eliminated = week_result.get('eliminated', [])
                consistency = week_result.get('consistency', 0)
                is_consistent = week_result.get('is_consistent', False)
                
                # 确定性 Φ = 1/std(p^MCMC)（仅在使用 MCMC 时有值）
                certainty_phi_list = week_result.get('certainty_phi') or week_result.get('certainty')
                
                # 为每位选手创建一行
                for i, (name, score, vote) in enumerate(zip(contestants, judge_scores, votes_map)):
                    row = {
                        '赛季': int(season),
                        '周次': int(week),
                        '投票方法': method,
                        '选手姓名': name,
                        '评委总分': float(score) if pd.notna(score) else None,
                        '估计投票比例': float(vote) if pd.notna(vote) else None,
                        '是否被淘汰': name in eliminated if eliminated else False,
                        '一致性': float(consistency) if pd.notna(consistency) else None,
                        '预测正确': bool(is_consistent),
                    }
                    if certainty_phi_list and i < len(certainty_phi_list):
                        row['确定性Φ'] = float(certainty_phi_list[i])
                    vote_summary_rows.append(row)
        
        if vote_summary_rows:
            vote_summary_df = pd.DataFrame(vote_summary_rows)
            vote_summary_df.to_excel(writer, sheet_name='投票估计汇总', index=False)
        
        # Sheet 3: 各赛季一致性统计
        season_consistency_rows = []
        for season, season_result in results.items():
            method = season_result.get('method', 'unknown')
            weeks = season_result.get('weeks', {})
            if weeks:
                consistencies = [w.get('consistency', 0) for w in weeks.values()]
                hard_consistencies = [w.get('is_consistent', False) for w in weeks.values()]
                season_consistency_rows.append({
                    '赛季': int(season),
                    '投票方法': method,
                    '分析周数': len(weeks),
                    '平均一致性': np.mean(consistencies) if consistencies else 0,
                    '一致性标准差': np.std(consistencies) if consistencies else 0,
                    '硬一致性准确率': np.mean(hard_consistencies)*100 if hard_consistencies else 0,
                })
        
        if season_consistency_rows:
            season_consistency_df = pd.DataFrame(season_consistency_rows)
            season_consistency_df.to_excel(writer, sheet_name='各赛季一致性', index=False)
        
        # Sheet 4: 争议案例分析
        controversy_rows = []
        for case in controversy_results:
            analysis = case.get('analysis', {})
            simulation = case.get('simulation', {})
            
            if 'error' not in analysis:
                controversy_rows.append({
                    '选手姓名': analysis.get('celebrity', ''),
                    '赛季': int(analysis.get('season', 0)),
                    '最终名次': int(analysis.get('final_placement', 0)),
                    '参赛周数': int(analysis.get('weeks_competed', 0)),
                    '平均评委排名': float(analysis.get('avg_judge_rank', 0)),
                    '平均投票排名': float(analysis.get('avg_vote_rank', 0)),
                    '评委最低分次数': int(analysis.get('times_lowest_judge_score', 0)),
                    '粉丝票弥补程度': float(analysis.get('judge_vote_gap', 0)),
                    '排名制潜在淘汰次数': int(simulation.get('rank_method_potential_eliminations', 0)),
                    '百分比制潜在淘汰次数': int(simulation.get('pct_method_potential_eliminations', 0)),
                    '方法差异': bool(simulation.get('method_makes_difference', False)),
                })
        
        if controversy_rows:
            controversy_df = pd.DataFrame(controversy_rows)
            controversy_df.to_excel(writer, sheet_name='争议案例分析', index=False)
        
        # Sheet 5: 方法对比结果
        comparison_rows = []
        for season, comp_result in comparison_results.items():
            comparison_rows.append({
                '赛季': int(season),
                '分析周数': int(comp_result.get('n_weeks', 0)),
                '结果不同周数': int(comp_result.get('n_different_outcomes', 0)),
                '差异率': f"{comp_result.get('difference_rate', 0)*100:.2f}%",
            })
        
        if comparison_rows:
            comparison_df = pd.DataFrame(comparison_rows)
            comparison_df.to_excel(writer, sheet_name='方法对比', index=False)
        
        # Sheet 6: 数据说明
        desc_data = [
            ['Sheet名称', '说明'],
            ['评估指标', '整体模型性能指标'],
            ['投票估计汇总', '每周每位选手的投票估计结果；含确定性Φ=1/std(p^MCMC)（使用--mcmc时）'],
            ['各赛季一致性', '每个赛季的一致性统计'],
            ['争议案例分析', '争议选手的详细分析'],
            ['方法对比', '排名制与百分比制的对比结果'],
            ['', ''],
            ['字段说明', ''],
            ['估计投票比例', '模型估计的粉丝投票比例（0-1之间）'],
            ['一致性', '预测的淘汰概率与实际淘汰者的匹配度'],
            ['预测正确', '预测的淘汰者是否与实际一致（True/False）'],
            ['粉丝票弥补程度', '投票排名 - 评委排名（正值表示粉丝更支持）'],
        ]
        desc_df = pd.DataFrame(desc_data[1:], columns=desc_data[0])
        desc_df.to_excel(writer, sheet_name='数据说明', index=False)
    
    print(f"  ✓ Excel 文件已保存: {excel_path}")
    print(f"    包含 {len([s for s in writer.sheets if s])} 个 Sheet")
    print(f"  结果已保存到 {output_dir}/")


def main():
    """主函数"""
    args = parse_args()
    
    print("="*70)
    print("DWTS 粉丝投票估计分析")
    print("基于逆向决策理论 (Inverse Decision-Making)")
    print("MCM 2026 Problem C")
    print("="*70)
    print(f"\n运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据文件: {args.data}")
    print(f"使用MCMC: {args.mcmc}")
    
    # 1. 创建输出目录
    output_dir = ensure_output_dir(args.output)
    
    # 2. 加载数据
    print("\n[1/6] 加载数据...")
    try:
        if not os.path.exists(args.data):
            if args.data.endswith('.xlsx') or args.data.endswith('.xls'):
                print(f"  错误: 找不到处理后的 Excel 文件 {args.data}")
                print("  请先运行预处理生成 Excel:")
                print("    python data_preprocessing.py")
                print("  或指定原始 CSV 后由本程序自动预处理:")
                print("    python run_analysis.py --data 2026_MCM_Problem_C_Data.csv")
            else:
                print(f"  错误: 找不到数据文件 {args.data}")
            sys.exit(1)
        df = load_and_preprocess_data(args.data)
        print(f"  成功加载 {len(df)} 条记录，{df['season'].nunique()} 个赛季")
    except FileNotFoundError:
        print(f"  错误: 找不到数据文件 {args.data}")
        print("  若使用默认 Excel，请先运行: python data_preprocessing.py")
        sys.exit(1)
    except Exception as e:
        print(f"  错误: {e}")
        sys.exit(1)
    
    # 确定要分析的赛季
    if args.seasons:
        seasons = args.seasons
    else:
        # 默认分析所有赛季，但先用部分赛季测试
        all_seasons = sorted(df['season'].unique())
        # 可以选择只分析部分赛季以加快速度
        seasons = all_seasons  # 或者用 all_seasons[:5] 测试
    
    print(f"  将分析的赛季: {seasons}")
    
    # 3. 运行主要分析
    print("\n[2/6] 运行IDM投票估计...")
    results, metrics = run_main_analysis(df, seasons, use_mcmc=args.mcmc, verbose=args.verbose)
    
    print(f"\n  分析完成!")
    print(f"  分析周数: {metrics['n_weeks_analyzed']}")
    print(f"  平均一致性: {metrics['mean_consistency']:.4f}")
    print(f"  硬一致性准确率: {metrics['hard_accuracy']*100:.2f}%")
    
    # 4. 争议案例分析
    print("\n[3/6] 分析争议案例...")
    controversy_results = run_controversy_analysis(df, results, verbose=args.verbose)
    
    # 5. 方法对比分析
    print("\n[4/6] 对比投票方法...")
    comparison_results = run_method_comparison(df, results, verbose=args.verbose)
    
    # 6. 生成可视化
    print("\n[5/6] 生成可视化图表...")
    generate_visualizations(results, controversy_results, comparison_results, output_dir)
    
    # 7. 保存结果
    print("\n[6/6] 保存结果...")
    save_results(results, metrics, controversy_results, comparison_results, output_dir)
    
    # 输出最终摘要
    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)
    print(f"\n输出文件位置: {os.path.abspath(output_dir)}/")
    print("  - metrics.json: 评估指标")
    print("  - vote_estimates.json: 详细投票估计")
    print("  - controversy_analysis.json: 争议案例分析")
    print("  - summary_report.txt: 文本摘要报告")
    print("  - paper_fig_*.png: 论文用汇总图（含一致性、争议、投票方法、确定性Φ汇总及 4 张单周案例）")
    
    return results, metrics


if __name__ == "__main__":
    results = main()
