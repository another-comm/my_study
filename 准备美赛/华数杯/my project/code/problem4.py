import numpy as np
import pandas as pd

from ai_common import calculate_entropy_weights, compute_dim_scores_and_weights, forecast_arima_series, sigmoid_normalize
from ai_data19 import DIM_MAP_5, INDICATOR_COLS_19, load_history_19

try:
    # 用于“最优规划/非线性规划”求解（可选依赖）
    from scipy.optimize import minimize
except Exception:
    minimize = None


DATA_CSV_PATH = None
FUTURE_YEARS = np.arange(2026, 2036)
TARGET_COUNTRY = "China"

# 1 万亿：默认理解为 2026-2035 十年总额
TOTAL_BUDGET = 1_000_000_000_000  # 元

# 贪心分配的粒度（越小越精细，但越慢）
DELTA_BUDGET = 10_000_000_000  # 100 亿/步；总共 100 步

# 目标函数：从“只看 2035”改为“看 2026-2035 多年综合收益（默认加权平均）”
OBJECTIVE_YEARS = FUTURE_YEARS  # 可改：例如 np.arange(2031, 2036) 更强调后期
# 权重模式：
# - "equal": 每年等权（加权平均）
# - "discount": 折现权重，越靠后的年份权重越大/越小由 gamma 决定
OBJECTIVE_WEIGHT_MODE = "equal"
OBJECTIVE_DISCOUNT_GAMMA = 1.0  # discount 模式下使用；gamma>1 更偏后期，gamma<1 更偏前期

# 求解方式：
# - "nlp": 非线性规划（需要 scipy）
# - "greedy": 离散粒度贪心（当前实现）
SOLVER = "nlp"
NLP_MULTI_STARTS = 8
NLP_MAXITER = 400
NLP_SEED = 42

# 单年总额上限（可选：None 表示不限制）
YEAR_BUDGET_CAP = None  # 例如 150_000_000_000

# 维度资金结构约束（避免“全砸一个维度”）
# - min_share: 每个维度至少占总预算的比例
# - max_share: 每个维度最多占总预算的比例
# 你可以按论文叙事调整（例如更偏基础设施/人才等）
DIM_BUDGET_MIN_SHARE = {
    "Talent": 0.15,
    "Research": 0.15,
    "Infrastructure": 0.25,
    "Economy": 0.15,
    "Policy": 0.10,
}
DIM_BUDGET_MAX_SHARE = {
    "Talent": 0.35,
    "Research": 0.30,
    "Infrastructure": 0.50,
    "Economy": 0.30,
    "Policy": 0.20,
}

# Sigmoid 归一化陡峭度（与你问题2/3保持一致）
ALPHA_SIGMOID = 2.0

# 投资方向（5维）-> 影响参数
# - lag: 投资到产生效果的滞后年数
# - B: 边际递减的尺度参数（元），越小表示“更快饱和”
# - S: 对应“标准化 z 分数”的提升强度系数（越大越激进）
# - decay: 投资随时间衰减（越小越偏向近年）
DIM_INVEST_CONFIG = {
    "Talent": {"lag": 2, "B": 180_000_000_000, "S": 0.28, "decay": 0.97},
    "Research": {"lag": 2, "B": 160_000_000_000, "S": 0.24, "decay": 0.97},
    "Infrastructure": {"lag": 1, "B": 260_000_000_000, "S": 0.30, "decay": 0.98},
    "Economy": {"lag": 1, "B": 140_000_000_000, "S": 0.18, "decay": 0.98},
    "Policy": {"lag": 0, "B": 80_000_000_000, "S": 0.14, "decay": 0.99},
}


def _check_budget_share_config(dims: list[str]) -> None:
    """检查 min/max 配置是否覆盖所有维度且可行。"""
    for d in dims:
        if d not in DIM_BUDGET_MIN_SHARE or d not in DIM_BUDGET_MAX_SHARE:
            raise ValueError(f"维度资金约束缺失: {d} 未在 DIM_BUDGET_MIN_SHARE / DIM_BUDGET_MAX_SHARE 中配置")
        if DIM_BUDGET_MIN_SHARE[d] < 0 or DIM_BUDGET_MAX_SHARE[d] <= 0:
            raise ValueError(f"维度资金约束非法: {d}")
        if DIM_BUDGET_MIN_SHARE[d] > DIM_BUDGET_MAX_SHARE[d]:
            raise ValueError(f"维度资金约束不可行: {d} 的 min_share > max_share")
    s_min = sum(DIM_BUDGET_MIN_SHARE[d] for d in dims)
    if s_min > 1.0 + 1e-9:
        raise ValueError(f"维度最低占比之和超过 1：sum(min_share)={s_min}")


