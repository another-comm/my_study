import warnings

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:
    ARIMA = None


def sigmoid_normalize(arr: np.ndarray, mean: np.ndarray, std: np.ndarray, alpha: float = 2.0) -> np.ndarray:
    """
    Sigmoid 归一化（与问题2/3保持一致）：
    先做 z-score 标准化，再过 sigmoid，将任意尺度映射到 (0,1)。
    """
    arr = np.asarray(arr, dtype=float)
    mean = np.asarray(mean, dtype=float)
    std = np.asarray(std, dtype=float)
    std_safe = np.where(std == 0, 1e-6, std)
    standardized = (arr - mean) / std_safe
    return 1 / (1 + np.exp(-alpha * standardized))


def calculate_entropy_weights(df_norm: pd.DataFrame) -> np.ndarray:
    """熵权法：输入列需为正（0-1更稳健），输出列权重向量（和为1）。"""
    df_norm = df_norm + 1e-9
    p = df_norm / df_norm.sum(axis=0)
    k = 1 / np.log(len(df_norm))
    e = -k * (p * np.log(p)).sum(axis=0)
    d = 1 - e
    weights = d / d.sum()
    return np.array(weights)


def compute_dim_scores_and_weights(df_norm: pd.DataFrame, dim_map: dict) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """
    计算：
    - 维度内熵权（每个维度内的指标权重）
    - 维度得分（每条样本的 5 维得分）
    - 维度间熵权（5 维权重）
    """
    dim_inner = {}
    for dim, cols in dim_map.items():
        dim_inner[dim] = calculate_entropy_weights(df_norm[cols])
    scores = {}
    for dim, cols in dim_map.items():
        scores[dim] = (df_norm[cols].values @ dim_inner[dim])
    scores_df = pd.DataFrame(scores)
    w_dim_ = calculate_entropy_weights(scores_df)
    return scores_df, dim_inner, w_dim_


def _fallback_forecast_linear(y: np.ndarray, steps: int) -> np.ndarray:
    """回退方案：线性趋势外推（小样本下更稳健）。"""
    y = np.asarray(y, dtype=float)
    y = y[~np.isnan(y)]
    n = len(y)
    if n == 0:
        return np.zeros(steps, dtype=float)
    if n == 1 or np.allclose(y, y[-1]):
        return np.full(steps, float(y[-1]), dtype=float)
    x = np.arange(n, dtype=float)
    try:
        a, b = np.polyfit(x, y, deg=1)
        x_f = np.arange(n, n + steps, dtype=float)
        return a * x_f + b
    except Exception:
        return np.full(steps, float(y[-1]), dtype=float)


_arima_warned = False


def forecast_arima_series(y: np.ndarray, steps: int, max_p: int = 2, max_d: int = 1, max_q: int = 2) -> np.ndarray:
    """小网格 AIC 选阶 ARIMA；不可用/失败则回退线性外推。"""
    global _arima_warned
    y = np.asarray(y, dtype=float)
    y = y[~np.isnan(y)]
    if len(y) < 3:
        return _fallback_forecast_linear(y, steps)

    if ARIMA is None:
        if not _arima_warned:
            print("[提示] 未检测到 statsmodels，ARIMA 将回退为线性趋势外推。建议安装：pip install statsmodels")
            _arima_warned = True
        return _fallback_forecast_linear(y, steps)

    best_aic = np.inf
    best_fit = None
    n = len(y)

    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                if n < (p + q + d + 2):
                    continue
                trend = "c" if d == 0 else "n"
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        fit = ARIMA(
                            y,
                            order=(p, d, q),
                            trend=trend,
                            enforce_stationarity=False,
                            enforce_invertibility=False,
                        ).fit()
                    aic = getattr(fit, "aic", np.inf)
                    if np.isfinite(aic) and aic < best_aic:
                        best_aic = aic
                        best_fit = fit
                except Exception:
                    continue

    if best_fit is None:
        return _fallback_forecast_linear(y, steps)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fc = best_fit.forecast(steps=steps)
        fc = np.asarray(fc, dtype=float)
        if fc.shape[0] != steps:
            return _fallback_forecast_linear(y, steps)
        return fc
    except Exception:
        return _fallback_forecast_linear(y, steps)

