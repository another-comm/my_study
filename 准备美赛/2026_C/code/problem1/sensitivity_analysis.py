import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from data_preprocessing import load_processed_excel
from idm_fan_vote_model import DWTSFanVoteEstimator


class SensitivityAnalyzer:
    def __init__(self, df):
        self.df = df

    def grid_search(self, seasons=None, softmax_temps=(0.5, 1.0, 1.5), likelihood_temps=(0.05, 0.1, 0.2), use_mcmc=False):
        if seasons is None:
            seasons = sorted(self.df["season"].unique())
        rows = []
        total = len(softmax_temps) * len(likelihood_temps)
        k = 0
        for s_temp in softmax_temps:
            for l_temp in likelihood_temps:
                k += 1
                print(f"[{k}/{total}] softmax_temp={s_temp}, likelihood_temp={l_temp} ...")
                estimator = DWTSFanVoteEstimator(softmax_temp=float(s_temp), likelihood_temp=float(l_temp))
                results = estimator.estimate_all_seasons(self.df, seasons=seasons, use_mcmc=use_mcmc, verbose=False)
                metrics = estimator.compute_overall_metrics(results)
                rows.append(
                    {
                        "softmax_temp": float(s_temp),
                        "likelihood_temp": float(l_temp),
                        "mean_consistency": float(metrics.get("mean_consistency", np.nan)),
                        "std_consistency": float(metrics.get("std_consistency", np.nan)),
                        "hard_accuracy": float(metrics.get("hard_accuracy", np.nan)),
                        "n_weeks": int(metrics.get("n_weeks_analyzed", 0)),
                    }
                )
        return pd.DataFrame(rows)

    def plot_sensitivity(self, df_grid, metric="mean_consistency", figsize=(6, 4), output_path=None):
        pivot = df_grid.pivot(index="softmax_temp", columns="likelihood_temp", values=metric)
        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(pivot, annot=True, fmt=".3f", cmap="viridis", ax=ax)
        ax.set_xlabel("likelihood_temp")
        ax.set_ylabel("softmax_temp")
        ax.set_title(f"Sensitivity of {metric}")
        plt.tight_layout()
        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches="tight")
        return fig


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def main():
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.dirname(_script_dir)
    data_path = os.path.join(_project_root, "2026_MCM_Problem_C_Data_processed.xlsx")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed Excel not found: {data_path}. Run data_preprocessing first.")

    df = load_processed_excel(data_path)

    analyzer = SensitivityAnalyzer(df)

    softmax_grid = [0.5, 0.8, 1.0, 1.2, 1.5]
    likelihood_grid = [0.05, 0.08, 0.10, 0.15, 0.20]

    # choose 5 representative seasons (adjust if needed)
    candidate_seasons = [1, 2, 11, 27, 28]
    available = sorted(df["season"].unique())
    seasons = [s for s in candidate_seasons if s in available]
    if len(seasons) < 5:
        # pad with other seasons if fewer than 5 of the above exist
        extra = [s for s in available if s not in seasons]
        seasons.extend(extra[: max(0, 5 - len(seasons))])
    print(f"Running sensitivity analysis on seasons: {seasons}")

    df_grid = analyzer.grid_search(seasons=seasons, softmax_temps=softmax_grid, likelihood_temps=likelihood_grid, use_mcmc=False)

    out_dir = ensure_dir(os.path.join(_script_dir, "results"))
    csv_path = os.path.join(out_dir, "sensitivity_grid.csv")
    df_grid.to_csv(csv_path, index=False, encoding="utf-8-sig")

    analyzer.plot_sensitivity(
        df_grid,
        metric="mean_consistency",
        output_path=os.path.join(out_dir, "sensitivity_mean_consistency.png"),
    )
    analyzer.plot_sensitivity(
        df_grid,
        metric="hard_accuracy",
        output_path=os.path.join(out_dir, "sensitivity_hard_accuracy.png"),
    )

    print("Sensitivity analysis finished.")
    print(f"Grid results saved to: {csv_path}")
    print(f"Heatmaps saved to: {out_dir}/sensitivity_*.png")


if __name__ == "__main__":
    main()