def _can_meet_min_shares(allocated_by_dim: dict[str, float], remaining_budget: float, dims: list[str]) -> bool:
    """检查剩余预算是否足够补齐所有维度的最低预算。"""
    need = 0.0
    for d in dims:
        min_budget = DIM_BUDGET_MIN_SHARE[d] * TOTAL_BUDGET
        need += max(0.0, min_budget - allocated_by_dim.get(d, 0.0))
    return remaining_budget + 1e-9 >= need

# （sigmoid_normalize / 熵权 / forecast_arima_series 已在 ai_common.py 中复用）


def score_from_raw_19(
    raw_vals_19: np.ndarray,
    indicator_cols: list[str],
    dim_map: dict,
    global_mean: np.ndarray,
    global_std: np.ndarray,
    dim_inner_weights: dict,
    dim_between_weights: np.ndarray,
) -> float:
    """raw_vals_19: shape (19,) 或 (1,19)"""
    x = np.asarray(raw_vals_19, dtype=float)
    if x.ndim == 1:
        x = x.reshape(1, -1)
    z = sigmoid_normalize(x, global_mean, global_std, ALPHA_SIGMOID)  # (1,19)
    col_idx = {c: i for i, c in enumerate(indicator_cols)}
    dim_scores = []
    for dim, cols in dim_map.items():
        idxs = [col_idx[c] for c in cols]
        w_inner = dim_inner_weights[dim]
        dim_scores.append(float(z[:, idxs] @ w_inner))
    dim_scores = np.asarray(dim_scores, dtype=float)  # (5,)
    return float(dim_scores @ dim_between_weights) * 100.0


def build_investment_impact_weights(indicator_cols: list[str], dim_map: dict, dim_inner_weights: dict) -> dict[str, np.ndarray]:
    """
    返回每个维度 k 对 19 指标的分摊权重 pi_{k,i}（sum_i pi=1，非该维度指标为0）。
    用维度内熵权作为分摊依据，解释性强且与评价体系一致。
    """
    col_idx = {c: i for i, c in enumerate(indicator_cols)}
    pi = {}
    for dim, cols in dim_map.items():
        w_inner = np.asarray(dim_inner_weights[dim], dtype=float).flatten()
        w_inner = w_inner / (w_inner.sum() + 1e-12)
        v = np.zeros(len(indicator_cols), dtype=float)
        for j, c in enumerate(cols):
            v[col_idx[c]] = w_inner[j]
        pi[dim] = v
    return pi


def delta_raw_from_plan(
    plan_u: dict[int, dict[str, float]],
    target_year: int,
    indicator_cols: list[str],
    global_std: np.ndarray,
    pi_dim_to_indicator: dict[str, np.ndarray],
) -> np.ndarray:
    """
    给定计划 plan_u[year][dim]=资金，输出对 target_year 的 19 指标原始值增量（shape (19,)）。
    这里采用：标准化提升 = S * log1p(u/B) * decay^(target-(year+lag))，再乘 global_std 转回原始尺度。
    """
    delta = np.zeros(len(indicator_cols), dtype=float)
    for y, by_dim in plan_u.items():
        for dim, money in by_dim.items():
            if money <= 0:
                continue
            cfg = DIM_INVEST_CONFIG[dim]
            lag = int(cfg["lag"])
            eff_year = y + lag
            if eff_year > target_year:
                continue
            decay = float(cfg["decay"])
            years_diff = target_year - eff_year
            time_weight = decay ** years_diff
            B = float(cfg["B"])
            S = float(cfg["S"])
            # 标准化提升（边际递减）
            delta_z = S * np.log1p(money / B) * time_weight
            # 分摊到该维度所属指标，再转成原始尺度（使用 global_std 把“标准化提升”转回原尺度）
            delta += (pi_dim_to_indicator[dim] * delta_z) * global_std
    return delta


def delta_raw_matrix_from_plan(
    plan_u: dict[int, dict[str, float]],
    target_years: list[int],
    indicator_cols: list[str],
    global_std: np.ndarray,
    pi_dim_to_indicator: dict[str, np.ndarray],
) -> np.ndarray:
    """
    给定计划 plan_u[year][dim]=资金，输出对多个 target_years 的 19 指标原始值增量矩阵（shape (M,19)）。
    相比逐年调用 delta_raw_from_plan，这里在一次遍历中累加，更适合多年目标函数。
    """
    tys = np.asarray(sorted([int(y) for y in target_years]), dtype=int)
    if tys.size == 0:
        raise ValueError("target_years 不能为空")
    M = int(tys.size)
    I = len(indicator_cols)
    delta_mat = np.zeros((M, I), dtype=float)
    std = np.asarray(global_std, dtype=float).reshape(1, -1)  # (1,I)

    for y, by_dim in plan_u.items():
        y = int(y)
        for dim, money in by_dim.items():
            if money <= 0:
                continue
            cfg = DIM_INVEST_CONFIG[dim]
            lag = int(cfg["lag"])
            eff_year = y + lag
            if eff_year > int(tys[-1]):
                continue
            decay = float(cfg["decay"])
            B = float(cfg["B"])
            S = float(cfg["S"])
            base = float(S * np.log1p(money / B))
            if base == 0.0:
                continue

            start = int(np.searchsorted(tys, eff_year, side="left"))
            years_diff = (tys[start:] - eff_year).astype(float)
            time_weight = (decay ** years_diff).reshape(-1, 1)  # (M-start,1)
            dz = base * time_weight  # (M-start,1)
            delta_mat[start:, :] += (dz * pi_dim_to_indicator[dim].reshape(1, -1)) * std

    return delta_mat


