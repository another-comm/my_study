"""
为 LME 影响分析构建选手-赛季层面数据：
评委均分、观众票均占比、年龄、行业、职业舞伴、季节等。
"""

import os
import re
import json
import pandas as pd
import numpy as np


def load_raw_with_week_totals(data_dir):
    """加载原始数据并计算每周评委总分。data_dir 通常为项目根目录。"""
    excel_path = os.path.join(data_dir, '2026_MCM_Problem_C_Data_processed.xlsx')
    csv_path = os.path.join(data_dir, '2026_MCM_Problem_C_Data.csv')
    if os.path.exists(excel_path):
        try:
            from data_preprocessing import load_processed_excel
            df = load_processed_excel(excel_path)
        except Exception:
            df = pd.read_excel(excel_path, sheet_name='数据', engine='openpyxl')
    else:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        df = _parse_and_add_week_totals(df)
    return _ensure_types(df)


def _ensure_types(df):
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


def compute_mean_judge_score_and_weeks(df):
    """选手-赛季：评委均分、参赛周数"""
    score_cols = [c for c in df.columns if 'total_score' in c and c.startswith('week')]
    rows = []
    for _, row in df.iterrows():
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
            'season': int(season),
            'mean_judge_score': round(mean_score, 4) if not np.isnan(mean_score) else np.nan,
            'weeks_competed': weeks_competed,
        })
    return pd.DataFrame(rows)


def aggregate_fan_vote_share(vote_estimates_path):
    """
    从 vote_estimates.json 按 (celebrity_name, season) 聚合平均观众票占比。
    返回 DataFrame: celebrity_name, season, mean_fan_vote_share
    """
    with open(vote_estimates_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # (name, season) -> list of vote shares in that season
    accum = {}
    for season_key, season_data in data.items():
        if not isinstance(season_data, dict) or 'weeks' not in season_data:
            continue
        season = season_data.get('season', int(season_key))
        for week_key, week_data in season_data.get('weeks', {}).items():
            if not isinstance(week_data, dict):
                continue
            contestants = week_data.get('contestants', [])
            votes_map = week_data.get('votes_map', [])
            if len(contestants) != len(votes_map):
                continue
            for name, share in zip(contestants, votes_map):
                key = (name, season)
                if key not in accum:
                    accum[key] = []
                try:
                    accum[key].append(float(share))
                except (ValueError, TypeError):
                    pass
    rows = []
    for (name, season), shares in accum.items():
        if not shares:
            continue
        rows.append({
            'celebrity_name': name,
            'season': season,
            'mean_fan_vote_share': round(np.mean(shares), 6),
            'n_weeks_fan_vote': len(shares),
        })
    return pd.DataFrame(rows)


def build_analysis_table(base_dir=None):
    """
    构建 LME 分析用表：一行 = 选手-赛季。
    列：celebrity_name, season, age, industry, ballroom_partner, mean_judge_score,
        mean_fan_vote_share, placement, weeks_competed.
    数据与 vote_estimates 从项目根与 problem1/results 读取。
    """
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    df = load_raw_with_week_totals(project_root)
    # 选手层面特征（取该季第一条即可，同一人在同季同一条记录）
    covar = df[['celebrity_name', 'season', 'celebrity_age_during_season', 'celebrity_industry',
                'ballroom_partner', 'placement', 'elimination_week']].copy()
    covar = covar.rename(columns={
        'celebrity_age_during_season': 'age',
        'celebrity_industry': 'industry',
        'ballroom_partner': 'pro_dancer',
    })
    covar['age'] = pd.to_numeric(covar['age'], errors='coerce')
    # 评委均分与参赛周数
    judge_df = compute_mean_judge_score_and_weeks(df)
    covar = covar.merge(judge_df, on=['celebrity_name', 'season'], how='left')
    # 观众票占比（由 problem1 生成，从 problem1/results 读取）
    vote_path = os.path.join(project_root, 'problem1', 'results', 'vote_estimates.json')
    if os.path.exists(vote_path):
        fan_df = aggregate_fan_vote_share(vote_path)
        covar = covar.merge(fan_df[['celebrity_name', 'season', 'mean_fan_vote_share']],
                            on=['celebrity_name', 'season'], how='left')
    else:
        covar['mean_fan_vote_share'] = np.nan
    # 去重：同一人同季只保留一行（数据应已唯一）
    covar = covar.drop_duplicates(subset=['celebrity_name', 'season']).reset_index(drop=True)
    return covar
