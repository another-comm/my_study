"""
对每个季度采用名次法(Rank)与百分比法(Percent)两种投票综合方式，
对比两种方法在各周淘汰结果上是否有差异，并汇总到 Excel。
含三张论文用图（英文标题）：方法一致率、差异周数、两方法与实际一致度对比。
"""

import json
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# English labels for paper figures
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_vote_estimates(json_path):
    """加载粉丝投票预估结果"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def rank_method_eliminated(contestants, judge_scores, votes_map):
    """
    名次法：评委名次 + 观众名次，名次和最大者被淘汰。
    名次 1 = 最好（分数最高/票数最高）。
    """
    judge_scores = np.asarray(judge_scores, dtype=float)
    votes_map = np.asarray(votes_map, dtype=float)
    n = len(contestants)
    # 评委名次：分数越高名次越好(1=最好)，相同分数给平均名次
    judge_rank = _rank_descending(judge_scores)   # 1 = highest score
    fan_rank = _rank_descending(votes_map)       # 1 = highest votes
    sum_ranks = judge_rank + fan_rank
    worst = np.max(sum_ranks)
    # 取名次和最大者（若有并列取第一个，与题目惯例一致）
    idx = np.where(sum_ranks == worst)[0]
    return [contestants[i] for i in idx]


def percent_method_eliminated(contestants, judge_scores, votes_map):
    """
    百分比法：评委得分占比 + 观众票数占比，综合占比最低者被淘汰。
    votes_map 已是比例（和为1），直接作为观众占比。
    """
    judge_scores = np.asarray(judge_scores, dtype=float)
    votes_map = np.asarray(votes_map, dtype=float)
    total_judge = np.sum(judge_scores)
    if total_judge <= 0:
        judge_pct = np.ones(len(contestants)) / len(contestants)
    else:
        judge_pct = judge_scores / total_judge
    combined = judge_pct + votes_map
    lowest = np.min(combined)
    idx = np.where(combined == lowest)[0]
    return [contestants[i] for i in idx]


def _rank_descending(values):
    """分数/票数越高名次越好：1=最好。同分给平均名次。"""
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    order = np.argsort(-arr)  # 降序
    ranks = np.empty(n, dtype=float)
    i = 0
    while i < n:
        j = i
        while j < n and arr[order[j]] == arr[order[i]]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = avg_rank
        i = j
    return ranks


def compare_all_seasons(data):
    """遍历所有赛季、所有周，分别用两种方法计算淘汰者并对比"""
    rows_weekly = []
    for season_key, season_data in data.items():
        if not isinstance(season_data, dict) or 'weeks' not in season_data:
            continue
        season = season_data.get('season', int(season_key))
        weeks_data = season_data['weeks']
        for week_key, week_data in weeks_data.items():
            if not isinstance(week_data, dict):
                continue
            contestants = week_data.get('contestants', [])
            judge_scores = week_data.get('judge_scores', [])
            votes_map = week_data.get('votes_map', [])
            actual_eliminated = week_data.get('eliminated', [])
            if not contestants or len(judge_scores) != len(contestants) or len(votes_map) != len(contestants):
                continue
            # 两种方法得到的淘汰者（列表，可能并列）
            rank_elim = rank_method_eliminated(contestants, judge_scores, votes_map)
            percent_elim = percent_method_eliminated(contestants, judge_scores, votes_map)
            # 取“主淘汰者”：两种方法都取第一个（便于对比）
            rank_one = rank_elim[0] if rank_elim else ""
            percent_one = percent_elim[0] if percent_elim else ""
            actual_one = actual_eliminated[0] if actual_eliminated else ""
            methods_agree = set(rank_elim) == set(percent_elim)
            rank_match_actual = actual_one in rank_elim if actual_one else None
            percent_match_actual = actual_one in percent_elim if actual_one else None
            rows_weekly.append({
                'season': season,
                'week': int(week_key),
                'actual_eliminated': actual_one,
                'rank_method_eliminated': rank_one,
                'percent_method_eliminated': percent_one,
                'methods_agree': methods_agree,
                'rank_match_actual': rank_match_actual,
                'percent_match_actual': percent_match_actual,
                'n_contestants': len(contestants),
            })
    return pd.DataFrame(rows_weekly)


def season_summary(df_weekly):
    """按赛季汇总：总周数、与真实一致周数、两种方法一致周数等"""
    if df_weekly.empty:
        return pd.DataFrame()
    summary = []
    for season in sorted(df_weekly['season'].unique()):
        sub = df_weekly[df_weekly['season'] == season]
        total = len(sub)
        rank_match = sub['rank_match_actual'].sum()
        percent_match = sub['percent_match_actual'].sum()
        methods_agree = sub['methods_agree'].sum()
        methods_differ = total - methods_agree
        diff_weeks = sub.loc[~sub['methods_agree'], 'week'].tolist()
        summary.append({
            'season': season,
            'total_weeks': total,
            'weeks_rank_match_actual': int(rank_match),
            'weeks_percent_match_actual': int(percent_match),
            'weeks_methods_agree': int(methods_agree),
            'weeks_methods_differ': int(methods_differ),
            'pct_methods_agree': round(100.0 * methods_agree / total, 2) if total else 0,
            'weeks_where_methods_differ': ','.join(map(str, diff_weeks)) if diff_weeks else '',
        })
    return pd.DataFrame(summary)


def plot_voting_method_figures(df_weekly, df_summary, out_dir):
    """
    Generate up to 3 paper-ready figures (all titles in English).
    df_weekly, df_summary: use original English column names.
    """
    os.makedirs(out_dir, exist_ok=True)
    seasons = sorted(df_summary['season'].unique())
    x = np.arange(len(seasons))
    width = 0.35

    # -------------------------------------------------------------------------
    # Figure 1: Agreement rate between Rank and Percent methods by season
    # -------------------------------------------------------------------------
    fig1, ax1 = plt.subplots(figsize=(10, 4.5))
    agree_pct = df_summary.sort_values('season')['pct_methods_agree'].values
    ax1.bar(x, agree_pct, color='steelblue', alpha=0.85, edgecolor='navy', linewidth=0.5)
    ax1.axhline(y=agree_pct.mean(), color='gray', linestyle='--', linewidth=1, label=f'Mean = {agree_pct.mean():.1f}%')
    ax1.set_xticks(x)
    ax1.set_xticklabels(seasons, rotation=0)
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Agreement Rate (%)')
    ax1.set_title('Agreement Rate Between Rank and Percent Methods by Season')
    ax1.set_ylim(0, 105)
    ax1.legend(loc='lower left', fontsize=9)
    ax1.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig1.savefig(os.path.join(out_dir, 'fig_agreement_rate_by_season.png'), dpi=150, bbox_inches='tight')
    plt.close(fig1)
    print(f"  Saved: {os.path.join(out_dir, 'fig_agreement_rate_by_season.png')}")

    # -------------------------------------------------------------------------
    # Figure 2: Number of weeks with different outcomes (Rank vs Percent) by season
    # -------------------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(10, 4.5))
    diff_weeks = df_summary.sort_values('season')['weeks_methods_differ'].values
    total_weeks = df_summary.sort_values('season')['total_weeks'].values
    colors = plt.cm.Reds(0.4 + 0.5 * (diff_weeks / (total_weeks.max() or 1)))
    ax2.bar(x, diff_weeks, color=colors, edgecolor='darkred', linewidth=0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(seasons, rotation=0)
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Number of Weeks')
    ax2.set_title('Weeks with Different Elimination Results: Rank vs Percent Method')
    ax2.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig2.savefig(os.path.join(out_dir, 'fig_disagreement_weeks_by_season.png'), dpi=150, bbox_inches='tight')
    plt.close(fig2)
    print(f"  Saved: {os.path.join(out_dir, 'fig_disagreement_weeks_by_season.png')}")

    # -------------------------------------------------------------------------
    # Figure 3: Accuracy of each method vs. actual elimination by season
    # -------------------------------------------------------------------------
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    rank_match = df_summary.sort_values('season')['weeks_rank_match_actual'].values
    percent_match = df_summary.sort_values('season')['weeks_percent_match_actual'].values
    total_weeks_sorted = df_summary.sort_values('season')['total_weeks'].values
    b1 = ax3.bar(x - width / 2, rank_match, width, label='Rank method matches actual', color='steelblue', alpha=0.85)
    b2 = ax3.bar(x + width / 2, percent_match, width, label='Percent method matches actual', color='coral', alpha=0.85)
    ax3.set_xticks(x)
    ax3.set_xticklabels(seasons, rotation=0)
    ax3.set_xlabel('Season')
    ax3.set_ylabel('Number of Weeks Matching Actual Elimination')
    ax3.set_title('Accuracy of Rank vs Percent Method Against Actual Outcomes by Season')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig3.savefig(os.path.join(out_dir, 'fig_accuracy_rank_vs_percent_by_season.png'), dpi=150, bbox_inches='tight')
    plt.close(fig3)
    print(f"  Saved: {os.path.join(out_dir, 'fig_accuracy_rank_vs_percent_by_season.png')}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    # 投票估计由 problem1 生成，从 problem1/results 读取
    json_path = os.path.join(project_root, 'problem1', 'results', 'vote_estimates.json')
    out_dir = os.path.join(base_dir, 'results')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'voting_methods_comparison.xlsx')

    if not os.path.exists(json_path):
        print(f"错误: 未找到 {json_path}")
        print("  请先运行 problem1 的 run_analysis.py 生成 vote_estimates.json")
        return

    print("加载粉丝投票预估...")
    data = load_vote_estimates(json_path)

    print("对各赛季各周应用名次法与百分比法并对比...")
    df_weekly = compare_all_seasons(data)
    df_summary = season_summary(df_weekly)

    print(f"共 {len(df_weekly)} 条周记录, {len(df_summary)} 个赛季")

    # Visualization: 3 paper figures (English titles)
    print("\n生成论文用图（英文标题）...")
    plot_voting_method_figures(df_weekly, df_summary, out_dir)

    # 中文列名便于报告使用
    weekly_cn = {
        'season': '赛季', 'week': '周次', 'actual_eliminated': '实际淘汰',
        'rank_method_eliminated': '名次法淘汰', 'percent_method_eliminated': '百分比法淘汰',
        'methods_agree': '两种方法一致', 'rank_match_actual': '名次法与实际一致',
        'percent_match_actual': '百分比法与实际一致', 'n_contestants': '当周选手数',
    }
    summary_cn = {
        'season': '赛季', 'total_weeks': '总周数',
        'weeks_rank_match_actual': '名次法与实际一致周数', 'weeks_percent_match_actual': '百分比法与实际一致周数',
        'weeks_methods_agree': '两种方法一致周数', 'weeks_methods_differ': '两种方法不一致周数',
        'pct_methods_agree': '方法一致率(%)', 'weeks_where_methods_differ': '方法不一致的周次',
    }
    df_weekly_cn = df_weekly.rename(columns=weekly_cn)
    df_summary_cn = df_summary.rename(columns=summary_cn)

    # 写入 Excel
    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        df_weekly_cn.to_excel(writer, sheet_name='按周对比', index=False)
        df_summary_cn.to_excel(writer, sheet_name='按季汇总', index=False)
        # 差异明细：仅保留两种方法不一致的周
        df_diff = df_weekly_cn[~df_weekly_cn['两种方法一致']].copy()
        if not df_diff.empty:
            df_diff.to_excel(writer, sheet_name='方法差异明细', index=False)
        else:
            pd.DataFrame(columns=df_weekly_cn.columns).to_excel(writer, sheet_name='方法差异明细', index=False)

    print(f"结果已保存: {out_path}")
    print("\n按季汇总预览:")
    print(df_summary_cn.to_string(index=False))
    n_differ = (~df_weekly_cn['两种方法一致']).sum()
    print(f"\n两种方法结果不一致的周数: {n_differ} / {len(df_weekly_cn)}")


if __name__ == '__main__':
    main()