def _objective_year_weights(years: list[int]) -> np.ndarray:
    """返回长度为 T 的权重（和为1），用于多年综合收益。"""
    T = len(years)
    if T == 0:
        raise ValueError("OBJECTIVE_YEARS 不能为空")
    mode = str(OBJECTIVE_WEIGHT_MODE).lower()
    if mode == "equal":
        w = np.ones(T, dtype=float)
    elif mode == "discount":
        gamma = float(OBJECTIVE_DISCOUNT_GAMMA)
        # 这里用“年份序号”做折现：t=0..T-1
        w = np.array([gamma**t for t in range(T)], dtype=float)
    else:
        raise ValueError(f"未知 OBJECTIVE_WEIGHT_MODE: {OBJECTIVE_WEIGHT_MODE}")
    w = w / (w.sum() + 1e-12)
    return w


def _scores_from_raw_matrix_19(
    raw_mat: np.ndarray,
    indicator_cols: list[str],
    dim_map: dict,
    global_mean: np.ndarray,
    global_std: np.ndarray,
    dim_inner_weights: dict,
    dim_between_weights: np.ndarray,
) -> np.ndarray:
    """raw_mat shape=(T,19) -> scores shape=(T,)"""
    x = np.asarray(raw_mat, dtype=float)
    if x.ndim != 2:
        raise ValueError("raw_mat 必须是二维数组 (T,19)")
    z = sigmoid_normalize(x, global_mean, global_std, ALPHA_SIGMOID)  # (T,19)
    col_idx = {c: i for i, c in enumerate(indicator_cols)}
    dim_scores = []
    for dim, cols in dim_map.items():
        idxs = [col_idx[c] for c in cols]
        w_inner = np.asarray(dim_inner_weights[dim], dtype=float).reshape(-1)
        dim_scores.append(z[:, idxs] @ w_inner)  # (T,)
    dim_scores = np.stack(dim_scores, axis=1)  # (T,5)
    w_between = np.asarray(dim_between_weights, dtype=float).reshape(-1)  # (5,)
    return (dim_scores @ w_between) * 100.0


