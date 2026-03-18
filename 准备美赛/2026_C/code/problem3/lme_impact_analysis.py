# -*- coding: utf-8 -*-
"""
线性混合效应模型 (LME) 分析：职业舞者与嘉宾特征对竞赛表现的影响。
双路径：路径 A 评委分（技术）、路径 B 粉丝票（人气）。
固定效应：年龄、行业；随机效应：职业舞者（随机截距）。
"""

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.formula.api import mixedlm
from statsmodels.regression.mixed_linear_model import MixedLMResults

# 设置绘图中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


# =============================================================================
# 1. 数据加载与合并
# =============================================================================

def load_base_data(data_dir):
    """加载预处理数据表（数据 sheet）。data_dir 通常为项目根目录。"""
    path = os.path.join(data_dir, '2026_MCM_Problem_C_Data_processed.xlsx')
    df = pd.read_excel(path, sheet_name='数据', engine='openpyxl')
    df['season'] = pd.to_numeric(df['season'], errors='coerce').fillna(0).astype(int)
    df['elimination_week'] = df['elimination_week'].apply(_to_int_or_none)
    return df


def _to_int_or_none(x):
    if pd.isna(x):
        return None
    try:
        v = float(x)
        return int(v) if v == int(v) else None
    except (ValueError, TypeError):
        return None


def compute_mean_judge_score(df):
    """
    按选手-赛季计算「平均评委分」：仅对参赛周取 weekX_avg_score 的均值。
    淘汰周之后的周不纳入计算。若无 weekX_avg_score 则用 weekX_total_score / weekX_judge_count 近似。
    """
    avg_cols = [c for c in df.columns if re.match(r'week\d+_avg_score', c)]
    total_cols = [c for c in df.columns if re.match(r'week\d+_total_score', c)]
    count_cols = [c for c in df.columns if re.match(r'week\d+_judge_count', c)]
    if not avg_cols and total_cols and count_cols:
        avg_cols = []
        for tc in sorted(total_cols, key=lambda x: int(re.search(r'week(\d+)_', x).group(1))):
            w = re.search(r'week(\d+)_', tc).group(1)
            cc = next((c for c in count_cols if c.startswith(f'week{w}_')), None)
            if cc is not None:
                avg_cols.append((tc, cc))
    use_ratio = isinstance(avg_cols and avg_cols[0], tuple)
    if not use_ratio and avg_cols:
        avg_cols = sorted(avg_cols, key=lambda x: int(re.search(r'week(\d+)_', x).group(1)))
    rows = []
    for idx, row in df.iterrows():
        season = row['season']
        elim_week = row['elimination_week']
        scores = []
        if use_ratio and avg_cols:
            for (tc, cc) in avg_cols:
                w = int(re.search(r'week(\d+)_', tc).group(1))
                if elim_week is not None and w > elim_week:
                    continue
                t, c = row[tc], row[cc]
                if pd.isna(t) or pd.isna(c) or c == 0:
                    continue
                try:
                    s = float(t) / float(c)
                    if s > 0:
                        scores.append(s)
                except (ValueError, TypeError):
                    pass
        elif avg_cols:
            for col in avg_cols:
                w = int(re.search(r'week(\d+)_', col).group(1))
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
        rows.append({
            'celebrity_name': row['celebrity_name'],
            'season': int(season),
            'mean_judge_score': round(mean_score, 4) if not np.isnan(mean_score) else np.nan,
        })
    return pd.DataFrame(rows)


def load_fan_vote_summary(problem1_results_dir):
    """加载投票估计汇总（由 problem1 生成）。problem1_results_dir 为 problem1/results 的路径。"""
    path = os.path.join(problem1_results_dir, 'analysis_results.xlsx')
    df = pd.read_excel(path, sheet_name='投票估计汇总', engine='openpyxl')
    # 列名可能是中文：选手姓名, 赛季, 估计投票比例
    name_col = '选手姓名' if '选手姓名' in df.columns else 'celebrity_name'
    season_col = '赛季' if '赛季' in df.columns else 'season'
    vote_col = '估计投票比例' if '估计投票比例' in df.columns else 'mean_fan_vote_share'
    agg = df.groupby([name_col, season_col], as_index=False)[vote_col].mean()
    agg = agg.rename(columns={name_col: 'celebrity_name', season_col: 'season', vote_col: 'mean_fan_vote_share'})
    return agg


