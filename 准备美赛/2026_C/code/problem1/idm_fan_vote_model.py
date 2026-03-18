"""
逆向决策模型（Inverse Decision-Making）用于推断《与星共舞》粉丝投票
基于 Jern, Lucas, & Kemp (2017) 的理论框架

模型核心思想：
- 观察者（我们）通过观察决策结果（淘汰）来反推决策者（粉丝）的潜在偏好（投票分布）
- 使用贝叶斯推断：P(θ|E,S) ∝ P(E|θ,S) × P(θ)
"""

import numpy as np
import pandas as pd
from scipy.special import softmax
from scipy.optimize import minimize
from scipy.stats import entropy, norm
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. 数据加载与预处理
# =============================================================================

def load_processed_data(excel_path):
    """
    从预处理后的 Excel 文件加载数据（后续分析请使用此函数）。
    
    Parameters:
    -----------
    excel_path : str
        预处理输出的 Excel 文件路径（.xlsx）
        
    Returns:
    --------
    df : pd.DataFrame
        预处理后的数据框
    """
    try:
        from data_preprocessing import load_processed_excel
        return load_processed_excel(excel_path)
    except ImportError:
        return pd.read_excel(excel_path, sheet_name='数据', engine='openpyxl')


def load_and_preprocess_data(filepath, use_advanced_preprocessing=True):
    """
    加载DWTS数据：
    - 若 filepath 为 .xlsx，则直接读取预处理后的 Excel（推荐，后续分析使用此方式）
    - 若 filepath 为 .csv，则运行完整预处理并输出 Excel，返回预处理后的数据
    
    Parameters:
    -----------
    filepath : str
        数据文件路径：预处理后的 Excel（.xlsx）或原始 CSV
    use_advanced_preprocessing : bool
        当输入为 CSV 时，是否使用高级预处理器（推荐）
        
    Returns:
    --------
    df : pd.DataFrame
        预处理后的数据框
    """
    filepath_lower = filepath.lower()
    
    # 若为 Excel，直接读取（处理后的数据）
    if filepath_lower.endswith('.xlsx') or filepath_lower.endswith('.xls'):
        return load_processed_data(filepath)
    
    # 若为 CSV，运行预处理并输出 Excel
    if use_advanced_preprocessing:
        try:
            from data_preprocessing import DWTSDataPreprocessor
            preprocessor = DWTSDataPreprocessor(filepath)
            df, _, _ = preprocessor.run_full_preprocessing()
            # run_full_preprocessing 内部已调用 save_processed_data() 输出 Excel
            return df
        except ImportError:
            print("警告: 无法导入高级预处理器，使用简化版本")
    
    # 简化版预处理（向后兼容）
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    
    # 解析结果字段，提取淘汰周次
    def parse_elimination_week(result):
        """从results字段解析淘汰周次"""
        if pd.isna(result):
            return None
        result = str(result).lower()
        if 'place' in result:
            # 进入决赛的选手
            return None  # 表示未被周赛淘汰
        elif 'eliminated week' in result:
            try:
                import re
                match = re.search(r'week\s*(\d+)', result)
                if match:
                    return int(match.group(1))
            except:
                return None
        return None
    
    df['elimination_week'] = df['results'].apply(parse_elimination_week)
    
    # 提取所有评委分数列
    judge_cols = [col for col in df.columns if 'judge' in col.lower() and 'score' in col.lower()]
    
    # 计算每周的总评委分数
    weeks = set()
    for col in judge_cols:
        parts = col.split('_')
        for part in parts:
            if part.startswith('week'):
                try:
                    week_num = int(part.replace('week', ''))
                    weeks.add(week_num)
                except:
                    pass
    
    max_week = max(weeks) if weeks else 11
    
    for week in range(1, max_week + 1):
        week_judge_cols = [col for col in judge_cols if f'week{week}_' in col]
        if week_judge_cols:
            # 计算该周所有评委的总分（处理N/A和字符串）
            def compute_total(row):
                total = 0
                for col in week_judge_cols:
                    val = row[col]
                    if pd.isna(val) or val == 'N/A' or val == '':
                        continue
                    try:
                        total += float(val)
                    except:
                        continue
                return total if total > 0 else np.nan
            
            df[f'week{week}_total_score'] = df.apply(compute_total, axis=1)
            
            # 计算该周评委人数
            def count_judges(row):
                count = 0
                for col in week_judge_cols:
                    val = row[col]
                    if pd.notna(val) and val != 'N/A' and val != '':
                        try:
                            float(val)
                            count += 1
                        except:
                            pass
                return count if count > 0 else np.nan
            
            df[f'week{week}_judge_count'] = df.apply(count_judges, axis=1)
    
    return df


def get_season_data(df, season):
    """
    获取指定赛季的数据
    
    Parameters:
    -----------
    df : pd.DataFrame
        完整数据框
    season : int
        赛季编号
        
    Returns:
    --------
    season_df : pd.DataFrame
        该赛季的数据
    """
    return df[df['season'] == season].copy()


