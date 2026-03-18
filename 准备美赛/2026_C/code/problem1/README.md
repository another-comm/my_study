# DWTS 粉丝投票估计 - MCM 2026 Problem C

基于逆向决策理论（Inverse Decision-Making, IDM）的粉丝投票推断模型

## 📋 目录

1. [项目概述](#项目概述)
2. [理论基础](#理论基础)
3. [文件结构](#文件结构)
4. [安装与环境](#安装与环境)
5. [使用指南](#使用指南)
6. [数据预处理](#数据预处理)
7. [模型说明](#模型说明)
8. [常见问题](#常见问题)

---

## 项目概述

本项目针对MCM 2026 Problem C《与星共舞》(Dancing with the Stars)问题，开发了基于认知科学中逆向决策理论的粉丝投票估计模型。

**核心思想**: 通过观察每周的淘汰结果，反向推断未公开的粉丝投票分布。

**参考文献**: Jern, A., Lucas, C. G., & Kemp, C. (2017). People learn other people's preferences through inverse decision-making. *Cognition*, 168, 46-64.

---

## 理论基础

### IDM模型框架

```
观察者（我们） ← 决策结果（淘汰） ← 决策者（粉丝集体）
        ↓
    反向推断
        ↓
   P(θ|E,S) ∝ P(E|θ,S) × P(θ)
```

其中:
- **θ**: 粉丝对各选手的潜在效用/人气
- **E**: 观察到的淘汰结果
- **S**: 已知的评委分数
- **P(θ|E,S)**: 后验分布（我们要求的）

### 正向模型（Forward Model）

**Luce选择公理 (Softmax)**:
```
p_i = exp(u_i / τ) / Σ_j exp(u_j / τ)
```
- `u_i`: 选手i的效用值
- `p_i`: 选手i的投票比例
- `τ`: 温度参数

### 逆向推断（Inverse Inference）

**贝叶斯推断**:
```
P(θ|E,S) = P(E|θ,S) × P(θ) / P(E|S)
```

**似然函数** (排名制):
```
P(E|θ,S) ∝ Sigmoid((f(E) - max_{j≠E} f(j)) / τ)
```

**似然函数** (百分比制):
```
P(E|θ,S) = exp(-g(E)/τ) / Σ_j exp(-g(j)/τ)
```

---

## 文件结构

```
code/
├── data_preprocessing.py           # 数据预处理模块
├── idm_fan_vote_model.py          # IDM核心模型
├── visualization_analysis.py       # 可视化与分析
├── advanced_analysis.py           # 高级分析（特征、舞者、新方案）
├── run_analysis.py                # 主运行脚本
├── test_preprocessing.py          # 预处理测试
├── requirements.txt               # 依赖包
├── README.md                      # 本文档
└── 2026_MCM_Problem_C_Data.csv   # 数据文件
```

### 模块说明

| 模块 | 功能 |
|------|------|
| **data_preprocessing.py** | 处理N/A值、0分、多舞蹈平均分等 |
| **idm_fan_vote_model.py** | IDM模型实现、MAP估计、MCMC采样 |
| **visualization_analysis.py** | 结果可视化、方法对比、争议案例 |
| **advanced_analysis.py** | 选手特征分析、舞者影响、新方案设计 |
| **run_analysis.py** | 整合所有分析的完整管道 |

---

## 安装与环境

### 1. Python环境

推荐使用Python 3.8+

### 2. 安装依赖

```bash
cd code
pip install -r requirements.txt
```

依赖包:
- numpy >= 1.21.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- matplotlib >= 3.4.0
- seaborn >= 0.11.0

### 3. 验证安装

```bash
python test_preprocessing.py
```

如果所有测试通过，环境配置成功。

---

## 使用指南

### 流程概览

1. **第一步：数据预处理（输出 Excel）**  
   对原始 CSV 做预处理，生成 `2026_MCM_Problem_C_Data_processed.xlsx`。

2. **第二步：后续分析**  
   所有分析脚本统一使用上述 **处理后的 Excel** 作为输入。

### 方式1: 命令行运行（推荐）

#### 第一步：运行预处理，生成 Excel
```bash
python data_preprocessing.py
```
或：
```bash
python -c "from data_preprocessing import quick_preprocess; quick_preprocess('2026_MCM_Problem_C_Data.csv')"
```
将得到：`2026_MCM_Problem_C_Data_processed.xlsx`（主表「数据」+ 说明表「数据说明」）。

#### 第二步：使用处理后的 Excel 进行分析
```bash
# 默认使用处理后的 Excel
python run_analysis.py --seasons 1 2 3 27 28

# 或显式指定 Excel 路径
python run_analysis.py --data 2026_MCM_Problem_C_Data_processed.xlsx --seasons 1 2 3 27 28
```

#### 完整分析（含MCMC不确定性量化）
```bash
python run_analysis.py --data 2026_MCM_Problem_C_Data_processed.xlsx --mcmc
```

#### 自定义输出目录
```bash
python run_analysis.py --data 2026_MCM_Problem_C_Data_processed.xlsx --output results_v2
```

**说明**：若在 `run_analysis.py` 中传入原始 CSV，程序会先执行预处理并保存 Excel，再使用预处理结果进行分析（适合一次性运行；推荐日常使用已生成的 Excel）。

### 方式2: 交互式Python

```python
# 1. 数据预处理（仅需对原始 CSV 执行一次，会生成 Excel）
from data_preprocessing import quick_preprocess, load_processed_excel, get_week_data

# 从原始 CSV 预处理并输出 Excel
df, stats, excel_path = quick_preprocess('2026_MCM_Problem_C_Data.csv')
print(f"加载了 {stats['n_seasons']} 个赛季的数据")
print(f"处理后的 Excel: {excel_path}")

# 后续分析可直接从 Excel 加载（推荐）
df = load_processed_excel('2026_MCM_Problem_C_Data_processed.xlsx')

# 查看特定周的数据
week_data = get_week_data(df, season=2, week=4)
print(week_data[['celebrity_name', 'week4_total_score']])

# 2. 运行IDM模型
from idm_fan_vote_model import DWTSFanVoteEstimator

estimator = DWTSFanVoteEstimator(
    softmax_temp=1.0,      # 效用→投票的温度
    likelihood_temp=0.1    # 淘汰概率的温度
)

# 估计投票
results = estimator.estimate_all_seasons(
    df, 
    seasons=[2, 27],  # 分析Season 2和27
    use_mcmc=False,   # 不使用MCMC（更快）
    verbose=True
)

# 计算评估指标
metrics = estimator.compute_overall_metrics(results)
print(f"一致性: {metrics['mean_consistency']:.4f}")
print(f"准确率: {metrics['hard_accuracy']*100:.2f}%")

# 3. 可视化
from visualization_analysis import plot_week_votes, plot_season_consistency

# 单周结果
week_result = results[2]['weeks'][4]
plot_week_votes(week_result, title='Season 2, Week 4')

# 整季一致性
plot_season_consistency(results[2])

# 4. 争议案例分析
from visualization_analysis import ControversyAnalyzer, plot_controversy_analysis

analyzer = ControversyAnalyzer(df)

# Jerry Rice (Season 2 亚军但评委分最低)
jerry = analyzer.analyze_controversy_case('Jerry Rice', 2, results)
plot_controversy_analysis(jerry)

# Bobby Bones (Season 27 冠军但评委分持续低)
bobby = analyzer.analyze_controversy_case('Bobby Bones', 27, results)
print(f"Bobby Bones 平均评委排名: {bobby['avg_judge_rank']:.2f}")
print(f"Bobby Bones 平均投票排名: {bobby['avg_vote_rank']:.2f}")

# 5. 方法对比
from visualization_analysis import VotingMethodComparator

comparator = VotingMethodComparator()

# 对比排名制和百分比制
judge_scores = week_result['judge_scores']
votes = week_result['votes_map']

comparison = comparator.compare_methods(judge_scores, votes)
print(f"两种方法结果是否不同: {comparison['any_difference']}")

# 6. 高级分析
from advanced_analysis import CelebrityFeatureAnalyzer, ProDancerAnalyzer

# 选手特征分析
celeb_analyzer = CelebrityFeatureAnalyzer(df)
industry_impact = celeb_analyzer.analyze_industry_impact()
print(industry_impact.head())

# 职业舞者分析
dancer_analyzer = ProDancerAnalyzer(df)
top_dancers = dancer_analyzer.get_top_dancers(5)
print(top_dancers)
```

---

## 数据预处理

### 为什么需要预处理？

根据题目说明，数据存在以下特殊情况：

1. **多舞蹈平均分**: 某些周有小数分（如8.5），因选手表演多个舞蹈
2. **额外积分**: 舞蹈淘汰赛等奖励分，均匀分配到评委分中
3. **团队舞蹈**: 团队分与个人分取平均
4. **N/A值**: 
   - 某些周只有3位评委（第4位评委分为N/A）
   - 节目未播出的周次（如Season 1只有6周，Week 7-11为N/A）
5. **0分**: 被淘汰选手在后续周的分数记为0
6. **评委变化**: 评委可能每周/每季不同

### 预处理流程

```python
from data_preprocessing import DWTSDataPreprocessor

preprocessor = DWTSDataPreprocessor('2026_MCM_Problem_C_Data.csv')

# 完整预处理
df, stats, validation = preprocessor.run_full_preprocessing()

# 步骤包括:
# 1. 加载原始数据
# 2. 检查数据结构
# 3. 解析results字段 → elimination_week
# 4. 提取评委分数 → weekX_total_score, weekX_judge_count
# 5. 处理0分（区分被淘汰 vs 真实0分）
# 6. 标识活跃选手 → weekX_active
# 7. 计算统计信息
# 8. 数据验证
```

### 预处理输出：Excel 文档

预处理会生成 **Excel 文件**（默认：`2026_MCM_Problem_C_Data_processed.xlsx`），包含两个 Sheet：

| Sheet 名称 | 内容 |
|------------|------|
| **数据** | 预处理后的完整数据表（后续分析统一使用此表） |
| **数据说明** | 字段说明与基本统计（总记录数、赛季数、选手数等） |

### 预处理后的关键字段（在「数据」Sheet 中）

| 字段 | 说明 | 示例 |
|------|------|------|
| `elimination_week` | 被淘汰的周次 | 4, 空(进决赛) |
| `weekX_total_score` | 第X周评委总分 | 28.5 |
| `weekX_judge_count` | 第X周评委人数 | 3或4 |
| `weekX_avg_score` | 第X周平均分 | 9.5 |
| `weekX_active` | 第X周是否活跃 | True/False |

### 验证预处理

```bash
python test_preprocessing.py
```

测试包括:
- ✓ 基础数据加载
- ✓ 数据结构检查
- ✓ 完整预处理流程
- ✓ 周数据提取
- ✓ 特定案例验证
- ✓ 数据一致性检查

---

## 模型说明

### 1. IDM核心模型

**类**: `InverseDecisionModel`

**核心方法**:
```python
model = InverseDecisionModel(
    method='percentage',     # 'rank' 或 'percentage'
    softmax_temp=1.0,       # 效用→投票温度
    likelihood_temp=0.1     # 淘汰概率温度
)

# MAP估计（快速）
utilities, votes = model.estimate_utilities_map(
    judge_scores, 
    eliminated_idx,
    prior_mean=None
)
```

### 2. MCMC采样器

**类**: `MCMCSampler`

**用途**: 量化不确定性，获得置信区间

```python
sampler = MCMCSampler(model, proposal_std=0.3)

samples, accept_rate = sampler.sample(
    judge_scores,
    eliminated_idx,
    n_samples=5000,
    burn_in=1000
)

# 后验统计
stats = sampler.compute_posterior_statistics(samples)
print(f"投票均值: {stats['vote_mean']}")
print(f"95% CI: [{stats['vote_ci_lower']}, {stats['vote_ci_upper']}]")
```

### 3. 评估指标

**软一致性**: 预测的淘汰概率与实际的匹配度
```python
consistency = predicted_elim_probs[actual_eliminated_idx]
```

**硬一致性**: 预测的淘汰者是否与实际一致
```python
is_consistent = (argmax(predicted_probs) == actual_eliminated_idx)
```

**确定性**: 基于后验方差
```python
certainty = 1 / (posterior_std + ε)
```

### 4. 参数调优建议

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `softmax_temp` | 0.5-1.5 | 越小越确定性，越大越随机 |
| `likelihood_temp` | 0.05-0.2 | 越小对淘汰结果越敏感 |
| `prior_std` | 0.5-2.0 | 先验分布宽度 |
| `n_samples` | 3000-10000 | MCMC采样数 |
| `burn_in` | 1000-2000 | MCMC预烧期 |

---

## 常见问题

### Q1: 运行时间很长怎么办？

**A**: 
- 不使用MCMC（去掉`--mcmc`参数）
- 只分析部分赛季：`--seasons 1 2 3`
- 减少MCMC采样数（修改代码中的`n_samples`）

### Q2: 一致性很低怎么办？

**A**: 
- 调整温度参数（`softmax_temp`和`likelihood_temp`）
- 检查数据预处理是否正确
- 某些周可能有特殊情况（如无淘汰）

### Q3: 如何解释结果？

**A**:
- **一致性 > 0.8**: 模型预测很准确
- **一致性 0.5-0.8**: 模型有一定预测能力
- **一致性 < 0.5**: 需要检查模型或数据

### Q4: 如何处理争议案例？

**A**:
```python
analyzer = ControversyAnalyzer(df)

# 分析
analysis = analyzer.analyze_controversy_case('Jerry Rice', 2, results)

# 模拟不同方法
simulation = analyzer.simulate_alternative_outcomes('Jerry Rice', 2, results)

print(simulation['recommendation'])
```

### Q5: 如何设计新的投票方案？

**A**:
```python
from advanced_analysis import VotingSchemeDesigner

designer = VotingSchemeDesigner()

# 加权方案（评委40%，粉丝60%）
def my_scheme(judge_scores, vote_props):
    return designer.weighted_combination(judge_scores, vote_props, 0.4, 0.6)

# 评估
eval_result = designer.evaluate_scheme(my_scheme, results)
print(f"差异率: {eval_result['eliminated_diff_rate']*100:.1f}%")
```

---

## 输出文件说明

运行`run_analysis.py`后，输出目录包含：

```
results/
├── metrics.json                    # 整体评估指标
├── vote_estimates.json            # 详细投票估计
├── controversy_analysis.json      # 争议案例分析
├── summary_report.txt             # 文本摘要
├── consistency_season_X.png       # 各赛季一致性图
├── controversy_Jerry_Rice_s2.png  # 争议案例图
└── votes_season_X_week_Y.png      # 周投票图
```

---

## 引用

如果使用本模型，请引用：

**理论基础**:
```
Jern, A., Lucas, C. G., & Kemp, C. (2017). 
People learn other people's preferences through inverse decision-making. 
Cognition, 168, 46-64.
```

**问题来源**:
```
COMAP Mathematical Contest in Modeling (MCM) 2026, Problem C: 
Data With The Stars
```

---

## 联系与支持

- 数据文件: `2026_MCM_Problem_C_Data.csv`
- 问题说明: `2026_MCM_Problem_C.pdf`
- 代码仓库: 本地目录 `c:\study\准备美赛\2026_C\code`

---

## 许可

本项目仅用于MCM 2026竞赛，遵守COMAP竞赛规则和AI使用政策。

---

**祝比赛顺利！🎉**
