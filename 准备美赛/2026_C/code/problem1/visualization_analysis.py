import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.special import softmax

def plot_week_votes(week_result, title=None, figsize=(12, 5)):
    contestants = week_result['contestants']
    judge_scores = np.array(week_result['judge_scores'])
    votes_map = np.array(week_result['votes_map'])
    elim_probs = np.array(week_result['elim_probs'])
    eliminated_idx = week_result['eliminated_idx']
    
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    ax1 = axes[0]
    colors = ['red' if i == eliminated_idx else 'steelblue' for i in range(len(contestants))]
    bars1 = ax1.bar(range(len(contestants)), judge_scores, color=colors)
    ax1.set_xticks(range(len(contestants)))
    ax1.set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    ax1.set_ylabel('Judge score')
    ax1.set_title('Judge scores')
    
    ax2 = axes[1]
    bars2 = ax2.bar(range(len(contestants)), votes_map, color=colors)
    ax2.set_xticks(range(len(contestants)))
    ax2.set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    ax2.set_ylabel('Vote proportion')
    ax2.set_title('Estimated fan vote proportion')
    
    ax3 = axes[2]
    bars3 = ax3.bar(range(len(contestants)), elim_probs, color=colors)
    ax3.set_xticks(range(len(contestants)))
    ax3.set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    ax3.set_ylabel('Elimination probability')
    ax3.set_title('Predicted elimination probability')
    
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig


def plot_week_votes_with_uncertainty(week_result, title=None, figsize=(10, 6)):
    if 'votes_mean' not in week_result:
        print("MCMC results are required to display uncertainty")
        return None
    
    contestants = week_result['contestants']
    votes_mean = np.array(week_result['votes_mean'])
    votes_ci_lower = np.array(week_result['votes_ci_lower'])
    votes_ci_upper = np.array(week_result['votes_ci_upper'])
    eliminated_idx = week_result['eliminated_idx']
    
    fig, ax = plt.subplots(figsize=figsize)
    
    x = np.arange(len(contestants))
    colors = ['red' if i == eliminated_idx else 'steelblue' for i in range(len(contestants))]
    
    ax.bar(x, votes_mean, color=colors, alpha=0.7)
    ax.errorbar(x, votes_mean, 
                yerr=[votes_mean - votes_ci_lower, votes_ci_upper - votes_mean],
                fmt='none', color='black', capsize=5)
    
    ax.set_xticks(x)
    ax.set_xticklabels(contestants, rotation=45, ha='right')
    ax.set_ylabel('Vote proportion')
    ax.set_title(title or 'Fan vote estimates (95% CI)')
    
    plt.tight_layout()
    return fig


def plot_season_consistency(season_result, figsize=(12, 5)):
    weeks = sorted(season_result['weeks'].keys())
    consistencies = [season_result['weeks'][w]['consistency'] for w in weeks]
    hard_consistencies = [season_result['weeks'][w]['is_consistent'] for w in weeks]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    ax1.plot(weeks, consistencies, 'o-', color='steelblue', linewidth=2, markersize=8)
    ax1.axhline(y=np.mean(consistencies), color='red', linestyle='--', label=f'Mean: {np.mean(consistencies):.3f}')
    ax1.set_xlabel('Week')
    ax1.set_ylabel('Consistency')
    ax1.set_title(f'Season {season_result["season"]} - soft consistency')
    ax1.legend()
    ax1.set_ylim(0, 1)
    
    colors = ['green' if c else 'red' for c in hard_consistencies]
    ax2.bar(weeks, [1]*len(weeks), color=colors, alpha=0.7)
    ax2.set_xlabel('Week')
    ax2.set_ylabel('Correct Prediction')
    ax2.set_title(f'Season {season_result["season"]} - hard consistency (accuracy: {np.mean(hard_consistencies)*100:.1f}%)')
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(['Incorrect', 'Correct'])
    
    plt.tight_layout()
    return fig