def get_week_contestants(season_df, week):
    """
    获取指定周仍在比赛的选手
    
    Parameters:
    -----------
    season_df : pd.DataFrame
        赛季数据
    week : int
        周次
        
    Returns:
    --------
    contestants : pd.DataFrame
        该周参赛选手数据
    """
    score_col = f'week{week}_total_score'
    if score_col not in season_df.columns:
        return pd.DataFrame()
    
    # 选手该周有分数（非0且非NaN）表示仍在比赛
    mask = (season_df[score_col].notna()) & (season_df[score_col] > 0)
    return season_df[mask].copy()


# =============================================================================
# 2. 正向决策模型（Forward Model）
# =============================================================================

class ForwardModel:
    """
    正向决策模型：给定效用值，计算投票概率分布
    基于Luce选择公理（Softmax模型）
    """
    
    def __init__(self, temperature=1.0):
        """
        Parameters:
        -----------
        temperature : float
            Softmax温度参数，控制选择的随机性
            τ → 0: 确定性选择（选效用最高的）
            τ → ∞: 均匀随机选择
        """
        self.temperature = temperature
    
    def compute_vote_probability(self, utilities):
        """
        计算投票概率分布（Softmax）
        
        Parameters:
        -----------
        utilities : np.ndarray
            各选手的效用值 (n_contestants,)
            
        Returns:
        --------
        probabilities : np.ndarray
            投票概率分布 (n_contestants,)
        """
        scaled_utilities = utilities / self.temperature
        return softmax(scaled_utilities)
    
    def compute_vote_counts(self, utilities, total_votes):
        """
        计算预期投票数
        
        Parameters:
        -----------
        utilities : np.ndarray
            各选手的效用值
        total_votes : float
            总投票数
            
        Returns:
        --------
        vote_counts : np.ndarray
            各选手的投票数
        """
        probs = self.compute_vote_probability(utilities)
        return probs * total_votes


# =============================================================================
# 3. 投票组合规则（Voting Combination Rules）
# =============================================================================

class VotingCombiner:
    """
    投票组合规则：组合评委分数和粉丝投票
    """
    
    @staticmethod
    def combine_by_rank(judge_scores, vote_proportions):
        """
        排名制组合（Seasons 1-2, 28-34）
        
        Parameters:
        -----------
        judge_scores : np.ndarray
            评委总分 (n_contestants,)
        vote_proportions : np.ndarray
            投票比例 (n_contestants,)
            
        Returns:
        --------
        combined_scores : np.ndarray
            组合后的排名和（越小越好）
        """
        n = len(judge_scores)
        
        # 评委分排名（分数越高排名越小）
        judge_ranks = n - np.argsort(np.argsort(judge_scores))
        
        # 投票排名（比例越高排名越小）
        vote_ranks = n - np.argsort(np.argsort(vote_proportions))
        
        # 排名之和（越小越好，即不容易被淘汰）
        combined_ranks = judge_ranks + vote_ranks
        
        return combined_ranks
    
    @staticmethod
    def combine_by_percentage(judge_scores, vote_proportions):
        """
        百分比制组合（Seasons 3-27）
        
        Parameters:
        -----------
        judge_scores : np.ndarray
            评委总分 (n_contestants,)
        vote_proportions : np.ndarray
            投票比例 (n_contestants,)
            
        Returns:
        --------
        combined_scores : np.ndarray
            组合后的百分比和（越大越好）
        """
        # 评委分百分比
        judge_total = np.sum(judge_scores)
        if judge_total > 0:
            judge_pct = judge_scores / judge_total
        else:
            judge_pct = np.ones(len(judge_scores)) / len(judge_scores)
        
        # 组合百分比（越大越好，即不容易被淘汰）
        combined_pct = judge_pct + vote_proportions
        
        return combined_pct
    
    @staticmethod
    def get_elimination_probability(combined_scores, method='rank', tau=0.1):
        """
        计算被淘汰的概率（使用Softmax平滑）
        
        Parameters:
        -----------
        combined_scores : np.ndarray
            组合分数
        method : str
            'rank' 或 'percentage'
        tau : float
            温度参数
            
        Returns:
        --------
        elim_probs : np.ndarray
            各选手被淘汰的概率
        """
        if method == 'rank':
            # 排名制：排名和越大越可能被淘汰
            return softmax(combined_scores / tau)
        else:
            # 百分比制：百分比和越小越可能被淘汰
            return softmax(-combined_scores / tau)


# =============================================================================
# 4. 逆向决策模型（Inverse Decision-Making Model）
# =============================================================================