def greedy_optimize_plan(
    baseline_raw_future: np.ndarray,
    indicator_cols: list[str],
    dim_map: dict,
    global_mean: np.ndarray,
    global_std: np.ndarray,
    dim_inner_weights: dict,
    dim_between_weights: np.ndarray,
) -> tuple[dict[int, dict[str, float]], float, float]:
    years = [int(y) for y in list(FUTURE_YEARS)]
    obj_years = sorted([int(y) for y in list(OBJECTIVE_YEARS)])
    if len(obj_years) == 0:
        raise ValueError("OBJECTIVE_YEARS 不能为空")
    idx_map = {y: i for i, y in enumerate(years)}
    try:
        obj_idxs = [idx_map[y] for y in obj_years]
    except KeyError as e:
        raise ValueError(f"OBJECTIVE_YEARS 必须是 FUTURE_YEARS 的子集，找不到年份: {e}")
    w_year = _objective_year_weights(obj_years)
    max_obj_year = max(obj_years)
    dims = list(dim_map.keys())
    _check_budget_share_config(dims)

    pi = build_investment_impact_weights(indicator_cols, dim_map, dim_inner_weights)

    plan_u: dict[int, dict[str, float]] = {int(y): {d: 0.0 for d in dims} for y in years}
    used = 0.0
    allocated_by_dim = {d: 0.0 for d in dims}

    baseline_obj_scores = _scores_from_raw_matrix_19(
        np.asarray(baseline_raw_future, dtype=float)[obj_idxs, :],
        indicator_cols,
        dim_map,
        global_mean,
        global_std,
        dim_inner_weights,
        dim_between_weights,
    )
    base_obj = float(np.sum(w_year * baseline_obj_scores))

    def objective_from_plan() -> float:
        delta_mat = delta_raw_matrix_from_plan(plan_u, obj_years, indicator_cols, global_std, pi)  # (M,19)
        raw_mat = np.asarray(baseline_raw_future, dtype=float)[obj_idxs, :] + delta_mat
        scores = _scores_from_raw_matrix_19(
            raw_mat, indicator_cols, dim_map, global_mean, global_std, dim_inner_weights, dim_between_weights
        )
        return float(np.sum(w_year * scores))

    steps = int(np.round(TOTAL_BUDGET / DELTA_BUDGET))
    for step in range(steps):
        best_gain = -np.inf
        best_choice = None  # (year, dim)

        current_obj = objective_from_plan()

        for y in years:
            y = int(y)
            # 单年上限
            if YEAR_BUDGET_CAP is not None:
                year_total = sum(plan_u[y].values())
                if year_total + DELTA_BUDGET > YEAR_BUDGET_CAP:
                    continue
            for dim in dims:
                lag = int(DIM_INVEST_CONFIG[dim]["lag"])
                # 若对任何目标年份都不可能生效，则跳过（避免无意义变量导致解退化）
                if y + lag > max_obj_year:
                    continue

                # 维度最大占比约束：不能超过 max_share
                max_budget_dim = DIM_BUDGET_MAX_SHARE[dim] * TOTAL_BUDGET
                if allocated_by_dim[dim] + DELTA_BUDGET > max_budget_dim + 1e-9:
                    continue

                # 可行性检查：投完这一笔后，剩余预算必须还能补齐所有维度的最低占比
                remaining_after = TOTAL_BUDGET - (used + DELTA_BUDGET)
                allocated_by_dim[dim] += DELTA_BUDGET
                feasible = _can_meet_min_shares(allocated_by_dim, remaining_after, dims)
                allocated_by_dim[dim] -= DELTA_BUDGET
                if not feasible:
                    continue

                # 试投一小步
                plan_u[y][dim] += DELTA_BUDGET
                trial_obj = objective_from_plan()
                gain = trial_obj - current_obj
                plan_u[y][dim] -= DELTA_BUDGET

                if gain > best_gain:
                    best_gain = gain
                    best_choice = (y, dim)

        if best_choice is None:
            break

        y_best, d_best = best_choice
        plan_u[y_best][d_best] += DELTA_BUDGET
        used += DELTA_BUDGET
        allocated_by_dim[d_best] += DELTA_BUDGET

        if (step + 1) % 10 == 0 or step == steps - 1:
            print(
                f"[优化] 步骤 {step+1}/{steps}，已分配 {used/1e12:.2f} 万亿，当前目标(多年加权)={current_obj:.4f}，本步增益={best_gain:.6f}（{y_best}-{d_best}）"
            )

    # 最终检查：若有维度未达最低占比，进行兜底补齐（尽量从“超过最低占比最多且边际贡献最小”的维度挪）
    # 注：理论上上面的可行性检查应保证最终可满足；这段主要是防浮点误差/粒度不整除。
    min_budget_by_dim = {d: DIM_BUDGET_MIN_SHARE[d] * TOTAL_BUDGET for d in dims}
    shortage = {d: max(0.0, min_budget_by_dim[d] - allocated_by_dim[d]) for d in dims}
    if any(v > 1e-6 for v in shortage.values()):
        print("[提示] 检测到维度最低占比未完全满足，正在进行兜底补齐（可能由粒度/浮点造成）…")
        # 先把每个短缺维度补齐到最近的 DELTA_BUDGET 整数倍
        for d in dims:
            if shortage[d] <= 0:
                continue
            need_steps = int(np.ceil(shortage[d] / DELTA_BUDGET))
            for _ in range(need_steps):
                # 从可挪出的维度里找一个：当前超出最低占比最多
                donors = [x for x in dims if allocated_by_dim[x] - min_budget_by_dim[x] >= DELTA_BUDGET - 1e-9]
                if not donors:
                    break
                donor = max(donors, key=lambda x: allocated_by_dim[x] - min_budget_by_dim[x])

                # 在 donor 里找一个年份把 DELTA_BUDGET 挪到 d：优先从“最晚年份”挪（对 2035 更不利的挪走）
                donor_years = [yy for yy in years if plan_u[int(yy)][donor] >= DELTA_BUDGET - 1e-9]
                recv_years = years
                if not donor_years:
                    break
                yy_d = int(max(donor_years))
                yy_r = int(min(recv_years))  # 先补到最早年份，便于滞后生效

                plan_u[yy_d][donor] -= DELTA_BUDGET
                plan_u[yy_r][d] += DELTA_BUDGET
                allocated_by_dim[donor] -= DELTA_BUDGET
                allocated_by_dim[d] += DELTA_BUDGET

    final_obj = objective_from_plan()
    return plan_u, base_obj, final_obj