def merge_base_and_vote(base_df, mean_judge_df, fan_vote_df):
    """合并：基础表（每行选手-赛季）+ 评委均分 + 粉丝票均占比。"""
    # 基础表每行已是选手-赛季，取协变量
    covar = base_df[['celebrity_name', 'season', 'celebrity_age_during_season', 'celebrity_industry', 'ballroom_partner']].drop_duplicates(subset=['celebrity_name', 'season'])
    covar = covar.merge(mean_judge_df, on=['celebrity_name', 'season'], how='left')
    covar = covar.merge(fan_vote_df, on=['celebrity_name', 'season'], how='left')
    return covar


# =============================================================================
# 2. 数据清洗：年龄标准化、行业聚类
# =============================================================================

def cluster_industry(industry_series):
    """
    将 celebrity_industry 聚类为：Sports, Actors, Music, Social_Media, Other。
    返回与 industry_series 同长的 Series。
    """
    def map_one(s):
        if pd.isna(s) or s == '':
            return 'Other'
        s = str(s).lower().strip()
        if 'athlete' in s or 'sport' in s:
            return 'Sports'
        if 'actor' in s or 'actress' in s:
            return 'Actors'
        if 'singer' in s or 'rapper' in s or 'music' in s:
            return 'Music'
        if 'reality' in s or 'tv personality' in s or 'model' in s or 'social' in s or 'influencer' in s or 'beauty' in s:
            return 'Social_Media'
        if 'news' in s or 'politician' in s or 'anchor' in s:
            return 'Other'
        return 'Other'
    return industry_series.apply(map_one)


def clean_and_prepare(df):
    """
    数据清洗：年龄标准化、行业聚类；剔除关键缺失。
    新增列：age_std, industry_cluster。
    """
    df = df.copy()
    df['age'] = pd.to_numeric(df['celebrity_age_during_season'], errors='coerce')
    df['industry_cluster'] = cluster_industry(df['celebrity_industry'])
    # 年龄标准化（在全体样本上）
    age_mean = df['age'].mean()
    age_std_val = df['age'].std()
    df['age_std'] = (df['age'] - age_mean) / age_std_val if age_std_val and age_std_val > 0 else 0.0
    # 剔除因变量或关键自变量缺失
    df = df.dropna(subset=['mean_judge_score', 'age_std', 'industry_cluster', 'ballroom_partner'])
    df = df.dropna(subset=['mean_fan_vote_share'])  # 粉丝模型需要粉丝票
    return df


# =============================================================================
# 3. 线性混合效应模型 (LME)
# =============================================================================

def fit_lme_judge(data):
    """路径 A（技术模型）：因变量 = mean_judge_score，固定效应 = 年龄 + 行业，随机截距 = ballroom_partner。"""
    model = mixedlm(
        'mean_judge_score ~ age_std + C(industry_cluster)',
        data=data,
        groups=data['ballroom_partner'],
    )
    return model.fit(reml=True)


def fit_lme_fan(data):
    """路径 B（人气模型）：因变量 = mean_fan_vote_share，固定效应 = 年龄 + 行业，随机截距 = ballroom_partner。"""
    model = mixedlm(
        'mean_fan_vote_share ~ age_std + C(industry_cluster)',
        data=data,
        groups=data['ballroom_partner'],
    )
    return model.fit(reml=True)


def compute_icc(result: MixedLMResults):
    """
    组内相关系数 ICC = Var(随机截距) / [Var(随机截距) + Var(残差)]。
    表示组（职业舞者）对因变量变异的贡献占比。
    """
    try:
        cov_re = result.cov_re
        if hasattr(cov_re, 'iloc'):
            var_u = float(cov_re.iloc[0, 0])
        else:
            var_u = float(np.asarray(cov_re).ravel()[0])
    except Exception:
        var_u = 0.0
    scale = float(result.scale)  # 残差方差
    total = var_u + scale
    icc = var_u / total if total > 0 else 0.0
    return icc, var_u, scale


# =============================================================================
# 4. 系数对比与可视化
# =============================================================================

def get_fixed_effect_names_and_coefs(result):
    """提取固定效应名称与系数（不含截距与 Group Var，仅年龄与行业）。"""
    names = list(result.params.index)
    coefs = result.params.values
    skip = {'Intercept', 'Group Var'}
    out = []
    for n, c in zip(names, coefs):
        if n in skip:
            continue
        out.append((n, float(c)))
    return out


def map_param_name_to_cn(name):
    """将公式中的参数名映射为中文（用于图表）。"""
    if name == 'age_std':
        return '年龄（标准化）'
    s = str(name)
    if 'industry_cluster' in s:
        # C(industry_cluster)[T.xxx] -> 行业：xxx
        if 'T.Actors' in s:
            return '行业：演员'
        if 'T.Music' in s:
            return '行业：音乐'
        if 'T.Social_Media' in s:
            return '行业：综艺/模特/社交'
        if 'T.Sports' in s:
            return '行业：体育'
        return '行业（参照：Other）'
    return name


