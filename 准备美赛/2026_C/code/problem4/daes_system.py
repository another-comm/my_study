"""
Problem 4 – Model III (DAES): Dual-Axis Equilibrium System

Goal:
Propose and offline-test an alternative weekly elimination system that combines
judge scores and fan votes in a way that is more fair and still exciting.

Inputs (from Model I output):
- problem1/results/vote_estimates.json
  (weekly contestants, judge_scores, votes_map, actual eliminated)

Inputs (from processed dataset):
- project_root/2026_MCM_Problem_C_Data_processed.xlsx  (sheet: 数据)
  (celebrity age, industry, ballroom_partner)

Outputs:
- problem4/results/daes_offline_test.xlsx
- problem4/results/fig_age_fairness.png
- problem4/results/fig_mentor_fairness.png
- problem4/results/fig_stage_contribution.png
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    mu = np.nanmean(x)
    sd = np.nanstd(x)
    if not np.isfinite(sd) or sd <= 1e-12:
        return np.zeros_like(x, dtype=float)
    return (x - mu) / sd


def softcap_votes(v: np.ndarray, gamma: float) -> np.ndarray:
    """Power transform for vote shares; gamma in (0,1] reduces head dominance."""
    v = np.asarray(v, dtype=float)
    v = np.clip(v, 1e-12, None)
    t = np.power(v, float(gamma))
    s = float(np.sum(t))
    return (t / s) if s > 0 else np.ones_like(t) / len(t)


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


# -----------------------------------------------------------------------------
# DAES parameters
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class DAESParams:
    gamma_votes: float = 0.70          # soft-capping fan votes (0<gamma<=1)
    lambda_age: float = 0.6932         # age bias compensation (from Model II)
    icc_mentor: float = 0.1146         # mentor contribution rate (ICC)
    alpha_min: float = 0.40            # judge weight early
    alpha_mid: float = 0.50            # judge weight mid
    alpha_max: float = 0.60            # judge weight late
    stage1_weeks: int = 4              # W1-W4
    stage2_weeks: int = 8              # W5-W8


def stage_weights(week: int, p: DAESParams) -> Tuple[float, float]:
    """Return (W_J, W_F) for the given week number (1-based)."""
    if week <= p.stage1_weeks:
        wj = p.alpha_min
    elif week <= p.stage2_weeks:
        wj = p.alpha_mid
    else:
        wj = p.alpha_max
    wf = 1.0 - wj
    return float(wj), float(wf)


# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------

def load_vote_estimates(vote_json_path: str) -> dict:
    with open(vote_json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_processed_base_table(processed_excel_path: str) -> pd.DataFrame:
    # processed excel in this project uses sheet name '数据'
    df = pd.read_excel(processed_excel_path, sheet_name="数据", engine="openpyxl")
    # normalize types
    df["season"] = pd.to_numeric(df["season"], errors="coerce").fillna(0).astype(int)
    # keep only needed columns if present
    cols = [
        "celebrity_name",
        "season",
        "celebrity_age_during_season",
        "celebrity_industry",
        "ballroom_partner",
    ]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].copy()
    df["celebrity_age_during_season"] = pd.to_numeric(
        df.get("celebrity_age_during_season", np.nan), errors="coerce"
    )
    return df


def build_covariate_maps(base_df: pd.DataFrame) -> Tuple[Dict[Tuple[str, int], float], Dict[Tuple[str, int], str]]:
    """
    Return:
    - age_std_map[(name,season)] -> float (global standardized age)
    - pro_map[(name,season)] -> pro dancer string (ballroom_partner)
    """
    d = base_df.drop_duplicates(subset=["celebrity_name", "season"]).copy()
    ages = d["celebrity_age_during_season"].astype(float)
    mu, sd = float(np.nanmean(ages)), float(np.nanstd(ages))
    if not np.isfinite(sd) or sd <= 1e-12:
        sd = 1.0
    d["age_std"] = (ages - mu) / sd

    age_std_map = {(r["celebrity_name"], int(r["season"])): float(r["age_std"]) for _, r in d.iterrows()}
    pro_map = {(r["celebrity_name"], int(r["season"])): str(r.get("ballroom_partner", "")) for _, r in d.iterrows()}
    return age_std_map, pro_map


# -----------------------------------------------------------------------------
# Mentor value-added (MVA) proxy
# -----------------------------------------------------------------------------

def estimate_pro_strength(vote_estimates: dict, pro_map: Dict[Tuple[str, int], str]) -> Dict[str, float]:
    """
    Estimate a pro dancer strength proxy using historical weekly judge z-scores.
    For each week: compute zscore across contestants; accumulate by pro dancer.
    Return normalized alpha_pro in [0,1] for each pro dancer.
    """
    pro_scores: Dict[str, List[float]] = {}
    for season_key, season_data in vote_estimates.items():
        if not isinstance(season_data, dict) or "weeks" not in season_data:
            continue
        season = int(season_data.get("season", int(season_key)))
        for week_key, week_data in (season_data.get("weeks") or {}).items():
            contestants = week_data.get("contestants", [])
            judge_scores = week_data.get("judge_scores", [])
            if not contestants or len(contestants) != len(judge_scores):
                continue
            zj = zscore(np.asarray(judge_scores, dtype=float))
            for name, zval in zip(contestants, zj):
                pro = pro_map.get((name, season), "")
                if not pro:
                    continue
                pro_scores.setdefault(pro, []).append(float(zval))

    # average and min-max normalize
    pro_mean = {pro: float(np.mean(vals)) for pro, vals in pro_scores.items() if len(vals) > 0}
    if not pro_mean:
        return {}
    vals = np.array(list(pro_mean.values()), dtype=float)
    vmin, vmax = float(np.min(vals)), float(np.max(vals))
    if not np.isfinite(vmax - vmin) or (vmax - vmin) <= 1e-12:
        return {pro: 0.5 for pro in pro_mean}
    return {pro: float((m - vmin) / (vmax - vmin)) for pro, m in pro_mean.items()}


# -----------------------------------------------------------------------------
# Baselines (for support / comparison)
# -----------------------------------------------------------------------------

def _rank_desc(values: np.ndarray) -> np.ndarray:
    """Higher value gets better (smaller) rank; ties -> average rank."""
    arr = np.asarray(values, dtype=float)
    order = np.argsort(-arr)
    n = len(arr)
    ranks = np.empty(n, dtype=float)
    i = 0
    while i < n:
        j = i
        while j < n and arr[order[j]] == arr[order[i]]:
            j += 1
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = avg
        i = j
    return ranks


def eliminated_rank_method(contestants: List[str], judge_scores: List[float], votes_map: List[float]) -> str:
    js = np.asarray(judge_scores, dtype=float)
    vm = np.asarray(votes_map, dtype=float)
    sum_r = _rank_desc(js) + _rank_desc(vm)
    idx = int(np.where(sum_r == np.max(sum_r))[0][0])
    return str(contestants[idx])


def eliminated_percent_method(contestants: List[str], judge_scores: List[float], votes_map: List[float]) -> str:
    js = np.asarray(judge_scores, dtype=float)
    vm = np.asarray(votes_map, dtype=float)
    total = float(np.sum(js))
    judge_pct = (js / total) if total > 0 else np.ones_like(js) / len(js)
    combined = judge_pct + vm
    idx = int(np.where(combined == np.min(combined))[0][0])
    return str(contestants[idx])


# -----------------------------------------------------------------------------
# DAES core
# -----------------------------------------------------------------------------

def eliminated_daes(
    season: int,
    week: int,
    contestants: List[str],
    judge_scores: List[float],
    votes_map: List[float],
    age_std_map: Dict[Tuple[str, int], float],
    pro_map: Dict[Tuple[str, int], str],
    pro_alpha: Dict[str, float],
    p: DAESParams,
) -> Tuple[str, Dict[str, float]]:
    """
    Return:
    - eliminated name (lowest DAES score)
    - per-contestant DAES score map (for diagnostics)
    """
    js = np.asarray(judge_scores, dtype=float)
    vm = np.asarray(votes_map, dtype=float)

    zj = zscore(js)
    v_soft = softcap_votes(vm, gamma=p.gamma_votes)
    zv = zscore(v_soft)

    # Judge adjustments: age compensation + mentor value-added shrink
    age_std = np.array([float(age_std_map.get((n, season), 0.0)) for n in contestants], dtype=float)
    pro_names = [pro_map.get((n, season), "") for n in contestants]
    a_pro = np.array([float(pro_alpha.get(pro, 0.5)) if pro else 0.5 for pro in pro_names], dtype=float)

    zj_adj = zj + p.lambda_age * age_std
    zj_final = zj_adj * (1.0 - p.icc_mentor * a_pro)

    wj, wf = stage_weights(week, p)
    s = wj * zj_final + wf * zv

    idx = int(np.where(s == np.min(s))[0][0])
    eliminated = str(contestants[idx])
    score_map = {str(n): float(v) for n, v in zip(contestants, s)}
    return eliminated, score_map


# -----------------------------------------------------------------------------
# Offline evaluation + figures
# -----------------------------------------------------------------------------

def offline_test(
    vote_estimates: dict,
    age_std_map: Dict[Tuple[str, int], float],
    pro_map: Dict[Tuple[str, int], str],
    p: DAESParams,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns:
    - df_weekly: per week results for DAES and baselines (one row per week)
    - df_season: per season aggregated metrics (one row per season)
    - df_cw: contestant-week table for fairness analysis (one row per contestant-week)
    """
    pro_alpha = estimate_pro_strength(vote_estimates, pro_map)

    rows = []
    cw_rows = []
    for season_key, season_data in vote_estimates.items():
        if not isinstance(season_data, dict) or "weeks" not in season_data:
            continue
        season = int(season_data.get("season", int(season_key)))
        for week_key, week_data in (season_data.get("weeks") or {}).items():
            week = int(week_key)
            contestants = week_data.get("contestants", [])
            judge_scores = week_data.get("judge_scores", [])
            votes_map = week_data.get("votes_map", [])
            actual = (week_data.get("eliminated") or [""])[0]
            if not contestants or len(contestants) != len(judge_scores) or len(contestants) != len(votes_map):
                continue

            pred_rank = eliminated_rank_method(contestants, judge_scores, votes_map)
            pred_percent = eliminated_percent_method(contestants, judge_scores, votes_map)
            pred_daes, _score_map = eliminated_daes(
                season, week, contestants, judge_scores, votes_map,
                age_std_map, pro_map, pro_alpha, p
            )

            # contestant-week table for fairness analysis
            zj = zscore(np.asarray(judge_scores, dtype=float))
            zv = zscore(softcap_votes(np.asarray(votes_map, dtype=float), gamma=p.gamma_votes))
            for name, jz, vz in zip(contestants, zj, zv):
                pro = pro_map.get((name, season), "")
                cw_rows.append({
                    "season": int(season),
                    "week": int(week),
                    "contestant": str(name),
                    "age_std": float(age_std_map.get((name, season), 0.0)),
                    "pro_name": str(pro),
                    "pro_alpha": float(pro_alpha.get(pro, 0.5)) if pro else 0.5,
                    "judge_z": float(jz),
                    "fan_z": float(vz),
                    "elim_rank": 1 if str(name) == pred_rank else 0,
                    "elim_percent": 1 if str(name) == pred_percent else 0,
                    "elim_daes": 1 if str(name) == pred_daes else 0,
                })

            rows.append({
                "season": season,
                "week": week,
                "n_contestants": len(contestants),
                "actual_eliminated": str(actual),
                "pred_rank": pred_rank,
                "pred_percent": pred_percent,
                "pred_daes": pred_daes,
                "rank_match": (pred_rank == actual) if actual else None,
                "percent_match": (pred_percent == actual) if actual else None,
                "daes_match": (pred_daes == actual) if actual else None,
                "W_J": stage_weights(week, p)[0],
                "W_F": stage_weights(week, p)[1],
            })

    df_weekly = pd.DataFrame(rows)
    df_cw = pd.DataFrame(cw_rows)
    if df_weekly.empty:
        return df_weekly, pd.DataFrame(), df_cw

    seasons = sorted(df_weekly["season"].unique())
    season_rows = []
    for s in seasons:
        sub = df_weekly[df_weekly["season"] == s]
        total = len(sub)
        season_rows.append({
            "season": int(s),
            "weeks": int(total),
            "acc_rank": float(np.mean(sub["rank_match"])) if total else np.nan,
            "acc_percent": float(np.mean(sub["percent_match"])) if total else np.nan,
            "acc_daes": float(np.mean(sub["daes_match"])) if total else np.nan,
        })

    df_season = pd.DataFrame(season_rows)
    return df_weekly, df_season, df_cw