class VotingMethodComparator:
    def __init__(self):
        pass
    
    def compare_methods(self, judge_scores, vote_proportions):
        n = len(judge_scores)
        
        # 排名制
        judge_ranks = n - np.argsort(np.argsort(judge_scores))
        vote_ranks = n - np.argsort(np.argsort(vote_proportions))
        rank_combined = judge_ranks + vote_ranks
        rank_final = np.argsort(rank_combined) + 1  # 最终名次
        
        # 百分比制
        judge_pct = judge_scores / np.sum(judge_scores)
        pct_combined = judge_pct + vote_proportions
        pct_final = n - np.argsort(np.argsort(pct_combined))  # 最终名次
        
        # 计算差异
        rank_diff = np.abs(rank_final - pct_final)
        
        return {
            'rank_method': {
                'judge_ranks': judge_ranks.tolist(),
                'vote_ranks': vote_ranks.tolist(),
                'combined': rank_combined.tolist(),
                'final_ranking': rank_final.tolist()
            },
            'percentage_method': {
                'judge_pct': judge_pct.tolist(),
                'vote_pct': vote_proportions.tolist(),
                'combined': pct_combined.tolist(),
                'final_ranking': pct_final.tolist()
            },
            'difference': rank_diff.tolist(),
            'any_difference': np.any(rank_diff > 0)
        }
    
    def analyze_method_bias(self, judge_scores, vote_proportions):
        n = len(judge_scores)
        
        # 计算评委排名和投票排名的相关性
        judge_ranking = np.argsort(np.argsort(-judge_scores))  # 降序排名
        vote_ranking = np.argsort(np.argsort(-vote_proportions))
        
        # 排名制的最终排名
        rank_combined = (n - np.argsort(np.argsort(judge_scores))) + \
                       (n - np.argsort(np.argsort(vote_proportions)))
        rank_final = np.argsort(rank_combined)
        
        # 百分比制的最终排名
        pct_combined = judge_scores/np.sum(judge_scores) + vote_proportions
        pct_final = np.argsort(-pct_combined)
        
        # 计算与原始排名的相关性
        from scipy.stats import spearmanr
        
        rank_vs_judge = spearmanr(rank_final, judge_ranking)[0]
        rank_vs_vote = spearmanr(rank_final, vote_ranking)[0]
        pct_vs_judge = spearmanr(pct_final, judge_ranking)[0]
        pct_vs_vote = spearmanr(pct_final, vote_ranking)[0]
        
        return {
            'rank_method_judge_correlation': rank_vs_judge,
            'rank_method_vote_correlation': rank_vs_vote,
            'percentage_method_judge_correlation': pct_vs_judge,
            'percentage_method_vote_correlation': pct_vs_vote,
            'rank_method_judge_bias': rank_vs_judge - rank_vs_vote,
            'percentage_method_judge_bias': pct_vs_judge - pct_vs_vote
        }


def plot_method_comparison(comparison, contestants, title=None, figsize=(14, 5)):
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    n = len(contestants)
    x = np.arange(n)
    width = 0.35
    
    ax1 = axes[0]
    ax1.bar(x - width/2, comparison['rank_method']['judge_ranks'], width, label='Judge Rank', color='steelblue')
    ax1.bar(x + width/2, comparison['rank_method']['vote_ranks'], width, label='Vote Rank', color='coral')
    ax1.set_xticks(x)
    ax1.set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    ax1.set_ylabel('Rank')
    ax1.set_title('Rank-based method')
    ax1.legend()
    
    ax2 = axes[1]
    ax2.bar(x - width/2, comparison['percentage_method']['judge_pct'], width, label='Judge %', color='steelblue')
    ax2.bar(x + width/2, comparison['percentage_method']['vote_pct'], width, label='Vote %', color='coral')
    ax2.set_xticks(x)
    ax2.set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    ax2.set_ylabel('Percentage')
    ax2.set_title('Percentage method')
    ax2.legend()
    
    ax3 = axes[2]
    ax3.bar(x - width/2, comparison['rank_method']['final_ranking'], width, label='Rank Method', color='steelblue')
    ax3.bar(x + width/2, comparison['percentage_method']['final_ranking'], width, label='Percentage Method', color='coral')
    ax3.set_xticks(x)
    ax3.set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    ax3.set_ylabel('Final Ranking')
    ax3.set_title('Final ranking comparison')
    ax3.legend()
    
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    return fig