class InverseDecisionModel:
    """
    逆向决策模型：从淘汰结果反推粉丝投票分布
    
    核心公式：P(θ|E,S) ∝ P(E|θ,S) × P(θ)
    - θ: 粉丝效用/投票分布
    - E: 被淘汰的选手
    - S: 评委分数
    """
    
    def __init__(self, method='percentage', softmax_temp=1.0, likelihood_temp=0.1):
        """
        Parameters:
        -----------
        method : str
            投票组合方式: 'rank' 或 'percentage'
        softmax_temp : float
            效用到投票概率的Softmax温度
        likelihood_temp : float
            淘汰概率的Softmax温度
        """
        self.method = method
        self.forward_model = ForwardModel(temperature=softmax_temp)
        self.combiner = VotingCombiner()
        self.likelihood_temp = likelihood_temp
    
    def compute_likelihood(self, utilities, judge_scores, eliminated_idx):
        """
        计算似然函数 P(E|θ,S)
        给定效用和评委分，计算观察到特定选手被淘汰的概率
        
        Parameters:
        -----------
        utilities : np.ndarray
            效用值 (n_contestants,)
        judge_scores : np.ndarray
            评委分数 (n_contestants,)
        eliminated_idx : int
            被淘汰选手的索引
            
        Returns:
        --------
        likelihood : float
            似然概率
        """
        # 效用 → 投票比例
        vote_probs = self.forward_model.compute_vote_probability(utilities)
        
        # 组合评委分和投票
        if self.method == 'rank':
            combined = self.combiner.combine_by_rank(judge_scores, vote_probs)
        else:
            combined = self.combiner.combine_by_percentage(judge_scores, vote_probs)
        
        # 计算淘汰概率
        elim_probs = self.combiner.get_elimination_probability(
            combined, method=self.method, tau=self.likelihood_temp
        )
        
        return elim_probs[eliminated_idx]
    
    def compute_prior(self, utilities, prior_mean=None, prior_std=1.0):
        """
        计算先验概率 P(θ)
        假设效用服从正态分布
        
        Parameters:
        -----------
        utilities : np.ndarray
            效用值 (n_contestants,)
        prior_mean : np.ndarray or None
            先验均值（如基于历史表现）
        prior_std : float
            先验标准差
            
        Returns:
        --------
        prior : float
            先验概率（对数）
        """
        if prior_mean is None:
            prior_mean = np.zeros(len(utilities))
        
        log_prior = np.sum(norm.logpdf(utilities, loc=prior_mean, scale=prior_std))
        return log_prior
    
    def compute_log_posterior(self, utilities, judge_scores, eliminated_idx, 
                               prior_mean=None, prior_std=1.0):
        """
        计算对数后验概率（未归一化）
        log P(θ|E,S) ∝ log P(E|θ,S) + log P(θ)
        
        Parameters:
        -----------
        utilities : np.ndarray
            效用值
        judge_scores : np.ndarray
            评委分数
        eliminated_idx : int
            被淘汰选手索引
        prior_mean : np.ndarray
            先验均值
        prior_std : float
            先验标准差
            
        Returns:
        --------
        log_posterior : float
            对数后验概率
        """
        likelihood = self.compute_likelihood(utilities, judge_scores, eliminated_idx)
        log_likelihood = np.log(likelihood + 1e-10)  # 防止log(0)
        log_prior = self.compute_prior(utilities, prior_mean, prior_std)
        
        return log_likelihood + log_prior
    
    def estimate_utilities_map(self, judge_scores, eliminated_idx, 
                                prior_mean=None, prior_std=1.0):
        """
        使用MAP（最大后验估计）推断效用值
        
        Parameters:
        -----------
        judge_scores : np.ndarray
            评委分数
        eliminated_idx : int
            被淘汰选手索引
        prior_mean : np.ndarray
            先验均值
        prior_std : float
            先验标准差
            
        Returns:
        --------
        optimal_utilities : np.ndarray
            MAP估计的效用值
        vote_proportions : np.ndarray
            对应的投票比例
        """
        n = len(judge_scores)
        
        if prior_mean is None:
            prior_mean = np.zeros(n)
        
        def neg_log_posterior(u):
            return -self.compute_log_posterior(
                u, judge_scores, eliminated_idx, prior_mean, prior_std
            )
        
        # 多次随机初始化，取最优解
        best_result = None
        best_value = np.inf
        
        for _ in range(10):
            u0 = np.random.randn(n) * 0.5 + prior_mean
            result = minimize(neg_log_posterior, u0, method='L-BFGS-B')
            
            if result.fun < best_value:
                best_value = result.fun
                best_result = result
        
        optimal_utilities = best_result.x
        vote_proportions = self.forward_model.compute_vote_probability(optimal_utilities)
        
        return optimal_utilities, vote_proportions


# =============================================================================
# 5. MCMC采样器（用于不确定性量化）
# =============================================================================