def _slope(x: np.ndarray, y: np.ndarray) -> float:
    """Simple OLS slope with intercept: y = a + b x."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if len(x) < 5:
        return float("nan")
    vx = float(np.var(x))
    if not np.isfinite(vx) or vx <= 1e-12:
        return float("nan")
    return float(np.cov(x, y, ddof=0)[0, 1] / vx)


def compute_fairness_metrics(df_cw: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Fairness metrics aligned with DAES goals:
    - age sensitivity: slope of elimination probability vs age_std
    - mentor sensitivity: slope of elimination probability vs pro_alpha
    Smaller absolute slopes => less structural dependence (more fair).
    """
    out: Dict[str, Dict[str, float]] = {}
    for method, col in [("Rank", "elim_rank"), ("Percent", "elim_percent"), ("DAES", "elim_daes")]:
        out[method] = {
            "slope_age": _slope(df_cw["age_std"].values, df_cw[col].values),
            "slope_pro": _slope(df_cw["pro_alpha"].values, df_cw[col].values),
        }
    return out


def make_figures(
    df_weekly: pd.DataFrame,
    df_season: pd.DataFrame,
    df_cw: pd.DataFrame,
    out_dir: str,
    p: DAESParams,
) -> None:
    ensure_dir(out_dir)

    # -------------------------------------------------------------------------
    # Figure 1: Age fairness – elimination rate by age quartile
    # -------------------------------------------------------------------------
    df = df_cw.copy()
    # quartiles based on whole dataset
    df["age_q"] = pd.qcut(df["age_std"], 4, labels=["Q1 (youngest)", "Q2", "Q3", "Q4 (oldest)"])
    age_grp = df.groupby("age_q", observed=True)[["elim_rank", "elim_percent", "elim_daes"]].mean()
    fig1, ax1 = plt.subplots(figsize=(8.8, 4.8))
    x = np.arange(len(age_grp.index))
    ax1.plot(x, 100 * age_grp["elim_rank"].values, marker="o", linewidth=1.8, label="Rank method")
    ax1.plot(x, 100 * age_grp["elim_percent"].values, marker="s", linewidth=1.8, label="Percent method")
    ax1.plot(x, 100 * age_grp["elim_daes"].values, marker="^", linewidth=2.2, label="DAES (proposed)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(age_grp.index.tolist())
    ax1.set_ylabel("Elimination Rate (%)")
    ax1.set_title("Age Fairness: Elimination Rate by Age Quartile")
    ax1.grid(alpha=0.3)
    ax1.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    fig1.savefig(os.path.join(out_dir, "fig_age_fairness.png"), dpi=150, bbox_inches="tight")
    plt.close(fig1)

    # -------------------------------------------------------------------------
    # Figure 2: Mentor fairness – elimination rate by mentor-strength quartile
    # -------------------------------------------------------------------------
    df["pro_q"] = pd.qcut(df["pro_alpha"], 4, labels=["Q1 (weakest)", "Q2", "Q3", "Q4 (strongest)"])
    pro_grp = df.groupby("pro_q", observed=True)[["elim_rank", "elim_percent", "elim_daes"]].mean()
    fig2, ax2 = plt.subplots(figsize=(8.8, 4.8))
    x2 = np.arange(len(pro_grp.index))
    ax2.plot(x2, 100 * pro_grp["elim_rank"].values, marker="o", linewidth=1.8, label="Rank method")
    ax2.plot(x2, 100 * pro_grp["elim_percent"].values, marker="s", linewidth=1.8, label="Percent method")
    ax2.plot(x2, 100 * pro_grp["elim_daes"].values, marker="^", linewidth=2.2, label="DAES (proposed)")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(pro_grp.index.tolist())
    ax2.set_ylabel("Elimination Rate (%)")
    ax2.set_title("Mentor Fairness: Elimination Rate by Mentor Strength Quartile")
    ax2.grid(alpha=0.3)
    ax2.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    fig2.savefig(os.path.join(out_dir, "fig_mentor_fairness.png"), dpi=150, bbox_inches="tight")
    plt.close(fig2)

    # -------------------------------------------------------------------------
    # Figure 3: Dynamic weights (design module)
    # -------------------------------------------------------------------------
    fig3, ax3 = plt.subplots(figsize=(8.5, 4.8))
    stages = ["Weeks 1–4", "Weeks 5–8", "Weeks 9+"]  # English
    wj = [float(p.alpha_min), float(p.alpha_mid), float(p.alpha_max)]
    wf = [1.0 - wj[0], 1.0 - wj[1], 1.0 - wj[2]]
    x3 = np.arange(len(stages))
    w = 0.35
    ax3.bar(x3 - w / 2, wf, w, label="Fan weight", color="coral", alpha=0.85)
    ax3.bar(x3 + w / 2, wj, w, label="Judge weight", color="steelblue", alpha=0.85)
    ax3.set_xticks(x3)
    ax3.set_xticklabels(stages)
    ax3.set_ylim(0, 0.8)
    ax3.set_ylabel("Weight")
    ax3.set_title("DAES Dynamic Weight Schedule (Fan vs Judge)")
    ax3.grid(axis="y", alpha=0.3)
    ax3.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    fig3.savefig(os.path.join(out_dir, "fig_stage_contribution.png"), dpi=150, bbox_inches="tight")
    plt.close(fig3)


def save_excel(df_weekly: pd.DataFrame, df_season: pd.DataFrame, df_cw: pd.DataFrame, out_path: str, p: DAESParams) -> None:
    ensure_dir(os.path.dirname(out_path))
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_weekly.to_excel(writer, sheet_name="Weekly", index=False)
        df_season.to_excel(writer, sheet_name="Season_Summary", index=False)
        df_cw.to_excel(writer, sheet_name="Contestant_Week", index=False)
        # parameters sheet
        params_df = pd.DataFrame([p.__dict__])
        params_df.to_excel(writer, sheet_name="DAES_Params", index=False)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_vote = os.path.join(project_root, "problem1", "results", "vote_estimates.json")
    default_excel = os.path.join(project_root, "2026_MCM_Problem_C_Data_processed.xlsx")
    default_out_dir = os.path.join(script_dir, "results")
    parser = argparse.ArgumentParser(description="DAES (Model III) offline test")
    parser.add_argument("--vote-json", type=str, default=default_vote, help="Path to vote_estimates.json")
    parser.add_argument("--processed-excel", type=str, default=default_excel, help="Path to processed Excel")
    parser.add_argument("--out-dir", type=str, default=default_out_dir, help="Output directory")
    parser.add_argument("--gamma", type=float, default=DAESParams.gamma_votes, help="Vote softcap gamma in (0,1]")
    parser.add_argument("--lambda-age", type=float, default=DAESParams.lambda_age, help="Age compensation coefficient")
    parser.add_argument("--icc", type=float, default=DAESParams.icc_mentor, help="Mentor ICC weight")
    parser.add_argument("--wj-early", type=float, default=DAESParams.alpha_min, help="Judge weight weeks 1-4")
    parser.add_argument("--wj-mid", type=float, default=DAESParams.alpha_mid, help="Judge weight weeks 5-8")
    parser.add_argument("--wj-late", type=float, default=DAESParams.alpha_max, help="Judge weight weeks 9+")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = ensure_dir(args.out_dir)
    p = DAESParams(
        gamma_votes=float(args.gamma),
        lambda_age=float(args.lambda_age),
        icc_mentor=float(args.icc),
        alpha_min=float(args.wj_early),
        alpha_mid=float(args.wj_mid),
        alpha_max=float(args.wj_late),
    )

    if not os.path.exists(args.vote_json):
        raise FileNotFoundError(f"vote_estimates.json not found: {args.vote_json}")
    if not os.path.exists(args.processed_excel):
        raise FileNotFoundError(f"processed excel not found: {args.processed_excel}")

    print("Loading inputs...")
    vote_estimates = load_vote_estimates(args.vote_json)
    base_df = load_processed_base_table(args.processed_excel)
    age_std_map, pro_map = build_covariate_maps(base_df)

    print("Running offline test for DAES and baselines...")
    df_weekly, df_season, df_cw = offline_test(vote_estimates, age_std_map, pro_map, p)
    if df_weekly.empty:
        print("No valid weekly records found. Please check input files.")
        return

    # headline metrics (accuracy is still reported, but not the main fairness objective)
    overall = {
        "Rank": float(np.mean(df_weekly["rank_match"])),
        "Percent": float(np.mean(df_weekly["percent_match"])),
        "DAES": float(np.mean(df_weekly["daes_match"])),
    }
    print("Overall accuracy vs actual elimination:")
    for k, v in overall.items():
        print(f"  {k:7s}: {v*100:.2f}%")

    fairness = compute_fairness_metrics(df_cw)
    print("Fairness metrics (smaller absolute slopes => less structural dependence):")
    for m in ["Rank", "Percent", "DAES"]:
        sa = fairness[m]["slope_age"]
        sp = fairness[m]["slope_pro"]
        print(f"  {m:7s}: slope_age={sa:+.5f}, slope_pro={sp:+.5f}")

    out_xlsx = os.path.join(out_dir, "daes_offline_test.xlsx")
    save_excel(df_weekly, df_season, df_cw, out_xlsx, p)
    print(f"Saved Excel: {out_xlsx}")

    make_figures(df_weekly, df_season, df_cw, out_dir, p)
    print(f"Saved figures to: {out_dir}")


if __name__ == "__main__":
    main()

