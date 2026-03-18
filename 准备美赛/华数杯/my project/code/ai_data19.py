import numpy as np
import pandas as pd


DATA_CSV_PATH = r"C:\study\准备美赛\华数杯\my project\data\AI_19_Indicators_2016_2025_Full.csv"

RENAME_MAP_19 = {
    "Top_Scholars": "Top_Scholars",
    "Total_Prof": "Total_Prof",
    "STEM_Scale": "STEM_Grads",
    "STEM_Intensity": "STEM_Intensity",
    "Migration_Idx": "Migration_Idx",
    "Skill_Pen": "Skill_Pen",
    "Papers": "Papers",
    "FWCI": "FWCI",
    "Patents": "Patents",
    "Compute_E": "Compute_EFLOPS",
    "Power_MW": "Power_MW",
    "GPU_Stock": "GPU_Stock",
    "5G_Cover": "5G_Cover",
    "Investment": "Investment",
    "Unicorns": "Unicorns",
    "GDP_Contrib": "GDP_Contrib",
    "Adoption": "Adoption",
    "Policy": "Policy_Score",
    "Data_Open": "Data_Score",
}

INDICATOR_COLS_19 = list(RENAME_MAP_19.values())

DIM_MAP_5 = {
    "Talent": ["Top_Scholars", "Total_Prof", "STEM_Grads", "STEM_Intensity", "Migration_Idx", "Skill_Pen"],
    "Research": ["Papers", "FWCI", "Patents"],
    "Infrastructure": ["Compute_EFLOPS", "Power_MW", "GPU_Stock", "5G_Cover"],
    "Economy": ["Investment", "Unicorns", "GDP_Contrib", "Adoption"],
    "Policy": ["Policy_Score", "Data_Score"],
}

POPULATION = {
    "USA": 342.3,
    "China": 1408.2,
    "India": 1445.5,
    "Japan": 122.8,
    "Germany": 83.2,
    "UK": 68.2,
    "France": 65.5,
    "South Korea": 51.5,
    "Canada": 39.8,
    "UAE": 10.3,
}


def load_history_19(csv_path: str = DATA_CSV_PATH) -> pd.DataFrame:
    raw_df = pd.read_csv(csv_path)
    raw_df[["Year", "Country"]] = raw_df["年份_国家"].str.split("_", expand=True)
    raw_df["Year"] = pd.to_numeric(raw_df["Year"], errors="coerce")
    raw_df["Country"] = raw_df["Country"].astype(str)
    raw_df = raw_df.rename(columns=RENAME_MAP_19)

    missing = [c for c in INDICATOR_COLS_19 if c not in raw_df.columns]
    if missing:
        raise ValueError(f"CSV缺少必要列: {missing}")

    df = raw_df[["Year", "Country"] + INDICATOR_COLS_19].copy()

    pop = df["Country"].map(POPULATION)
    if pop.isnull().any():
        miss = df.loc[pop.isnull(), "Country"].unique()
        raise ValueError(f"缺少人口数据: {miss}")

    for col in ["Top_Scholars", "Total_Prof", "STEM_Grads"]:
        total_by_year = df.groupby("Year")[col].transform("sum")
        df[col] = 0.3 * (df[col] / total_by_year) + 0.7 * (df[col] / pop)

    return df.dropna().sort_values(["Country", "Year"]).reset_index(drop=True)