class MCMCSampler:
    """
    Metropolis-Hastings MCMC采样器
    用于从后验分布采样，量化不确定性
    """
    
    def __init__(self, idm_model, proposal_std=0.3):
        """
        Parameters:
        -----------
        idm_model : InverseDecisionModel
            逆向决策模型
        proposal_std : float
            提议分布的标准差
        """
        self.idm_model = idm_model
        self.proposal_std = proposal_std
    
    def sample(self, judge_scores, eliminated_idx, n_samples=5000, 
               burn_in=1000, prior_mean=None, prior_std=1.0):
        """
        MCMC采样
        
        Parameters:
        -----------
        judge_scores : np.ndarray
            评委分数
        eliminated_idx : int
            被淘汰选手索引
        n_samples : int
            采样数量
        burn_in : int
            预烧期
        prior_mean : np.ndarray
            先验均值
        prior_std : float
            先验标准差
            
        Returns:
        --------
        samples : np.ndarray
            效用值样本 (n_samples, n_contestants)
        acceptance_rate : float
            接受率
        """
        n = len(judge_scores)
        
        if prior_mean is None:
            prior_mean = np.zeros(n)
        
        # 初始化
        current_u = prior_mean.copy()
        current_log_post = self.idm_model.compute_log_posterior(
            current_u, judge_scores, eliminated_idx, prior_mean, prior_std
        )
        
        samples = []
        n_accepted = 0
        
        total_iterations = n_samples + burn_in
        
        for i in range(total_iterations):
            # 提议新状态
            proposed_u = current_u + np.random.randn(n) * self.proposal_std
            proposed_log_post = self.idm_model.compute_log_posterior(
                proposed_u, judge_scores, eliminated_idx, prior_mean, prior_std
            )
            
            # Metropolis-Hastings接受准则
            log_alpha = proposed_log_post - current_log_post
            
            if np.log(np.random.rand()) < log_alpha:
                current_u = proposed_u
                current_log_post = proposed_log_post
                n_accepted += 1
            
            # 保存样本（跳过burn-in期）
            if i >= burn_in:
                samples.append(current_u.copy())
        
        samples = np.array(samples)
        acceptance_rate = n_accepted / total_iterations
        
        return samples, acceptance_rate
    
    def compute_posterior_statistics(self, samples):
        """
        计算后验统计量
        
        Parameters:
        -----------
        samples : np.ndarray
            效用值样本 (n_samples, n_contestants)
            
        Returns:
        --------
        stats : dict
            包含均值、标准差、方差、置信区间等
        """
        mean = np.mean(samples, axis=0)
        std = np.std(samples, axis=0)
        var = std ** 2
        ci_lower = np.percentile(samples, 2.5, axis=0)
        ci_upper = np.percentile(samples, 97.5, axis=0)
        
        # 转换为投票比例
        vote_samples = np.array([softmax(s) for s in samples])
        vote_mean = np.mean(vote_samples, axis=0)
        vote_std = np.std(vote_samples, axis=0)
        vote_var = vote_std ** 2
        vote_ci_lower = np.percentile(vote_samples, 2.5, axis=0)
        vote_ci_upper = np.percentile(vote_samples, 97.5, axis=0)
        
        return {
            'utility_mean': mean,
            'utility_std': std,
            'utility_var': var,
            'utility_ci_lower': ci_lower,
            'utility_ci_upper': ci_upper,
            'vote_mean': vote_mean,
            'vote_std': vote_std,
            'vote_var': vote_var,
            'vote_ci_lower': vote_ci_lower,
            'vote_ci_upper': vote_ci_upper
        }


# =============================================================================
# 6. 一致性与确定性度量
# =============================================================================

