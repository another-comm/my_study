"""
找出「评委高分却早淘汰」与「评委低分却晚淘汰或最终成绩很好」的案例。
即：评委与观众意见分歧的典型样本。

筛选标准（可在脚本内调整）：
1. 评委高分早淘汰：当季评委平均分名次在前半（1=最高），且淘汰周次 ≤ 5。
2. 评委低分晚淘汰或成绩好（严格）：当季评委名次在最后3名，且满足其一：淘汰周≥8、或最终名次 1/2/3。

输出：本目录 results/judge_fan_divergence_cases.xlsx
  - 评委高分早淘汰 / 评委低分晚淘汰或成绩好 / 全部选手统计
  - 数据从项目根目录读取
"""

import os
import re
import pandas as pd
import numpy as np


def load_data(data_dir):
    """优先加载预处理 Excel，否则从 CSV 计算每周总分。data_dir 通常为项目根目录。"""
    excel_path = os.path.join(data_dir, '2026_MCM_Problem_C_Data_processed.xlsx')
    csv_path = os.path.join(data_dir, '2026_MCM_Problem_C_Data.csv')

    if os.path.exists(excel_path):
        try:
            from data_preprocessing import load_processed_excel
            return load_processed_excel(excel_path)
        except Exception:
            df = pd.read_excel(excel_path, sheet_name='数据', engine='openpyxl')
            return _ensure_types(df)
    # 从 CSV 加载并计算每周总分
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df = _parse_and_add_week_totals(df)
    return df


def _ensure_types(df):
    """确保 season, placement, elimination_week 类型正确"""
    if 'season' in df.columns:
        df['season'] = pd.to_numeric(df['season'], errors='coerce').fillna(0).astype(int)
    if 'placement' in df.columns:
        df['placement'] = pd.to_numeric(df['placement'], errors='coerce').fillna(0).astype(int)
    if 'elimination_week' in df.columns:
        def to_elim(x):
            if pd.isna(x): return None
            try:
                v = float(x)
                return int(v) if v == int(v) else None
            except (ValueError, TypeError):
                return None
        df['elimination_week'] = df['elimination_week'].apply(to_elim)
    return df


def _parse_and_add_week_totals(df):
    """从原始 CSV 解析 elimination_week 并计算每周评委总分"""
    def extract_elimination_week(result_str):
        if pd.isna(result_str): return None
        s = str(result_str).lower().strip()
        if 'eliminated week' in s:
            m = re.search(r'week\s*(\d+)', s)
            return int(m.group(1)) if m else None
        return None

    df['elimination_week'] = df['results'].apply(extract_elimination_week)
    df['season'] = pd.to_numeric(df['season'], errors='coerce').fillna(0).astype(int)
    df['placement'] = pd.to_numeric(df['placement'], errors='coerce').fillna(0).astype(int)

    judge_cols = [c for c in df.columns if 'week' in c.lower() and 'judge' in c.lower() and 'score' in c.lower()]
    weeks = set()
    for c in judge_cols:
        for part in c.split('_'):
            if part.startswith('week'):
                try:
                    weeks.add(int(part.replace('week', '')))
                except ValueError:
                    pass
                break

    for week in sorted(weeks):
        cols = [c for c in judge_cols if c.startswith(f'week{week}_')]
        if not cols:
            continue
        def total(row):
            s = 0
            for c in cols:
                v = row[c]
                if pd.isna(v) or v == 'N/A' or v == '': continue
                try:
                    s += float(v)
                except (ValueError, TypeError):
                    pass
            return s if s > 0 else np.nan
        df[f'week{week}_total_score'] = df.apply(total, axis=1)
    return _ensure_types(df)


def compute_contestant_stats(df):
    """
    为每位选手计算：参赛周数、评委平均分、在当季的评委名次(1=最高分)。
    """
    score_cols = [c for c in df.columns if 'total_score' in c and c.startswith('week')]
    rows = []
    for idx, row in df.iterrows():
        season = row['season']
        elim_week = row['elimination_week']
        scores = []
        for col in score_cols:
            w = int(col.split('week')[1].split('_')[0])
            if elim_week is not None and w > elim_week:
                continue
            v = row[col]
            if pd.isna(v) or (isinstance(v, (int, float)) and v <= 0):
                continue
            try:
                scores.append(float(v))
            except (ValueError, TypeError):
                pass
        mean_score = np.mean(scores) if scores else np.nan
        weeks_competed = len(scores)
        rows.append({
            'celebrity_name': row['celebrity_name'],
            'season': season,
            'placement': row.get('placement', 0),
            'elimination_week': elim_week,
            'results': row.get('results', ''),
            'weeks_competed': weeks_competed,
            'mean_judge_score': round(mean_score, 4) if not np.isnan(mean_score) else np.nan,
        })
    stats_df = pd.DataFrame(rows)

    # 按赛季计算评委名次：该季内按 mean_judge_score 降序排名，1=最高
    stats_df['judge_rank_in_season'] = np.nan
    for season in stats_df['season'].unique():
        mask = stats_df['season'] == season
        sub = stats_df.loc[mask, 'mean_judge_score'].rank(ascending=False, method='min')
        stats_df.loc[mask, 'judge_rank_in_season'] = sub.astype(int)
    stats_df['n_in_season'] = stats_df.groupby('season')['season'].transform('count')
    return stats_df