# =============================================================================
# 3. 争议案例分析
# =============================================================================

class ControversyAnalyzer:
    def __init__(self, df):
        self.df = df
        self.comparator = VotingMethodComparator()
    
    def find_celebrity(self, name_pattern, season=None):
        mask = self.df['celebrity_name'].str.lower().str.contains(name_pattern.lower())
        if season:
            mask = mask & (self.df['season'] == season)
        return self.df[mask]
    
    def analyze_controversy_case(self, celebrity_name, season, vote_estimates):
        celeb_data = self.find_celebrity(celebrity_name, season)
        if len(celeb_data) == 0:
            return {'error': f'Contestant not found: {celebrity_name} in Season {season}'}
        
        celeb = celeb_data.iloc[0]
        final_placement = celeb['placement']
        
        # 分析每周的表现
        weeks_analysis = []
        season_result = vote_estimates.get(season, {})
        
        for week, week_result in season_result.get('weeks', {}).items():
            if celebrity_name not in week_result.get('contestants', []):
                continue
            
            idx = week_result['contestants'].index(celebrity_name)
            
            judge_scores = np.array(week_result['judge_scores'])
            votes = np.array(week_result['votes_map'])
            
            # 计算该周该选手的排名
            judge_rank = len(judge_scores) - np.argsort(np.argsort(judge_scores))[idx]
            vote_rank = len(votes) - np.argsort(np.argsort(votes))[idx]
            
            # 用两种方法计算
            comparison = self.comparator.compare_methods(judge_scores, votes)
            
            weeks_analysis.append({
                'week': week,
                'judge_score': judge_scores[idx],
                'judge_rank': judge_rank,
                'estimated_vote_proportion': votes[idx],
                'vote_rank': vote_rank,
                'rank_method_final': comparison['rank_method']['final_ranking'][idx],
                'pct_method_final': comparison['percentage_method']['final_ranking'][idx],
                'n_contestants': len(judge_scores)
            })
        
        if weeks_analysis:
            judge_ranks = [w['judge_rank'] for w in weeks_analysis]
            vote_ranks = [w['vote_rank'] for w in weeks_analysis]
            
            analysis = {
                'celebrity': celebrity_name,
                'season': season,
                'final_placement': final_placement,
                'weeks_competed': len(weeks_analysis),
                'avg_judge_rank': np.mean(judge_ranks),
                'avg_vote_rank': np.mean(vote_ranks),
                'times_lowest_judge_score': sum(1 for w in weeks_analysis if w['judge_rank'] == w['n_contestants']),
                'weeks_analysis': weeks_analysis,
                'judge_vote_gap': np.mean(vote_ranks) - np.mean(judge_ranks),  # 正值表示粉丝票弥补了评委分
            }
        else:
            analysis = {
                'celebrity': celebrity_name,
                'season': season,
                'error': 'No weekly data found for this contestant'
            }
        
        return analysis
    
    def simulate_alternative_outcomes(self, celebrity_name, season, vote_estimates):
        analysis = self.analyze_controversy_case(celebrity_name, season, vote_estimates)
        
        if 'error' in analysis:
            return analysis
        
        # 统计在每种方法下可能被淘汰的次数
        rank_method_eliminations = 0
        pct_method_eliminations = 0
        
        for week_data in analysis['weeks_analysis']:
            n = week_data['n_contestants']
            # 在排名制下，排名最后（数值最大）的被淘汰
            if week_data['rank_method_final'] == n:
                rank_method_eliminations += 1
            # 在百分比制下，排名最后的被淘汰
            if week_data['pct_method_final'] == n:
                pct_method_eliminations += 1
        
        simulation = {
            'celebrity': celebrity_name,
            'season': season,
            'actual_placement': analysis['final_placement'],
            'weeks_competed': analysis['weeks_competed'],
            'rank_method_potential_eliminations': rank_method_eliminations,
            'pct_method_potential_eliminations': pct_method_eliminations,
            'method_makes_difference': rank_method_eliminations != pct_method_eliminations,
            'recommendation': self._get_recommendation(rank_method_eliminations, pct_method_eliminations)
        }
        
        return simulation
    
    def _get_recommendation(self, rank_elims, pct_elims):
        if rank_elims < pct_elims:
            return "Rank-based method is more favorable to this contestant (fan influence stronger)."
        elif pct_elims < rank_elims:
            return "Percentage method is more favorable to this contestant."
        else:
            return "Both methods produce similar outcomes."