class ModelEvaluator:
    """
    模型评估器：计算一致性和确定性指标
    """
    
    @staticmethod
    def compute_consistency(predicted_elim_probs, actual_eliminated_idx):
        """
        计算一致性指标
        模型预测的淘汰者与实际淘汰者匹配的概率
        
        Parameters:
        -----------
        predicted_elim_probs : np.ndarray
            模型预测的各选手淘汰概率
        actual_eliminated_idx : int
            实际被淘汰选手的索引
            
        Returns:
        --------
        consistency : float
            一致性指标 [0, 1]
        """
        # 方法1：实际被淘汰选手的预测淘汰概率
        consistency = predicted_elim_probs[actual_eliminated_idx]
        return consistency
    
    @staticmethod
    def compute_consistency_hard(predicted_elim_probs, actual_eliminated_idx):
        """
        硬一致性：预测的最可能被淘汰者是否与实际一致
        
        Returns:
        --------
        is_consistent : bool
        """
        predicted_idx = np.argmax(predicted_elim_probs)
        return predicted_idx == actual_eliminated_idx
    
    @staticmethod
    def compute_certainty_variance(posterior_stats, epsilon=1e-6):
        """
        基于后验方差的确定性度量
        
        根据 Jern 等人的理论：Certainty = 1 / Var(θ|E,S)
        
        Parameters:
        -----------
        posterior_stats : dict
            后验统计量，包含 'vote_std' 或 'vote_var'
        epsilon : float
            正则化常数，防止除零
            
        Returns:
        --------
        certainty : np.ndarray
            各选手投票估计的确定性（基于方差）
        """
        if 'vote_var' in posterior_stats:
            vote_var = posterior_stats['vote_var']
        elif 'vote_std' in posterior_stats:
            vote_var = posterior_stats['vote_std'] ** 2
        else:
            raise ValueError("posterior_stats must contain 'vote_std' or 'vote_var'")
        
        # Certainty = 1 / Var(θ|E,S)
        certainty = 1.0 / (vote_var + epsilon)
        return certainty
    
    @staticmethod
    def compute_certainty_entropy(vote_samples, epsilon=1e-6):
        """
        基于信息熵的确定性度量
        
        Entropy = -Σ p_i log(p_i)
        Certainty ∝ 1 / Entropy
        
        Parameters:
        -----------
        vote_samples : np.ndarray
            投票比例样本 (n_samples, n_contestants)
        epsilon : float
            正则化常数
            
        Returns:
        --------
        certainty : np.ndarray
            各选手的确定性指标（基于熵）
        avg_entropy : float
            平均熵
        individual_entropies : np.ndarray
            每个样本的熵
        """
        # 计算每个样本的熵
        individual_entropies = np.array([entropy(sample) for sample in vote_samples])
        avg_entropy = np.mean(individual_entropies)
        
        # 计算每个选手投票比例的熵（跨样本）
        # 对每个选手，计算其投票比例分布的熵
        n_contestants = vote_samples.shape[1]
        contestant_entropies = []
        
        for i in range(n_contestants):
            # 该选手在所有样本中的投票比例分布
            vote_dist = vote_samples[:, i]
            # 归一化（使其成为概率分布）
            vote_dist_norm = vote_dist / (vote_dist.sum() + epsilon)
            # 计算熵（避免log(0)）
            vote_dist_norm = vote_dist_norm[vote_dist_norm > epsilon]
            if len(vote_dist_norm) > 0:
                h = -np.sum(vote_dist_norm * np.log(vote_dist_norm + epsilon))
            else:
                h = 0
            contestant_entropies.append(h)
        
        contestant_entropies = np.array(contestant_entropies)
        
        # Certainty ∝ 1 / Entropy
        certainty = 1.0 / (contestant_entropies + epsilon)
        
        return certainty, avg_entropy, individual_entropies
    
    @staticmethod
    def compute_certainty_consistency(consistency_value, epsilon=1e-6):
        """
        基于一致性的确定性代理指标
        
        当无法进行MCMC采样时，使用一致性作为确定性的代理指标
        Certainty ∝ Consistency = P(E | θ_MAP, S)
        
        Parameters:
        -----------
        consistency_value : float
            软一致性值 [0, 1]
        epsilon : float
            正则化常数
            
        Returns:
        --------
        certainty : float
            基于一致性的确定性指标
        """
        # 一致性越高，确定性越高
        # 可以直接使用一致性值，或进行归一化
        certainty = consistency_value / (1.0 + epsilon)
        return certainty
    
    @staticmethod
    def compute_certainty_from_map(votes_map, judge_scores, eliminated_idx, 
                                    method='rank', epsilon=1e-6):
        """
        从MAP估计计算确定性（无需MCMC）
        
        使用投票分布的集中程度作为确定性的近似度量
        
        Parameters:
        -----------
        votes_map : np.ndarray
            MAP估计的投票比例
        judge_scores : np.ndarray
            评委分数
        eliminated_idx : int
            被淘汰选手索引
        method : str
            投票方法
        epsilon : float
            正则化常数
            
        Returns:
        --------
        certainty : np.ndarray
            各选手的确定性指标
        certainty_metrics : dict
            详细的确定性度量指标
        """
        votes = np.array(votes_map)
        n = len(votes)
        
        # 方法1：基于投票分布的熵（整体分布）
        vote_entropy = entropy(votes)
        certainty_entropy_scalar = 1.0 / (vote_entropy + epsilon)
        # 为每个选手分配相同的熵基确定性（整体分布特征）
        certainty_entropy = np.full(n, certainty_entropy_scalar)
        
        # 方法2：基于投票分布的方差（整体分布）
        vote_var = np.var(votes)
        certainty_var_scalar = 1.0 / (vote_var + epsilon)
        # 为每个选手分配相同的方差基确定性
        certainty_var = np.full(n, certainty_var_scalar)
        
        # 方法3：基于投票分布的集中度（Gini系数）
        sorted_votes = np.sort(votes)[::-1]
        n_vals = np.arange(1, n + 1)
        gini = (2 * np.sum(n_vals * sorted_votes)) / (n * np.sum(sorted_votes)) - (n + 1) / n
        gini = max(0, min(1, gini))  # 确保在[0,1]范围内
        certainty_gini = np.full(n, gini)  # Gini越高，分布越集中，确定性越高
        
        # 方法4：基于每个选手投票比例的确定性
        # 投票比例越接近0或1，确定性越高；越接近均匀分布，确定性越低
        certainty_individual = np.zeros(n)
        for i in range(n):
            vote_i = votes[i]
            # 使用投票比例的"确定性"：越极端（接近0或1），确定性越高
            certainty_individual[i] = 1.0 - 2 * abs(vote_i - 0.5)  # 归一化到[0,1]
        
        # 方法5：基于淘汰边缘的接近程度
        if method == 'rank':
            judge_ranks = n - np.argsort(np.argsort(judge_scores))
            vote_ranks = n - np.argsort(np.argsort(votes))
            combined = judge_ranks + vote_ranks
        else:
            judge_pct = judge_scores / np.sum(judge_scores)
            combined = judge_pct + votes
        
        sorted_combined = np.sort(combined)
        if len(sorted_combined) >= 2:
            gap = sorted_combined[-1] - sorted_combined[-2]  # 淘汰者与次低分的差距
            # 差距越小，确定性越高（因为只有窄区间能解释结果）
            certainty_gap_scalar = 1.0 / (gap + epsilon)
        else:
            gap = 0.0
            certainty_gap_scalar = 0.5
        
        # 为每个选手分配基于差距的确定性
        # 被淘汰选手和接近淘汰线的选手确定性较高
        certainty_gap = np.zeros(n)
        for i in range(n):
            combined_i = combined[i]
            # 越接近淘汰线，确定性越高
            rank_from_bottom = np.sum(combined >= combined_i)
            certainty_gap[i] = certainty_gap_scalar * (1.0 / (rank_from_bottom + epsilon))
        
        # 归一化各指标到[0,1]范围
        certainty_entropy_norm = certainty_entropy / (certainty_entropy.max() + epsilon)
        certainty_var_norm = certainty_var / (certainty_var.max() + epsilon)
        certainty_gini_norm = certainty_gini  # 已在[0,1]
        certainty_individual_norm = certainty_individual  # 已在[0,1]
        certainty_gap_norm = certainty_gap / (certainty_gap.max() + epsilon)
        
        # 综合确定性（加权平均）
        certainty_combined = (
            0.2 * certainty_entropy_norm +
            0.2 * certainty_var_norm +
            0.2 * certainty_gini_norm +
            0.2 * certainty_individual_norm +
            0.2 * certainty_gap_norm
        )
        
        # 归一化到合理范围
        certainty_combined = np.clip(certainty_combined, 0, 1)
        
        certainty_metrics = {
            'entropy_based': certainty_entropy.tolist(),
            'variance_based': certainty_var.tolist(),
            'gini_based': certainty_gini.tolist(),
            'individual_based': certainty_individual.tolist(),
            'gap_based': certainty_gap.tolist(),
            'combined': certainty_combined.tolist(),
            'vote_entropy': float(vote_entropy),
            'vote_variance': float(vote_var),
            'gini_coefficient': float(gini),
            'elimination_gap': float(gap)
        }
        
        return certainty_combined, certainty_metrics