def _vector_to_plan(
    u_flat: np.ndarray,
    years: list[int],
    dims: list[str],
) -> dict[int, dict[str, float]]:
    T = len(years)
    K = len(dims)
    u = np.asarray(u_flat, dtype=float).reshape(T, K)
    plan_u: dict[int, dict[str, float]] = {}
    for t, y in enumerate(years):
        plan_u[int(y)] = {dims[k]: float(max(0.0, u[t, k])) for k in range(K)}
    return plan_u


def _allocate_with_bounds(total: float, lower: np.ndarray, upper: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    生成一个满足 lower<=x<=upper 且 sum(x)=total 的可行向量。
    用于非线性规划多起点初始化。
    """
    lower = np.asarray(lower, dtype=float).copy()
    upper = np.asarray(upper, dtype=float).copy()
    if np.any(upper < lower - 1e-9):
        raise ValueError("allocate_with_bounds: upper < lower")
    slack = upper - lower
    remaining = float(total - lower.sum())
    if remaining < -1e-6:
        raise ValueError("allocate_with_bounds: total < sum(lower)")
    if remaining > slack.sum() + 1e-6:
        raise ValueError("allocate_with_bounds: total > sum(upper)")
    if remaining <= 1e-9 or slack.sum() <= 1e-12:
        return lower

    x = lower.copy()
    # 先按随机权重分一轮
    p = rng.random(len(lower))
    p = p / (p.sum() + 1e-12)
    add = np.minimum(slack, remaining * p)
    x += add
    remaining = float(total - x.sum())

    # 若还有剩余，按“仍有余量的维度”继续分配
    guard = 0
    while remaining > 1e-7 and guard < 50:
        cap = upper - x
        idx = np.where(cap > 1e-9)[0]
        if idx.size == 0:
            break
        p2 = rng.random(idx.size)
        p2 = p2 / (p2.sum() + 1e-12)
        add2 = np.minimum(cap[idx], remaining * p2)
        x[idx] += add2
        remaining = float(total - x.sum())
        guard += 1

    # 兜底：把数值误差归并到仍可加的第一个位置
    if abs(total - x.sum()) > 1e-5:
        cap = upper - x
        idx = int(np.argmax(cap))
        x[idx] += float(total - x.sum())
        x = np.minimum(np.maximum(x, lower), upper)
    return x


def optimize_plan_nlp(
    baseline_raw_future: np.ndarray,
    indicator_cols: list[str],
    dim_map: dict,
    global_mean: np.ndarray,
    global_std: np.ndarray,
    dim_inner_weights: dict,
    dim_between_weights: np.ndarray,
) -> tuple[dict[int, dict[str, float]], float, float]:
    """
    “最优规划”版本：把 u_{t,k}（year×dim）作为连续变量，直接最大化 2026-2035 多年综合收益（加权平均）。
    由于 log+sigmoid 的存在，这是一个光滑但非凸的非线性规划；默认用 SLSQP 多起点近似求解。
    若 scipy 不可用，则自动回退到贪心版本。
    """
    years = [int(y) for y in list(FUTURE_YEARS)]
    obj_years = sorted([int(y) for y in list(OBJECTIVE_YEARS)])
    if len(obj_years) == 0:
        raise ValueError("OBJECTIVE_YEARS 不能为空")
    idx_map = {y: i for i, y in enumerate(years)}
    try:
        obj_idxs = [idx_map[y] for y in obj_years]
    except KeyError as e:
        raise ValueError(f"OBJECTIVE_YEARS 必须是 FUTURE_YEARS 的子集，找不到年份: {e}")
    w_year = _objective_year_weights(obj_years)
    max_obj_year = max(obj_years)

    dims = list(dim_map.keys())
    _check_budget_share_config(dims)

    baseline_scores_obj = _scores_from_raw_matrix_19(
        np.asarray(baseline_raw_future, dtype=float)[obj_idxs, :],
        indicator_cols,
        dim_map,
        global_mean,
        global_std,
        dim_inner_weights,
        dim_between_weights,
    )
    base_obj = float(np.sum(w_year * baseline_scores_obj))

    if minimize is None:
        print("[提示] 未检测到 scipy，无法进行非线性规划求解；将回退为贪心分配。建议安装：pip install scipy")
        plan_u, _, final_obj = greedy_optimize_plan(
            baseline_raw_future,
            indicator_cols,
            dim_map,
            global_mean,
            global_std,
            dim_inner_weights,
            dim_between_weights,
        )
        return plan_u, base_obj, final_obj

    # 预计算：pi(K,I)、参数向量
    pi = build_investment_impact_weights(indicator_cols, dim_map, dim_inner_weights)
    K = len(dims)
    T = len(years)
    I = len(indicator_cols)

    pi_mat = np.vstack([pi[d] for d in dims]).astype(float)  # (K,I)
    std = np.asarray(global_std, dtype=float).reshape(-1)  # (I,)

    B = np.array([float(DIM_INVEST_CONFIG[d]["B"]) for d in dims], dtype=float)  # (K,)
    S = np.array([float(DIM_INVEST_CONFIG[d]["S"]) for d in dims], dtype=float)  # (K,)
    decay = np.array([float(DIM_INVEST_CONFIG[d]["decay"]) for d in dims], dtype=float)  # (K,)
    lag = np.array([int(DIM_INVEST_CONFIG[d]["lag"]) for d in dims], dtype=int)  # (K,)

    # 预计算：score 计算用的维度索引（加速 objective）
    col_idx = {c: i for i, c in enumerate(indicator_cols)}
    dim_idxs = [[col_idx[c] for c in dim_map[d]] for d in dims]
    w_inner_list = [np.asarray(dim_inner_weights[d], dtype=float).reshape(-1) for d in dims]
    w_between = np.asarray(dim_between_weights, dtype=float).reshape(-1)

    def scores_from_raw_mat(raw_mat: np.ndarray) -> np.ndarray:
        z = sigmoid_normalize(np.asarray(raw_mat, dtype=float), global_mean, global_std, ALPHA_SIGMOID)  # (T,19)
        dim_scores = []
        for k in range(K):
            dim_scores.append(z[:, dim_idxs[k]] @ w_inner_list[k])
        dim_scores = np.stack(dim_scores, axis=1)  # (T,5)
        return (dim_scores @ w_between) * 100.0  # (T,)

    # 目标：最大化多年加权得分 => 最小化负值
    def objective(u_flat: np.ndarray) -> float:
        u = np.asarray(u_flat, dtype=float).reshape(T, K)
        u = np.clip(u, 0.0, None)

        # 先算每笔投入的“基础标准化提升”（不含滞后/衰减传播）
        base_tk = S.reshape(1, -1) * np.log1p(u / B.reshape(1, -1))  # (T,K)

        # 传播到每个评估年份：dz_year_k[tau,k]
        dz_year_k = np.zeros((T, K), dtype=float)
        for k in range(K):
            for t in range(T):
                eff = t + int(lag[k])
                if eff >= T:
                    continue
                # tau=eff..T-1
                pw = decay[k] ** np.arange(0, T - eff, dtype=float)  # (T-eff,)
                dz_year_k[eff:, k] += float(base_tk[t, k]) * pw

        delta_raw_full = (dz_year_k @ pi_mat) * std.reshape(1, -1)  # (T,19)
        raw_full = np.asarray(baseline_raw_future, dtype=float) + delta_raw_full
        scores_full = scores_from_raw_mat(raw_full)  # (T,)
        obj = float(np.sum(w_year * scores_full[obj_idxs]))
        return -obj

    # 约束
    constraints = []

    # 总预算等式约束
    constraints.append({"type": "eq", "fun": lambda u: float(np.sum(u) - TOTAL_BUDGET)})

    # 维度 min/max share（线性不等式）
    min_dim = np.array([DIM_BUDGET_MIN_SHARE[d] * TOTAL_BUDGET for d in dims], dtype=float)
    max_dim = np.array([DIM_BUDGET_MAX_SHARE[d] * TOTAL_BUDGET for d in dims], dtype=float)
    for k in range(K):
        constraints.append(
            {"type": "ineq", "fun": (lambda u, k=k: float(np.sum(np.asarray(u).reshape(T, K)[:, k]) - min_dim[k]))}
        )
        constraints.append(
            {"type": "ineq", "fun": (lambda u, k=k: float(max_dim[k] - np.sum(np.asarray(u).reshape(T, K)[:, k])))}
        )

    # 单年上限（若启用）
    if YEAR_BUDGET_CAP is not None:
        cap = float(YEAR_BUDGET_CAP)
        for t in range(T):
            constraints.append(
                {"type": "ineq", "fun": (lambda u, t=t: float(cap - np.sum(np.asarray(u).reshape(T, K)[t, :])))}
            )

    # 变量上下界：u>=0；若对任何目标年份都不可能生效，则强制该变量=0，避免解退化
    bounds = []
    for t, y in enumerate(years):
        for k in range(K):
            if int(y + lag[k]) > max_obj_year:
                bounds.append((0.0, 0.0))
            else:
                bounds.append((0.0, None))

    # 多起点初始化
    rng = np.random.default_rng(int(NLP_SEED))
    best = None
    best_val = np.inf

    # 一个确定性初值：先满足维度占比，再按年份均分
    lower_dim = min_dim
    upper_dim = max_dim
    dim_totals0 = _allocate_with_bounds(TOTAL_BUDGET, lower_dim, upper_dim, rng)
    year_w0 = np.ones(T, dtype=float) / T
    x0 = np.zeros((T, K), dtype=float)
    for k in range(K):
        x0[:, k] = dim_totals0[k] * year_w0
    x0 = x0.reshape(-1)

    x0_list = [x0]
    for _ in range(max(0, int(NLP_MULTI_STARTS) - 1)):
        dim_totals = _allocate_with_bounds(TOTAL_BUDGET, lower_dim, upper_dim, rng)
        x = np.zeros((T, K), dtype=float)
        for k in range(K):
            # 随机把该维度资金分配到 10 年
            w = rng.random(T)
            w = w / (w.sum() + 1e-12)
            x[:, k] = dim_totals[k] * w
        x0_list.append(x.reshape(-1))

    for idx, x_init in enumerate(x0_list, start=1):
        res = minimize(
            objective,
            x_init,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": int(NLP_MAXITER), "ftol": 1e-6, "disp": False},
        )
        val = float(getattr(res, "fun", np.inf))
        if np.isfinite(val) and val < best_val:
            best_val = val
            best = res
        if idx == 1 or idx == len(x0_list) or idx % 2 == 0:
            msg = getattr(res, "message", "")
            print(f"[NLP] 起点 {idx}/{len(x0_list)}：success={bool(getattr(res,'success',False))}，fun={val:.6f}，{msg}")

    if best is None:
        print("[提示] NLP 求解失败，回退为贪心分配。")
        plan_u, _, final_obj = greedy_optimize_plan(
            baseline_raw_future,
            indicator_cols,
            dim_map,
            global_mean,
            global_std,
            dim_inner_weights,
            dim_between_weights,
        )
        return plan_u, base_obj, final_obj

    u_best = np.asarray(best.x, dtype=float).reshape(T, K)
    # 数值收敛后做一次投影式修正（避免极小的负数/求和误差）
    u_best = np.clip(u_best, 0.0, None)
    s = float(u_best.sum())
    if s > 0 and abs(s - TOTAL_BUDGET) / (TOTAL_BUDGET + 1e-12) > 1e-9:
        u_best *= (TOTAL_BUDGET / s)

    plan_u = _vector_to_plan(u_best.reshape(-1), years, dims)

    obj_opt = -float(getattr(best, "fun", np.nan))
    return plan_u, base_obj, obj_opt


def plan_to_dataframe(plan_u: dict[int, dict[str, float]]) -> pd.DataFrame:
    rows = []
    for y, by_dim in sorted(plan_u.items()):
        row = {"Year": y}
        for k, v in by_dim.items():
            row[k] = v
        row["Total"] = sum(by_dim.values())
        rows.append(row)
    df = pd.DataFrame(rows)
    return df


def main():
    indicator_cols = INDICATOR_COLS_19
    dim_map = DIM_MAP_5

    df_history = load_history_19()
    countries = sorted(df_history["Country"].unique().tolist())
    if TARGET_COUNTRY not in countries:
        raise ValueError(f"未在数据中找到国家: {TARGET_COUNTRY}")

    # 历史期全局 Sigmoid 归一化统计量
    global_mean = df_history[indicator_cols].mean().values
    global_std = df_history[indicator_cols].std(ddof=0).values
    df_norm_all = pd.DataFrame(
        sigmoid_normalize(df_history[indicator_cols].values, global_mean, global_std, ALPHA_SIGMOID),
        columns=indicator_cols,
    )

    dim_scores_df, dim_inner_weights, w_dim = compute_dim_scores_and_weights(df_norm_all, dim_map)
    dim_between_weights = w_dim.flatten()  # 5维
    print("维度间熵权 (5维):", dict(zip(list(dim_map.keys()), dim_between_weights.round(4))))

    # =========
    # 2) 基准情景：对所有国家做 ARIMA 预测 2035 得分（用于比较排名）
    # =========
    print("\n正在生成基准情景（ARIMA）2035 得分...")
    baseline_score_2035 = {}
    baseline_raw_future_by_country = {}

    for c in countries:
        cdf = df_history[df_history["Country"] == c].sort_values("Year")
        steps = len(FUTURE_YEARS)
        mat = np.zeros((steps, len(indicator_cols)), dtype=float)
        for j, col in enumerate(indicator_cols):
            mat[:, j] = forecast_arima_series(cdf[col].values.astype(float), steps=steps)
        mat = np.clip(mat, 0, None)
        baseline_raw_future_by_country[c] = mat
        raw_2035 = mat[FUTURE_YEARS.tolist().index(2035), :]
        baseline_score_2035[c] = score_from_raw_19(
            raw_2035, indicator_cols, dim_map, global_mean, global_std, dim_inner_weights, dim_between_weights
        )

    baseline_rank = (
        pd.DataFrame({"Country": list(baseline_score_2035.keys()), "Score_2035": list(baseline_score_2035.values())})
        .sort_values("Score_2035", ascending=False)
        .reset_index(drop=True)
    )
    baseline_rank["Rank_2035"] = baseline_rank.index + 1
    print("\n[基准] 2035 排名：")
    print(baseline_rank[["Rank_2035", "Country", "Score_2035"]].to_string(index=False))

    # =========
    # 3) 优化：分配 1 万亿使中国 2026-2035 多年综合收益最大（加权平均）
    # =========
    print("\n开始优化中国资金分配（目标：最大化 2026-2035 多年综合收益）...")
    cn_baseline_raw_future = baseline_raw_future_by_country[TARGET_COUNTRY]
    if str(SOLVER).lower() == "nlp":
        plan_u, obj_base, obj_opt = optimize_plan_nlp(
            cn_baseline_raw_future,
            indicator_cols,
            dim_map,
            global_mean,
            global_std,
            dim_inner_weights,
            dim_between_weights,
        )
    else:
        plan_u, obj_base, obj_opt = greedy_optimize_plan(
            cn_baseline_raw_future,
            indicator_cols,
            dim_map,
            global_mean,
            global_std,
            dim_inner_weights,
            dim_between_weights,
        )

    print("\n[中国] 2026-2035 多年综合得分（加权平均）基准：", round(obj_base, 4))
    print("[中国] 2026-2035 多年综合得分（加权平均）投资后：", round(obj_opt, 4))
    print("[中国] 多年综合提升：", round(obj_opt - obj_base, 4))

    # 同时报告 2035 单年得分（便于排名/论文展示）
    pi_cn = build_investment_impact_weights(indicator_cols, dim_map, dim_inner_weights)
    idx_2035 = FUTURE_YEARS.tolist().index(2035)
    score_2035_base = score_from_raw_19(
        cn_baseline_raw_future[idx_2035, :],
        indicator_cols,
        dim_map,
        global_mean,
        global_std,
        dim_inner_weights,
        dim_between_weights,
    )
    delta_2035 = delta_raw_from_plan(plan_u, 2035, indicator_cols, global_std, pi_cn)
    score_2035_opt = score_from_raw_19(
        cn_baseline_raw_future[idx_2035, :] + delta_2035,
        indicator_cols,
        dim_map,
        global_mean,
        global_std,
        dim_inner_weights,
        dim_between_weights,
    )
    print("\n[中国] 2035 基准得分：", round(score_2035_base, 4))
    print("[中国] 2035 投资后得分：", round(score_2035_opt, 4))
    print("[中国] 2035 得分提升：", round(score_2035_opt - score_2035_base, 4))

    # =========
    # 4) 计算投资后 2035 排名（其他国家基准不变）
    # =========
    improved_scores = dict(baseline_score_2035)
    improved_scores[TARGET_COUNTRY] = score_2035_opt
    improved_rank = (
        pd.DataFrame({"Country": list(improved_scores.keys()), "Score_2035": list(improved_scores.values())})
        .sort_values("Score_2035", ascending=False)
        .reset_index(drop=True)
    )
    improved_rank["Rank_2035"] = improved_rank.index + 1
    print("\n[投资后] 2035 排名：")
    print(improved_rank[["Rank_2035", "Country", "Score_2035"]].to_string(index=False))

    # =========
    # 5) 输出资金分配表与排名表
    # =========
    df_plan = plan_to_dataframe(plan_u)
    # 便于阅读：转成“亿元”
    to_yi = 1e8
    df_plan_display = df_plan.copy()
    for col in df_plan_display.columns:
        if col != "Year":
            df_plan_display[col] = df_plan_display[col] / to_yi

    out_plan = "problem4_investment_plan_2026_2035.csv"
    out_rank = "problem4_rank_2035_baseline_vs_invest.csv"
    df_plan_display.to_csv(out_plan, index=False, encoding="utf-8-sig")

    merged_rank = baseline_rank[["Country", "Rank_2035", "Score_2035"]].merge(
        improved_rank[["Country", "Rank_2035", "Score_2035"]],
        on="Country",
        suffixes=("_baseline", "_invest"),
    )
    merged_rank["Rank_change"] = merged_rank["Rank_2035_baseline"] - merged_rank["Rank_2035_invest"]
    merged_rank["Score_change"] = merged_rank["Score_2035_invest"] - merged_rank["Score_2035_baseline"]
    merged_rank.to_csv(out_rank, index=False, encoding="utf-8-sig")

    print(f"\n已输出：`{out_plan}`（单位：亿元）")
    print(f"已输出：`{out_rank}`（2035 排名与得分对比）")


if __name__ == "__main__":
    main()

