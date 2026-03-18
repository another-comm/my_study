# 确定性度量方法说明

## 概述

根据 Jern 等人的逆向决策理论，推断的确定性取决于后验分布的集中程度。本代码实现了多种确定性度量方法。

## 实现的确定性度量方法

### 1. 基于后验方差的确定性（MCMC方法）

**公式**：
```
Certainty = 1 / Var(θ|E,S)
```

**实现**：`ModelEvaluator.compute_certainty_variance()`

**说明**：
- 需要MCMC采样获得后验分布
- 方差越小，后验分布越集中，确定性越高
- 返回每个选手的确定性数组

**使用场景**：当使用 `--mcmc` 参数运行分析时

---

### 2. 基于信息熵的确定性（MCMC方法）

**公式**：
```
Entropy = -Σ p_i log(p_i)
Certainty ∝ 1 / Entropy
```

**实现**：`ModelEvaluator.compute_certainty_entropy()`

**说明**：
- 需要MCMC采样获得投票比例样本
- 熵越低，投票分布越集中，确定性越高
- 返回每个选手的确定性数组、平均熵、每个样本的熵

**使用场景**：当使用 `--mcmc` 参数运行分析时

---

### 3. 基于一致性的确定性（代理指标）

**公式**：
```
Certainty ∝ Consistency = P(E | θ_MAP, S)
```

**实现**：`ModelEvaluator.compute_certainty_consistency()`

**说明**：
- 无需MCMC，使用MAP估计即可
- 一致性越高，确定性越高
- 返回标量值

**使用场景**：所有分析（默认计算）

---

### 4. 基于MAP估计的综合确定性（无需MCMC）

**实现**：`ModelEvaluator.compute_certainty_from_map()`

**说明**：
- 无需MCMC，使用MAP估计的投票分布
- 综合多种方法计算确定性

**包含的子方法**：

#### 4.1 基于投票分布熵的确定性
- 计算整体投票分布的熵
- 熵越低，确定性越高

#### 4.2 基于投票分布方差的确定性
- 计算投票分布的方差
- 方差越小，确定性越高

#### 4.3 基于Gini系数的确定性
- 计算投票分布的Gini系数
- Gini越高，分布越集中，确定性越高

#### 4.4 基于个体投票比例的确定性
- 投票比例越接近0或1，确定性越高
- 投票比例越接近均匀分布，确定性越低

#### 4.5 基于淘汰边缘接近程度的确定性
- 越接近淘汰线，确定性越高
- 差距越小，只有窄区间能解释结果，确定性越高

**综合方法**：
```python
certainty_combined = (
    0.2 * entropy_based +
    0.2 * variance_based +
    0.2 * gini_based +
    0.2 * individual_based +
    0.2 * gap_based
)
```

**使用场景**：所有分析（默认计算）

---

## 结果中的确定性字段

### MAP估计结果（默认）

每个周次的结果包含以下确定性字段：

```python
{
    'certainty_map': [float, ...],  # 综合确定性（每个选手）
    'certainty_consistency': float,  # 基于一致性的确定性
    'certainty_metrics': {
        'entropy_based': [float, ...],
        'variance_based': [float, ...],
        'gini_based': [float, ...],
        'individual_based': [float, ...],
        'gap_based': [float, ...],
        'combined': [float, ...],
        'vote_entropy': float,
        'vote_variance': float,
        'gini_coefficient': float,
        'elimination_gap': float
    }
}
```

### MCMC结果（使用 --mcmc 时）

额外包含：

```python
{
    'certainty_variance_mcmc': [float, ...],  # 基于后验方差的确定性
    'certainty_entropy_mcmc': [float, ...],   # 基于信息熵的确定性
    'avg_entropy_mcmc': float,                 # 平均熵
    'votes_std': [float, ...],                 # 投票比例标准差
    'votes_var': [float, ...],                 # 投票比例方差
    'votes_ci_lower': [float, ...],           # 95%置信区间下界
    'votes_ci_upper': [float, ...],           # 95%置信区间上界
    'ci_width': [float, ...]                  # 置信区间宽度
}
```

---

## 确定性因情境而异

### 高确定性场景

- **特征**：选手处于淘汰边缘，只有极窄的票数区间能解释其"死里逃生"
- **表现**：后验分布较窄，方差较小，确定性极高
- **示例**：排名和差距很小的周次

### 低确定性场景

- **特征**：评委分领先很多，粉丝投票的大幅波动都不会改变淘汰结果
- **表现**：后验分布较宽，方差较大，确定性较低
- **示例**：评委分差距很大的周次

### 实际观察

- **排名制赛季**：平均一致性 0.75-1.0 → 确定性较高
- **百分比制赛季**：平均一致性 0.17-0.34 → 确定性较低
- **一致性标准差**：0.3285 → 说明不同周次间确定性存在显著差异

---

## 使用示例

### 基本使用（MAP估计）

```python
from idm_fan_vote_model import DWTSFanVoteEstimator

estimator = DWTSFanVoteEstimator()
results = estimator.estimate_all_seasons(df, seasons=[1, 2], use_mcmc=False)

# 访问确定性
for season, season_result in results.items():
    for week, week_result in season_result['weeks'].items():
        certainty_map = week_result['certainty_map']
        certainty_consistency = week_result['certainty_consistency']
        certainty_metrics = week_result['certainty_metrics']
        
        print(f"Season {season}, Week {week}:")
        print(f"  综合确定性: {certainty_map}")
        print(f"  一致性确定性: {certainty_consistency}")
        print(f"  投票分布熵: {certainty_metrics['vote_entropy']}")
```

### 使用MCMC（精确度量）

```python
results = estimator.estimate_all_seasons(df, seasons=[1, 2], use_mcmc=True)

# 访问MCMC确定性
for season, season_result in results.items():
    for week, week_result in season_result['weeks'].items():
        if 'certainty_variance_mcmc' in week_result:
            certainty_var = week_result['certainty_variance_mcmc']
            certainty_entropy = week_result['certainty_entropy_mcmc']
            ci_width = week_result['ci_width']
            
            print(f"Season {season}, Week {week}:")
            print(f"  基于方差的确定性: {certainty_var}")
            print(f"  基于熵的确定性: {certainty_entropy}")
            print(f"  置信区间宽度: {ci_width}")
```

---

## 代码位置

- **ModelEvaluator类**：`idm_fan_vote_model.py` lines 654-741
- **确定性计算**：`estimate_season_votes()` 方法中
- **MCMC采样**：`MCMCSampler` 类

---

## 参考文献

Jern, A., Lucas, C. G., & Kemp, C. (2017). People learn other people's preferences through inverse decision-making. *Cognition*, 168, 46-64.