# =============================================================================
# 7. 完整推断管道
# =============================================================================

class DWTSFanVoteEstimator:
    """
    DWTS粉丝投票估计器
    整合所有组件的完整推断管道
    """
    
    def __init__(self, softmax_temp=1.0, likelihood_temp=0.1):
        """
        Parameters:
        -----------
        softmax_temp : float
            效用到投票的Softmax温度
        likelihood_temp : float
            淘汰概率的Softmax温度
        """
        self.softmax_temp = softmax_temp
        self.likelihood_temp = likelihood_temp
        self.evaluator = ModelEvaluator()
    
    def get_voting_method(self, season):
        """根据赛季确定投票组合方式"""
        if season in [1, 2] or season >= 28:
            return 'rank'
        else:
            return 'percentage'
    
    def estimate_season_votes(self, season_df, season, use_mcmc=False, 
                               n_samples=3000, verbose=True):
        """
        估计整个赛季的粉丝投票
        
        Parameters:
        -----------
        season_df : pd.DataFrame
            赛季数据
        season : int
            赛季编号
        use_mcmc : bool
            是否使用MCMC进行不确定性量化
        n_samples : int
            MCMC采样数
        verbose : bool
            是否打印进度
            
        Returns:
        --------
        results : dict
            包含每周的投票估计结果
        """
        method = self.get_voting_method(season)
        idm = InverseDecisionModel(
            method=method, 
            softmax_temp=self.softmax_temp,
            likelihood_temp=self.likelihood_temp
        )
        sampler = MCMCSampler(idm)
        
        results = {
            'season': season,
            'method': method,
            'weeks': {}
        }
        
        # 找出该赛季的最大周数
        score_cols = [col for col in season_df.columns if col.startswith('week') and 'total_score' in col]
        max_week = max([int(col.split('_')[0].replace('week', '')) for col in score_cols])
        
        # 初始化先验（第一周使用均匀先验）
        prior_mean = None
        
        for week in range(1, max_week + 1):
            score_col = f'week{week}_total_score'
            if score_col not in season_df.columns:
                continue
            
            # 获取该周参赛选手
            contestants = get_week_contestants(season_df, week)
            if len(contestants) < 2:
                continue
            
            # 获取评委分数
            judge_scores = contestants[score_col].values.astype(float)
            contestant_names = contestants['celebrity_name'].values
            
            # 找出该周被淘汰的选手
            eliminated_mask = contestants['elimination_week'] == week
            
            if not eliminated_mask.any():
                # 该周没有淘汰
                if verbose:
                    print(f"  Week {week}: No elimination this week")
                continue
            
            eliminated_names = contestants[eliminated_mask]['celebrity_name'].values
            eliminated_idx = np.where(eliminated_mask)[0][0]  # 取第一个被淘汰的
            
            if verbose:
                print(f"  Week {week}: {len(contestants)} contestants, "
                      f"eliminated: {eliminated_names[0] if len(eliminated_names) > 0 else 'None'}")
            
            # 设置先验
            n = len(contestants)
            if prior_mean is None or len(prior_mean) != n:
                prior_mean = np.zeros(n)
            
            # MAP估计
            utilities_map, votes_map = idm.estimate_utilities_map(
                judge_scores, eliminated_idx, prior_mean=prior_mean, prior_std=1.0
            )
            
            # 计算一致性
            vote_probs = ForwardModel(self.softmax_temp).compute_vote_probability(utilities_map)
            if method == 'rank':
                combined = VotingCombiner.combine_by_rank(judge_scores, vote_probs)
            else:
                combined = VotingCombiner.combine_by_percentage(judge_scores, vote_probs)
            elim_probs = VotingCombiner.get_elimination_probability(
                combined, method=method, tau=self.likelihood_temp
            )
            consistency = self.evaluator.compute_consistency(elim_probs, eliminated_idx)
            is_consistent = self.evaluator.compute_consistency_hard(elim_probs, eliminated_idx)
            
            # 计算基于一致性的确定性（代理指标）
            certainty_consistency = self.evaluator.compute_certainty_consistency(consistency)
            
            # 从MAP估计计算确定性（无需MCMC）
            certainty_map, certainty_metrics = self.evaluator.compute_certainty_from_map(
                votes_map, judge_scores, eliminated_idx, method=method
            )
            
            week_result = {
                'contestants': contestant_names.tolist(),
                'judge_scores': judge_scores.tolist(),
                'eliminated': eliminated_names.tolist(),
                'eliminated_idx': eliminated_idx,
                'utilities_map': utilities_map.tolist(),
                'votes_map': votes_map.tolist(),
                'consistency': consistency,
                'is_consistent': is_consistent,
                'elim_probs': elim_probs.tolist(),
                # 确定性度量（基于MAP估计）
                'certainty_map': certainty_map.tolist(),
                'certainty_consistency': float(certainty_consistency),
                'certainty_metrics': {
                    'entropy_based': certainty_metrics['entropy_based'],  # 数组
                    'variance_based': certainty_metrics['variance_based'],  # 数组
                    'gini_based': certainty_metrics['gini_based'],  # 数组（每个选手一个值）
                    'individual_based': certainty_metrics['individual_based'],  # 数组
                    'gap_based': certainty_metrics['gap_based'],  # 数组
                    'combined': certainty_metrics['combined'],  # 数组
                    'vote_entropy': float(certainty_metrics['vote_entropy']),  # 标量
                    'vote_variance': float(certainty_metrics['vote_variance']),  # 标量
                    'gini_coefficient': float(certainty_metrics['gini_coefficient']),  # 标量
                    'elimination_gap': float(certainty_metrics['elimination_gap'])  # 标量
                }
            }
            
            # MCMC采样（可选，提供更精确的确定性度量）
            if use_mcmc:
                samples, accept_rate = sampler.sample(
                    judge_scores, eliminated_idx, 
                    n_samples=n_samples, burn_in=1000,
                    prior_mean=prior_mean, prior_std=1.0
                )
                stats = sampler.compute_posterior_statistics(samples)
                
                # 计算基于后验方差的确定性
                certainty_variance = self.evaluator.compute_certainty_variance(stats)
                
                # 计算基于信息熵的确定性
                vote_samples = np.array([softmax(s) for s in samples])
                certainty_entropy_mcmc, avg_entropy, individual_entropies = \
                    self.evaluator.compute_certainty_entropy(vote_samples)
                
                # 添加方差到stats中
                stats['vote_var'] = stats['vote_std'] ** 2
                # 论文 4.5.2 确定性 Φ_{i,t} = 1 / std(p_{i,t}^{MCMC})
                epsilon_cert = 1e-6
                certainty_phi = (1.0 / (np.asarray(stats['vote_std']) + epsilon_cert)).tolist()
                
                week_result.update({
                    'mcmc_accept_rate': accept_rate,
                    'votes_mean': stats['vote_mean'].tolist(),
                    'votes_std': stats['vote_std'].tolist(),
                    'votes_var': stats['vote_var'].tolist(),
                    'votes_ci_lower': stats['vote_ci_lower'].tolist(),
                    'votes_ci_upper': stats['vote_ci_upper'].tolist(),
                    # MCMC确定性度量
                    'certainty_variance_mcmc': certainty_variance.tolist(),
                    'certainty_entropy_mcmc': certainty_entropy_mcmc.tolist(),
                    'avg_entropy_mcmc': float(avg_entropy),
                    'ci_width': (np.array(stats['vote_ci_upper']) - 
                                 np.array(stats['vote_ci_lower'])).tolist(),
                    # 确定性 Φ = 1/std(p)（论文 4.5.2）
                    'certainty_phi': certainty_phi,
                    'certainty': certainty_phi,  # 供 analyze_certainty 等使用
                })
            
            results['weeks'][week] = week_result
            
            # 更新下一周的先验（使用当前后验均值）
            # 注意：选手数量可能变化，需要处理
            prior_mean = utilities_map.copy()
        
        return results
    
    def estimate_all_seasons(self, df, seasons=None, use_mcmc=False, verbose=True):
        """
        估计所有赛季的粉丝投票
        
        Parameters:
        -----------
        df : pd.DataFrame
            完整数据
        seasons : list or None
            要分析的赛季列表，None表示全部
        use_mcmc : bool
            是否使用MCMC
        verbose : bool
            是否打印进度
            
        Returns:
        --------
        all_results : dict
            所有赛季的结果
        """
        if seasons is None:
            seasons = sorted(df['season'].unique())
        
        all_results = {}
        
        for season in seasons:
            if verbose:
                print(f"\n{'='*50}")
                print(f"Processing Season {season}")
                print('='*50)
            
            season_df = get_season_data(df, season)
            results = self.estimate_season_votes(
                season_df, season, use_mcmc=use_mcmc, verbose=verbose
            )
            all_results[season] = results
        
        return all_results
    
    def compute_overall_metrics(self, all_results):
        """
        计算整体评估指标
        
        Parameters:
        -----------
        all_results : dict
            所有赛季的结果
            
        Returns:
        --------
        metrics : dict
            整体指标
        """
        all_consistencies = []
        all_hard_consistencies = []
        
        for season, season_result in all_results.items():
            for week, week_result in season_result['weeks'].items():
                all_consistencies.append(week_result['consistency'])
                all_hard_consistencies.append(week_result['is_consistent'])
        
        metrics = {
            'mean_consistency': np.mean(all_consistencies),
            'std_consistency': np.std(all_consistencies),
            'hard_accuracy': np.mean(all_hard_consistencies),
            'n_weeks_analyzed': len(all_consistencies)
        }
        
        return metrics


