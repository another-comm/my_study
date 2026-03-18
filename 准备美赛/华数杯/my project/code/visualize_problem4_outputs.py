import pandas as pd
import matplotlib.pyplot as plt


PLAN_CSV = "problem4_investment_plan_2026_2035.csv"
RANK_CSV = "problem4_rank_2035_baseline_vs_invest.csv"


def plot_investment_plan(plan_path: str) -> None:
    df = pd.read_csv(plan_path)

    years = df["Year"].astype(int)
    dims = ["Talent", "Research", "Infrastructure", "Economy", "Policy"]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.stackplot(
        years,
        *(df[d].values for d in dims),
        labels=dims,
        alpha=0.9,
    )
    ax.set_title("Investment Plan (2026–2035) by Dimension")
    ax.set_xlabel("Year")
    ax.set_ylabel("Budget (100M CNY)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", ncol=3, frameon=True)
    fig.tight_layout()
    fig.savefig("problem4_investment_plan.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_rank_and_score_changes(rank_path: str) -> None:
    df = pd.read_csv(rank_path)

    # 1) Score change bar chart
    df1 = df.sort_values("Score_change", ascending=False).copy()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df1["Country"], df1["Score_change"], color="steelblue", alpha=0.85)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("2035 Score Change After Investment")
    ax.set_xlabel("Country")
    ax.set_ylabel("Score Change")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig("problem4_score_change_2035.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # 2) Rank change bar chart (positive means improved rank)
    df2 = df.sort_values("Rank_change", ascending=False).copy()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df2["Country"], df2["Rank_change"], color="darkorange", alpha=0.85)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("2035 Rank Change After Investment (Positive = Better)")
    ax.set_xlabel("Country")
    ax.set_ylabel("Rank Change")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig("problem4_rank_change_2035.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # 3) Baseline vs invest score scatter (with y=x reference)
    fig, ax = plt.subplots(figsize=(7, 7))
    x = df["Score_2035_baseline"].values
    y = df["Score_2035_invest"].values
    ax.scatter(x, y, s=50, color="seagreen", alpha=0.85)
    for _, r in df.iterrows():
        ax.text(r["Score_2035_baseline"], r["Score_2035_invest"], str(r["Country"]), fontsize=9, alpha=0.9)
    lo = min(x.min(), y.min())
    hi = max(x.max(), y.max())
    pad = (hi - lo) * 0.05 if hi > lo else 1.0
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], linestyle="--", color="gray", linewidth=1)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("2035 Score: Baseline vs After Investment")
    ax.set_xlabel("Baseline Score (2035)")
    ax.set_ylabel("Score After Investment (2035)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("problem4_score_baseline_vs_invest_2035.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    # Use a common font fallback for English plots
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    plot_investment_plan(PLAN_CSV)
    plot_rank_and_score_changes(RANK_CSV)
    print("Saved figures:")
    print("- problem4_investment_plan.png")
    print("- problem4_score_change_2035.png")
    print("- problem4_rank_change_2035.png")
    print("- problem4_score_baseline_vs_invest_2035.png")


if __name__ == "__main__":
    main()

