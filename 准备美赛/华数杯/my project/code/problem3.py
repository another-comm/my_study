import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ai_common import compute_dim_scores_and_weights, forecast_arima_series, sigmoid_normalize
from ai_data19 import DIM_MAP_5, INDICATOR_COLS_19, load_history_19


def run_prediction(df_history: pd.DataFrame, alpha: float = 2.0) -> pd.DataFrame:
    future_years = np.arange(2026, 2036)
    global_mean = df_history[INDICATOR_COLS_19].mean().values
    global_std = df_history[INDICATOR_COLS_19].std(ddof=0).values
    df_norm_all = pd.DataFrame(
        sigmoid_normalize(df_history[INDICATOR_COLS_19].values, global_mean, global_std, alpha),
        columns=INDICATOR_COLS_19,
    )
    dim_scores_df, dim_inner_weights, w_dim = compute_dim_scores_and_weights(df_norm_all, DIM_MAP_5)
    w_dim_future = w_dim.flatten()

    col_idx = {c: i for i, c in enumerate(INDICATOR_COLS_19)}
    dim_idxs = {dim: [col_idx[c] for c in cols] for dim, cols in DIM_MAP_5.items()}

    countries = sorted(df_history["Country"].unique().tolist())
    rows = []
    for country in countries:
        cdf = df_history[df_history["Country"] == country].sort_values("Year")
        steps = len(future_years)
        mat = np.zeros((steps, len(INDICATOR_COLS_19)), dtype=float)
        for j, col in enumerate(INDICATOR_COLS_19):
            mat[:, j] = forecast_arima_series(cdf[col].values.astype(float), steps=steps)
        mat = np.clip(mat, 0, None)

        for t_idx, yr in enumerate(future_years):
            real_vals = mat[t_idx : t_idx + 1, :]
            norm_vals = sigmoid_normalize(real_vals, global_mean, global_std, alpha)
            dim_scores = []
            for dim, idxs in dim_idxs.items():
                dim_scores.append(float(norm_vals[:, idxs] @ dim_inner_weights[dim]))
            score = float(np.asarray(dim_scores, dtype=float) @ w_dim_future) * 100.0
            rows.append([int(yr), country, score] + real_vals.flatten().tolist())

    return pd.DataFrame(rows, columns=["Year", "Country", "Forecast_Score"] + INDICATOR_COLS_19)


def main():
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    df_history = load_history_19()
    df_future = run_prediction(df_history)

    global_mean = df_history[INDICATOR_COLS_19].mean().values
    global_std = df_history[INDICATOR_COLS_19].std(ddof=0).values
    df_norm_all = pd.DataFrame(
        sigmoid_normalize(df_history[INDICATOR_COLS_19].values, global_mean, global_std, 2.0),
        columns=INDICATOR_COLS_19,
    )
    dim_scores_df, _, w_dim = compute_dim_scores_and_weights(df_norm_all, DIM_MAP_5)
    df_hist_score = pd.DataFrame({"Year": df_history["Year"], "Country": df_history["Country"]})
    df_hist_score["Forecast_Score"] = (dim_scores_df.values @ w_dim.flatten()) * 100.0

    plot_df = pd.concat([df_hist_score, df_future[["Year", "Country", "Forecast_Score"]]], ignore_index=True)
    plt.figure(figsize=(14, 8))
    sns.lineplot(data=plot_df, x="Year", y="Forecast_Score", hue="Country", marker="o", linewidth=2.5)
    plt.axvline(x=2025, color="red", linestyle="--")
    plt.title("Global AI Competitiveness Forecast (2016–2035)", fontsize=16)
    plt.ylabel("Overall Competitiveness Score", fontsize=12)
    plt.xlabel("Year", fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.tight_layout()

    rank_2035 = df_future[df_future["Year"] == 2035].sort_values(by="Forecast_Score", ascending=False).copy()
    rank_2035["Rank"] = range(1, len(rank_2035) + 1)
    print(rank_2035[["Rank", "Country", "Forecast_Score"]].to_string(index=False))
    plt.show()


if __name__ == "__main__":
    main()