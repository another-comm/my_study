"""
Problem 3 – Sensitivity analysis for the LME impact model.

Goal:
Explore how key conclusions (age effect, mentor ICC) change under
different reasonable data-processing choices:
- Age standardization: global vs per-season
- Industry fixed effects: with 5 clusters vs no industry term

Outputs:
- problem3/results/lme_sensitivity.csv
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict

import numpy as np
import pandas as pd

from lme_impact_analysis import (
    load_base_data,
    compute_mean_judge_score,
    load_fan_vote_summary,
    merge_base_and_vote,
    clean_and_prepare,
    compute_icc,
)
from statsmodels.formula.api import mixedlm


@dataclass(frozen=True)
class SensitivityConfig:
    id: str
    age_mode: str          # 'global' or 'by_season'
    industry_mode: str     # 'full' or 'none'


CONFIGS: List[SensitivityConfig] = [
    SensitivityConfig(id="global_full", age_mode="global", industry_mode="full"),
    SensitivityConfig(id="season_full", age_mode="by_season", industry_mode="full"),
    SensitivityConfig(id="global_noind", age_mode="global", industry_mode="none"),
    SensitivityConfig(id="season_noind", age_mode="by_season", industry_mode="none"),
]


def recompute_age_std(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    df = df.copy()
    if mode == "global":
        # already computed in clean_and_prepare
        return df
    if mode == "by_season":
        def _std(group: pd.DataFrame) -> pd.Series:
            mu = group["age"].mean()
            sd = group["age"].std()
            if not sd or sd <= 0:
                return pd.Series(0.0, index=group.index)
            return (group["age"] - mu) / sd

        df["age_std"] = (
            df.groupby("season", group_keys=False).apply(_std).astype(float)
        )
        return df
    raise ValueError(f"Unknown age_mode={mode}")


def fit_lme(df: pd.DataFrame, dep: str, cfg: SensitivityConfig):
    if cfg.industry_mode == "full":
        formula = f"{dep} ~ age_std + C(industry_cluster)"
    else:
        formula = f"{dep} ~ age_std"
    model = mixedlm(formula, data=df, groups=df["ballroom_partner"])
    return model.fit(reml=True)


def run_sensitivity(project_root: str) -> pd.DataFrame:
    problem1_results = os.path.join(project_root, "problem1", "results")

    base_df = load_base_data(project_root)
    mean_judge_df = compute_mean_judge_score(base_df)
    fan_vote_df = load_fan_vote_summary(problem1_results)
    df = merge_base_and_vote(base_df, mean_judge_df, fan_vote_df)
    df = clean_and_prepare(df)

    rows: List[Dict[str, float]] = []
    for cfg in CONFIGS:
        df_cfg = recompute_age_std(df, cfg.age_mode)

        # judge model
        res_j = fit_lme(df_cfg, "mean_judge_score", cfg)
        icc_j, var_u_j, scale_j = compute_icc(res_j)
        age_coef_j = float(res_j.params.get("age_std", np.nan))

        # fan model
        res_f = fit_lme(df_cfg, "mean_fan_vote_share", cfg)
        icc_f, var_u_f, scale_f = compute_icc(res_f)
        age_coef_f = float(res_f.params.get("age_std", np.nan))

        rows.append(
            {
                "config_id": cfg.id,
                "age_mode": cfg.age_mode,
                "industry_mode": cfg.industry_mode,
                "icc_judge": icc_j,
                "icc_fan": icc_f,
                "age_coef_judge": age_coef_j,
                "age_coef_fan": age_coef_f,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    print("Running LME sensitivity analysis for Problem 3...")
    df_sens = run_sensitivity(project_root)
    out_csv = os.path.join(results_dir, "lme_sensitivity.csv")
    df_sens.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("Sensitivity grid saved to:", out_csv)
    print(df_sens)


if __name__ == "__main__":
    main()