def find_high_judge_early_exit(stats_df, early_weeks_max=5, top_half=True):
    """
    评委高分却早淘汰：当季评委名次在前半（或前3），但淘汰周次较早。
    early_weeks_max: 视为「早淘汰」的最大周次，如 5 表示 week 2,3,4,5 淘汰算早。
    top_half: True=名次在前半即算「评委高分」，否则仅取前3名。
    """
    n = stats_df['n_in_season'].iloc[0] if len(stats_df) else 0
    threshold_rank = (np.ceil(n / 2).astype(int)) if top_half else 3
    early = stats_df['elimination_week'].notna() & (stats_df['elimination_week'] <= early_weeks_max)
    high_rank = stats_df['judge_rank_in_season'] <= threshold_rank
    mask = early & high_rank
    return stats_df[mask].copy()


def find_low_judge_late_or_top(stats_df, late_week_min=8, bottom_n=3):
    """
    评委低分却晚淘汰或最终成绩很好（严格版）：当季评委名次在最后 bottom_n 名，且淘汰很晚或最终前三。
    late_week_min: 淘汰周 >= 该值才视为「晚淘汰」（默认 8，比 7 更严）。
    bottom_n: 仅当季评委名次在最后 N 名算「评委低分」（默认 3，即倒数前三）。
    """
    n = stats_df['n_in_season'].iloc[0] if len(stats_df) else 0
    # 评委低分：名次 >= (n - bottom_n + 1)，即最后 bottom_n 名
    rank_threshold = n - bottom_n + 1
    low_rank = stats_df['judge_rank_in_season'] >= rank_threshold
    # 晚淘汰：淘汰周 >= late_week_min；或最终名次 1/2/3（含决赛）
    late_elim = stats_df['elimination_week'].notna() & (stats_df['elimination_week'] >= late_week_min)
    top3_place = (stats_df['placement'] >= 1) & (stats_df['placement'] <= 3)
    late_or_good = late_elim | top3_place
    mask = late_or_good & low_rank
    return stats_df[mask].copy()


def run(base_dir=None):
    """base_dir: 本问题目录，结果写入 base_dir/results；数据从项目根目录读取。"""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    df = load_data(project_root)
    stats_df = compute_contestant_stats(df)

    # 按季筛选
    high_early_list = []
    low_late_list = []
    for season in sorted(stats_df['season'].unique()):
        sub = stats_df[stats_df['season'] == season].copy()
        if len(sub) < 3:
            continue
        h = find_high_judge_early_exit(sub, early_weeks_max=5, top_half=True)
        l = find_low_judge_late_or_top(sub, late_week_min=8, bottom_n=3)
        high_early_list.append(h)
        low_late_list.append(l)

    high_early_df = pd.concat(high_early_list, ignore_index=True) if high_early_list else pd.DataFrame()
    low_late_df = pd.concat(low_late_list, ignore_index=True) if low_late_list else pd.DataFrame()

    # 输出路径
    out_path = os.path.join(base_dir, 'results', 'judge_fan_divergence_cases.xlsx')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 中文列名便于报告使用
    col_cn = {
        'celebrity_name': '选手姓名', 'season': '赛季', 'placement': '最终名次',
        'elimination_week': '淘汰周次', 'results': '结果描述', 'weeks_competed': '参赛周数',
        'mean_judge_score': '评委平均分', 'judge_rank_in_season': '当季评委名次(1最高)',
        'n_in_season': '当季选手数',
    }
    high_cn = high_early_df.rename(columns=col_cn) if not high_early_df.empty else high_early_df
    low_cn = low_late_df.rename(columns=col_cn) if not low_late_df.empty else low_late_df
    stats_cn = stats_df.rename(columns=col_cn)

    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        if not high_cn.empty:
            high_cn.to_excel(writer, sheet_name='评委高分早淘汰', index=False)
        else:
            pd.DataFrame(columns=list(col_cn.values())).to_excel(writer, sheet_name='评委高分早淘汰', index=False)
        if not low_cn.empty:
            low_cn.to_excel(writer, sheet_name='评委低分晚淘汰或成绩好', index=False)
        else:
            pd.DataFrame(columns=list(col_cn.values())).to_excel(writer, sheet_name='评委低分晚淘汰或成绩好', index=False)
        stats_cn.to_excel(writer, sheet_name='全部选手统计', index=False)

    print(f"结果已保存: {out_path}")
    def safe_print(s):
        try:
            print(s)
        except UnicodeEncodeError:
            print(s.encode('gbk', errors='replace').decode('gbk'))
    print("\n【评委高分却早淘汰】 (评委名次在前半且淘汰周≤5)")
    if not high_early_df.empty:
        safe_print(high_early_df[['celebrity_name', 'season', 'elimination_week', 'judge_rank_in_season', 'n_in_season', 'mean_judge_score', 'results']].to_string(index=False))
    else:
        print("  无")
    print("\n【评委低分却晚淘汰或最终成绩很好】 (严格：当季评委最后3名 且 淘汰周≥8 或 最终前三)")
    if not low_late_df.empty:
        safe_print(low_late_df[['celebrity_name', 'season', 'placement', 'elimination_week', 'judge_rank_in_season', 'n_in_season', 'mean_judge_score', 'results']].to_string(index=False))
    else:
        print("  无")
    return high_early_df, low_late_df, stats_df, out_path


if __name__ == '__main__':
    run()