def plot_controversy_analysis(analysis, figsize=(14, 6)):
    if 'error' in analysis:
        print(analysis['error'])
        return None
    
    weeks_data = analysis['weeks_analysis']
    weeks = [w['week'] for w in weeks_data]
    judge_ranks = [w['judge_rank'] for w in weeks_data]
    vote_ranks = [w['vote_rank'] for w in weeks_data]
    n_contestants = [w['n_contestants'] for w in weeks_data]
    
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    ax1 = axes[0]
    ax1.plot(weeks, judge_ranks, 'o-', label='Judge Rank', color='steelblue', linewidth=2, markersize=8)
    ax1.plot(weeks, vote_ranks, 's-', label='Vote Rank (estimated)', color='coral', linewidth=2, markersize=8)
    ax1.plot(weeks, n_contestants, 'x--', label='Total Contestants', color='gray', alpha=0.5)
    ax1.set_xlabel('Week')
    ax1.set_ylabel('Rank')
    ax1.set_title(f'{analysis["celebrity"]} (Season {analysis["season"]}) - ranking trends')
    ax1.legend()
    ax1.invert_yaxis()  # 排名越小越好，所以反转Y轴
    
    ax2 = axes[1]
    gaps = [v - j for j, v in zip(judge_ranks, vote_ranks)]
    colors = ['green' if g > 0 else 'red' for g in gaps]
    ax2.bar(weeks, gaps, color=colors, alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_xlabel('Week')
    ax2.set_ylabel('Vote Rank - Judge Rank')
    ax2.set_title('Vote vs judge rank difference\n(positive = fans more supportive)')
    
    fig.suptitle(f'Controversy analysis: {analysis["celebrity"]} - final placement: {analysis["final_placement"]}', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    return fig


# =============================================================================
# 3.5 论文用汇总图（适合直接放入论文，英文标注）
# =============================================================================

def plot_paper_consistency_summary(results, figsize=(10, 5)):
    """
    全赛季一致性汇总：一张图展示所有赛季的软一致性均值与硬一致性准确率。
    适合论文 Figure：左图各赛季平均一致性，右图各赛季硬准确率。
    """
    seasons = sorted(results.keys())
    mean_consistencies = []
    hard_accuracies = []
    for s in seasons:
        weeks_data = results[s].get('weeks', {})
        if not weeks_data:
            mean_consistencies.append(np.nan)
            hard_accuracies.append(np.nan)
            continue
        cons = [weeks_data[w]['consistency'] for w in sorted(weeks_data.keys())]
        hard = [weeks_data[w]['is_consistent'] for w in sorted(weeks_data.keys())]
        mean_consistencies.append(np.mean(cons))
        hard_accuracies.append(np.mean(hard) * 100)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    x = np.arange(len(seasons))
    ax1.bar(x, mean_consistencies, color='steelblue', alpha=0.8, edgecolor='navy', linewidth=0.5)
    ax1.axhline(y=np.nanmean(mean_consistencies), color='red', linestyle='--', linewidth=1.5, 
                label=f'Overall mean: {np.nanmean(mean_consistencies):.3f}')
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Mean soft consistency')
    ax1.set_title('(a) Soft consistency by season')
    ax1.set_xticks(x[::2])
    ax1.set_xticklabels([seasons[i] for i in range(0, len(seasons), 2)])
    ax1.legend()
    ax1.set_ylim(0, 1)
    
    ax2.bar(x, hard_accuracies, color='forestgreen', alpha=0.7, edgecolor='darkgreen', linewidth=0.5)
    ax2.axhline(y=np.nanmean(hard_accuracies), color='red', linestyle='--', linewidth=1.5,
                label=f'Overall: {np.nanmean(hard_accuracies):.1f}%')
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Hard consistency accuracy (%)')
    ax2.set_title('(b) Hard consistency accuracy by season')
    ax2.set_xticks(x[::2])
    ax2.set_xticklabels([seasons[i] for i in range(0, len(seasons), 2)])
    ax2.legend()
    ax2.set_ylim(0, 105)
    
    plt.tight_layout()
    return fig


def plot_paper_controversy_summary(controversy_results, figsize=(10, 8)):
    """
    四例争议案例汇总：2x2 子图，每子图展示一名选手的评委排名 vs 估计投票排名随周次变化。
    适合论文 Figure：评委-粉丝分歧典型案例。
    """
    cases = [c for c in controversy_results if 'error' not in c.get('analysis', {})]
    if len(cases) == 0:
        return None
    cases = cases[:4]
    n = len(cases)
    
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = np.atleast_2d(axes).flatten()
    
    for idx, case in enumerate(cases):
        ax = axes[idx]
        analysis = case['analysis']
        weeks_data = analysis.get('weeks_analysis', [])
        if not weeks_data:
            continue
        weeks = [w['week'] for w in weeks_data]
        judge_ranks = [w['judge_rank'] for w in weeks_data]
        vote_ranks = [w['vote_rank'] for w in weeks_data]
        max_rank = max(max(judge_ranks), max(vote_ranks))
        
        ax.plot(weeks, judge_ranks, 'o-', label='Judge rank', color='steelblue', linewidth=1.5, markersize=5)
        ax.plot(weeks, vote_ranks, 's-', label='Est. vote rank', color='coral', linewidth=1.5, markersize=5)
        ax.set_xlabel('Week')
        ax.set_ylabel('Rank')
        ax.set_title(f"{analysis['celebrity']} (S{analysis['season']}), placement: {analysis['final_placement']}")
        ax.legend(fontsize=8)
        ax.invert_yaxis()
        # 显式设置 y 范围：排名 1 在上方，避免曲线跑出可视区
        ax.set_ylim(max_rank + 0.5, 0.5)
    
    for idx in range(n, 4):
        axes[idx].set_visible(False)
    
    fig.suptitle('Controversy cases: judge rank vs estimated fan vote rank over weeks', fontsize=12, fontweight='bold')
    plt.tight_layout()
    return fig


def plot_paper_voting_method_difference(comparison_results, figsize=(10, 4)):
    """
    投票方法差异汇总：各赛季「排名制 vs 百分比制」产生不同淘汰结果的周次占比。
    适合论文 Figure：说明赛制选择对结果影响大。
    """
    seasons = sorted(comparison_results.keys())
    rates = [comparison_results[s]['difference_rate'] * 100 for s in seasons]
    
    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(seasons))
    colors = ['coral' if r == 100 else 'steelblue' for r in rates]
    ax.bar(x, rates, color=colors, alpha=0.8, edgecolor='gray', linewidth=0.3)
    ax.axhline(y=np.mean(rates), color='red', linestyle='--', linewidth=1.5, 
               label=f'Mean: {np.mean(rates):.1f}%')
    ax.set_xlabel('Season')
    ax.set_ylabel('% of weeks with different outcome')
    ax.set_title('Voting method comparison: rank-based vs percentage-based (difference rate by season)')
    ax.set_xticks(x[::2])
    ax.set_xticklabels([seasons[i] for i in range(0, len(seasons), 2)])
    ax.legend()
    ax.set_ylim(0, 105)
    plt.tight_layout()
    return fig


def plot_paper_certainty_summary(results, figsize=(10, 5)):
    """
    确定性 Φ = 1/std(p^MCMC) 汇总：各赛季平均 Φ、全样本 Φ 分布。
    仅当结果中包含 MCMC 的 certainty_phi 时有效。
    """
    seasons = sorted(results.keys())
    mean_phi_by_season = []
    all_phi = []
    has_certainty = False
    for s in seasons:
        weeks_data = results[s].get('weeks', {})
        if not weeks_data:
            mean_phi_by_season.append(np.nan)
            continue
        phi_list = []
        for w in weeks_data.values():
            phi = w.get('certainty_phi') or w.get('certainty')
            if phi is not None:
                has_certainty = True
                phi_arr = np.asarray(phi)
                phi_list.extend(phi_arr.tolist())
                all_phi.extend(phi_arr.tolist())
        mean_phi_by_season.append(np.mean(phi_list) if phi_list else np.nan)
    if not has_certainty or not all_phi:
        return None
    all_phi = np.array(all_phi)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    x = np.arange(len(seasons))
    ax1.bar(x, mean_phi_by_season, color='darkviolet', alpha=0.8, edgecolor='indigo', linewidth=0.5)
    ax1.axhline(y=np.nanmean(mean_phi_by_season), color='red', linestyle='--', linewidth=1.5,
                label=f'Overall mean: {np.nanmean(mean_phi_by_season):.2f}')
    ax1.set_xlabel('Season')
    ax1.set_ylabel(r'Mean certainty $\Phi$')
    ax1.set_title(r'(a) Mean certainty $\Phi = 1/\mathrm{std}(p^{\mathrm{MCMC}})$ by season')
    ax1.set_xticks(x[::2])
    ax1.set_xticklabels([seasons[i] for i in range(0, len(seasons), 2)])
    ax1.legend()
    ax1.set_ylim(0, None)
    ax2.hist(all_phi, bins=min(50, max(20, len(all_phi)//20)), color='darkviolet', alpha=0.7, edgecolor='white')
    ax2.axvline(x=np.mean(all_phi), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(all_phi):.2f}')
    ax2.set_xlabel(r'Certainty $\Phi$')
    ax2.set_ylabel('Count')
    ax2.set_title(r'(b) Distribution of $\Phi$ (all contestant-weeks)')
    ax2.legend()
    fig.suptitle(r'Certainty metric $\Phi_{i,t} = 1/\mathrm{std}(p_{i,t}^{\mathrm{MCMC}})$', fontsize=12, fontweight='bold')
    plt.tight_layout()
    return fig


def plot_paper_vote_example(week_result, season, week, figsize=(10, 4)):
    """
    单周投票估计示例：评委分、估计粉丝票比例、淘汰概率；若有 MCMC 则增加确定性 Φ。
    """
    contestants = week_result['contestants']
    judge_scores = np.array(week_result['judge_scores'])
    votes_map = np.array(week_result['votes_map'])
    elim_probs = np.array(week_result['elim_probs'])
    eliminated_idx = week_result['eliminated_idx']
    certainty_phi = week_result.get('certainty_phi') or week_result.get('certainty')
    n_panels = 4 if (certainty_phi is not None and len(certainty_phi) == len(contestants)) else 3
    fig, axes = plt.subplots(1, n_panels, figsize=(figsize[0] * n_panels / 3, figsize[1]))
    if n_panels == 3:
        axes = list(axes)
    colors = ['red' if i == eliminated_idx else 'steelblue' for i in range(len(contestants))]
    
    axes[0].bar(range(len(contestants)), judge_scores, color=colors)
    axes[0].set_xticks(range(len(contestants)))
    axes[0].set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    axes[0].set_ylabel('Judge score')
    axes[0].set_title('(a) Judge scores')
    
    axes[1].bar(range(len(contestants)), votes_map, color=colors)
    axes[1].set_xticks(range(len(contestants)))
    axes[1].set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    axes[1].set_ylabel('Vote proportion')
    axes[1].set_title('(b) Estimated fan vote proportion')
    
    axes[2].bar(range(len(contestants)), elim_probs, color=colors)
    axes[2].set_xticks(range(len(contestants)))
    axes[2].set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
    axes[2].set_ylabel('Elimination probability')
    axes[2].set_title('(c) Predicted elimination probability')
    
    if n_panels == 4:
        phi_arr = np.array(certainty_phi, dtype=float)
        axes[3].bar(range(len(contestants)), phi_arr, color=colors)
        axes[3].set_xticks(range(len(contestants)))
        axes[3].set_xticklabels(contestants, rotation=45, ha='right', fontsize=8)
        axes[3].set_ylabel(r'Certainty $\Phi$')
        axes[3].set_title(r'(d) Certainty $\Phi = 1/\mathrm{std}(p^{\mathrm{MCMC}})$')
        axes[3].set_ylim(0, None)
    
    fig.suptitle(f'Example: Season {season}, Week {week}', fontsize=12, fontweight='bold')
    plt.tight_layout()
    return fig


# =============================================================================
# 4. 综合报告生成
# =============================================================================

def generate_summary_report(all_results, metrics, controversy_analyses=None):
    report = []
    report.append("="*70)
    report.append("DWTS fan vote estimation report")
    report.append("Based on the inverse decision-making (IDM) model")
    report.append("="*70)
    
    report.append("\n[1] Model performance")
    report.append(f"  Total weeks analyzed: {metrics['n_weeks_analyzed']}")
    report.append(f"  Mean soft consistency: {metrics['mean_consistency']:.4f} (±{metrics['std_consistency']:.4f})")
    report.append(f"  Hard consistency accuracy: {metrics['hard_accuracy']*100:.2f}%")
    
    report.append("\n[2] Season overview")
    for season, result in all_results.items():
        method = result['method']
        n_weeks = len(result['weeks'])
        consistencies = [w['consistency'] for w in result['weeks'].values()]
        avg_consistency = np.mean(consistencies) if consistencies else 0
        report.append(f"  Season {season}: method={method}, weeks={n_weeks}, mean consistency={avg_consistency:.3f}")
    
    if controversy_analyses:
        report.append("\n[3] Controversy cases")
        for analysis in controversy_analyses:
            if 'error' not in analysis:
                report.append(f"\n  {analysis['celebrity']} (Season {analysis['season']})")
                report.append(f"    Final placement: {analysis['final_placement']}")
                report.append(f"    Weeks competed: {analysis['weeks_competed']}")
                report.append(f"    Avg judge rank: {analysis['avg_judge_rank']:.1f}")
                report.append(f"    Avg vote rank: {analysis['avg_vote_rank']:.1f}")
                report.append(f"    Times lowest judge score: {analysis['times_lowest_judge_score']}")
                report.append(f"    Fan vote - judge gap: {analysis['judge_vote_gap']:+.1f}")
    
    return "\n".join(report)


# =============================================================================
# 5. 使用示例
# =============================================================================

if __name__ == "__main__":
    print("Visualization and analysis module.")
    print("Import this module together with idm_fan_vote_model.py for interactive use.")