def plot_coefficient_comparison(result_judge, result_fan, out_path):
    """
    绘制评委模型 vs 粉丝模型中「年龄」与「行业」系数的对比图（中文标题与坐标轴）。
    """
    fe_judge = get_fixed_effect_names_and_coefs(result_judge)
    fe_fan = get_fixed_effect_names_and_coefs(result_fan)
    # 统一变量顺序（按评委模型顺序）
    labels_cn = [map_param_name_to_cn(n) for n, _ in fe_judge]
    coef_judge = [c for _, c in fe_judge]
    name_to_fan = dict(fe_fan)
    coef_fan = [name_to_fan.get(n, np.nan) for n, _ in fe_judge]
    x = np.arange(len(labels_cn))
    w = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar(x - w / 2, coef_judge, w, label='评委分模型（技术）', color='steelblue', alpha=0.85)
    bars2 = ax.bar(x + w / 2, coef_fan, w, label='粉丝票模型（人气）', color='coral', alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels_cn, rotation=15, ha='right')
    ax.set_ylabel('系数估计值')
    ax.set_xlabel('特征')
    ax.set_title('固定效应系数对比：评委分 vs 粉丝票')
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax.legend(loc='best', fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  对比图已保存: {out_path}")


# =============================================================================
# 5. 主流程
# =============================================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    problem1_results = os.path.join(project_root, 'problem1', 'results')

    # 1) 加载数据（基础数据从项目根，投票汇总从 problem1/results）
    print("【1】加载数据...")
    base_df = load_base_data(project_root)
    mean_judge_df = compute_mean_judge_score(base_df)
    fan_vote_df = load_fan_vote_summary(problem1_results)
    df = merge_base_and_vote(base_df, mean_judge_df, fan_vote_df)
    print(f"  合并后样本量: {len(df)}")

    # 2) 数据清洗
    print("\n【2】数据清洗：年龄标准化、行业聚类...")
    df = clean_and_prepare(df)
    print(f"  清洗后样本量: {len(df)}")
    print(f"  行业聚类分布:\n{df['industry_cluster'].value_counts().to_string()}")

    # 3) 拟合双路径 LME
    print("\n【3】拟合线性混合效应模型 (LME)...")
    result_judge = fit_lme_judge(df)
    result_fan = fit_lme_fan(df)

    # 4) 打印两个模型的汇总表
    print("\n" + "=" * 70)
    print("路径 A（技术模型）：因变量 = 平均评委分 (weekX_avg_score 均值)")
    print("=" * 70)
    print(result_judge.summary())

    print("\n" + "=" * 70)
    print("路径 B（人气模型）：因变量 = 估计粉丝投票比例")
    print("=" * 70)
    print(result_fan.summary())

    # 5) ICC
    print("\n【4】组内相关系数 (ICC)：职业舞者对分数的贡献占比")
    icc_judge, var_u_j, scale_j = compute_icc(result_judge)
    icc_fan, var_u_f, scale_f = compute_icc(result_fan)
    print(f"  评委分模型: ICC = {icc_judge:.4f}  (随机效应方差={var_u_j:.6f}, 残差方差={scale_j:.6f})")
    print(f"  粉丝票模型: ICC = {icc_fan:.4f}  (随机效应方差={var_u_f:.6f}, 残差方差={scale_f:.6f})")

    # 6) 年龄与行业系数差异对比
    print("\n【5】评委模型 vs 粉丝模型：年龄与行业系数对比")
    fe_judge = get_fixed_effect_names_and_coefs(result_judge)
    fe_fan = dict(get_fixed_effect_names_and_coefs(result_fan))
    for name, cj in fe_judge:
        cf = fe_fan.get(name, np.nan)
        diff = (cf - cj) if not np.isnan(cf) else np.nan
        print(f"  {map_param_name_to_cn(name)}:  评委系数={cj:.4f},  粉丝系数={cf:.4f},  差异={diff:.4f}")

    # 7) 可视化（输出到本问题目录的 results）
    print("\n【6】生成系数对比图...")
    results_dir = os.path.join(base_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    plot_coefficient_comparison(result_judge, result_fan, os.path.join(results_dir, 'lme_coefficient_comparison.png'))

    print("\n分析完成。")


if __name__ == '__main__':
    main()