# =============================================================================
# 8. 主函数与使用示例
# =============================================================================

def main():
    """主函数：运行完整分析"""
    
    # 数据文件路径（请根据实际路径修改）
    data_path = '2026_MCM_Problem_C_Data.csv'
    
    print("="*60)
    print("DWTS 粉丝投票估计模型 - 基于逆向决策理论(IDM)")
    print("="*60)
    
    # 1. 加载数据
    print("\n[1] 加载数据...")
    try:
        df = load_and_preprocess_data(data_path)
        print(f"    数据加载成功！共 {len(df)} 条记录，{df['season'].nunique()} 个赛季")
    except FileNotFoundError:
        print(f"    错误：找不到数据文件 {data_path}")
        print("    请确保数据文件在正确路径")
        return None
    
    # 2. 创建估计器
    print("\n[2] 初始化模型...")
    estimator = DWTSFanVoteEstimator(
        softmax_temp=1.0,      # 效用到投票的温度参数
        likelihood_temp=0.1    # 淘汰概率的温度参数
    )
    
    # 3. 运行分析（先分析几个赛季作为示例）
    print("\n[3] 运行投票估计...")
    test_seasons = [1, 2, 3, 27, 28]  # 测试几个关键赛季
    
    results = estimator.estimate_all_seasons(
        df, 
        seasons=test_seasons,
        use_mcmc=False,  # 设为True可获得不确定性估计，但会更慢
        verbose=True
    )
    
    # 4. 计算整体指标
    print("\n[4] 计算评估指标...")
    metrics = estimator.compute_overall_metrics(results)
    
    print(f"\n{'='*60}")
    print("评估结果汇总")
    print('='*60)
    print(f"分析的周数: {metrics['n_weeks_analyzed']}")
    print(f"平均一致性（软）: {metrics['mean_consistency']:.4f} ± {metrics['std_consistency']:.4f}")
    print(f"硬一致性准确率: {metrics['hard_accuracy']*100:.2f}%")
    
    return results, metrics, df


if __name__ == "__main__":
    results = main()
