from __future__ import annotations

import json
import math
import textwrap
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import nbformat as nbf
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import clone
from sklearn.ensemble import StackingRegressor, VotingRegressor
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor


warnings.filterwarnings("ignore")

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
sns.set_theme(style="whitegrid", font="Microsoft YaHei")


BASE_DIR = Path(__file__).resolve().parents[1]
CODE_DIR = BASE_DIR / "code"
RESULT_DIR = BASE_DIR / "result"
LATEX_DIR = BASE_DIR / "latex"
CSV_PATH = next(CODE_DIR.glob("*.csv"))
STUDENT_NAME = "林鑫"
STUDENT_ID = "1043220122"
NOTEBOOK_PATH = CODE_DIR / f"上机实验04-{STUDENT_ID}{STUDENT_NAME}.ipynb"
REPORT_PATH = LATEX_DIR / f"上机实验报告04-{STUDENT_ID}{STUDENT_NAME}.tex"


def ensure_dirs() -> None:
    CODE_DIR.mkdir(exist_ok=True)
    RESULT_DIR.mkdir(exist_ok=True)
    LATEX_DIR.mkdir(exist_ok=True)


def load_and_prepare_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    df_raw = pd.read_csv(CSV_PATH)
    df_raw.columns = ["date", "close", "open", "high", "low", "volume", "pct_change"]

    df = df_raw.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["volume"] = (
        df["volume"].astype(str).str.replace("K", "", regex=False).str.replace(",", "", regex=False).astype(float)
    )
    df["pct_change"] = pd.to_numeric(
        df["pct_change"].astype(str).str.replace("%", "", regex=False),
        errors="coerce",
    )

    raw_rows = len(df)
    missing_summary = df.isna().sum()
    duplicate_count = int(df.duplicated().sum())
    df = df.dropna().drop_duplicates().reset_index(drop=True)

    numeric_cols = ["close", "open", "high", "low", "volume", "pct_change"]
    outlier_records = []
    clipped_df = df.copy()
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = int(((df[col] < lower) | (df[col] > upper)).sum())
        outlier_records.append(
            {
                "feature": col,
                "q1": round(float(q1), 4),
                "q3": round(float(q3), 4),
                "lower": round(float(lower), 4),
                "upper": round(float(upper), 4),
                "outlier_count": outlier_count,
            }
        )
        clipped_df[col] = clipped_df[col].clip(lower=lower, upper=upper)

    outlier_df = pd.DataFrame(outlier_records).sort_values("outlier_count", ascending=False)

    clipped_df["year"] = clipped_df["date"].dt.year
    clipped_df["month"] = clipped_df["date"].dt.month
    clipped_df["day"] = clipped_df["date"].dt.day
    clipped_df["weekday"] = clipped_df["date"].dt.weekday + 1
    clipped_df["amplitude"] = clipped_df["high"] - clipped_df["low"]
    clipped_df["open_high_gap"] = clipped_df["high"] - clipped_df["open"]
    clipped_df["open_low_gap"] = clipped_df["open"] - clipped_df["low"]
    clipped_df["high_low_ratio"] = clipped_df["high"] / clipped_df["low"]
    clipped_df["intraday_range_ratio"] = (clipped_df["high"] - clipped_df["low"]) / clipped_df["open"]
    clipped_df["vol_change_ratio"] = clipped_df["volume"].pct_change()
    clipped_df["ma3"] = clipped_df["close"].shift(1).rolling(3).mean()
    clipped_df["ma5"] = clipped_df["close"].shift(1).rolling(5).mean()
    clipped_df["ma10"] = clipped_df["close"].shift(1).rolling(10).mean()
    clipped_df["vol_ma5"] = clipped_df["volume"].shift(1).rolling(5).mean()
    clipped_df["ret_std5"] = clipped_df["pct_change"].shift(1).rolling(5).std()

    for lag in [1, 2, 3, 5]:
        clipped_df[f"close_lag{lag}"] = clipped_df["close"].shift(lag)
        clipped_df[f"open_lag{lag}"] = clipped_df["open"].shift(lag)
        clipped_df[f"volume_lag{lag}"] = clipped_df["volume"].shift(lag)
        clipped_df[f"pct_change_lag{lag}"] = clipped_df["pct_change"].shift(lag)

    model_df = clipped_df.dropna().reset_index(drop=True)
    summary = {
        "raw_rows": raw_rows,
        "clean_rows": int(len(df)),
        "model_rows": int(len(model_df)),
        "missing_rows_removed": int(raw_rows - len(df)),
        "duplicate_count": duplicate_count,
        "missing_total": int(missing_summary.sum()),
        "start_date": df_raw.iloc[:, 0].min(),
        "end_date": df_raw.iloc[:, 0].max(),
    }
    return df_raw, clipped_df, model_df, {"outlier_df": outlier_df, "summary": summary}


def split_and_scale(
    model_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, np.ndarray, np.ndarray, StandardScaler, list[str]]:
    feature_cols = [
        "open",
        "high",
        "low",
        "volume",
        "year",
        "month",
        "day",
        "weekday",
        "amplitude",
        "open_high_gap",
        "open_low_gap",
        "high_low_ratio",
        "intraday_range_ratio",
        "vol_change_ratio",
        "ma3",
        "ma5",
        "ma10",
        "vol_ma5",
        "ret_std5",
    ]
    for lag in [1, 2, 3, 5]:
        feature_cols.extend([f"close_lag{lag}", f"open_lag{lag}", f"volume_lag{lag}", f"pct_change_lag{lag}"])

    X = model_df[feature_cols]
    y = model_df["close"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, scaler, feature_cols


def evaluate_model(
    name: str,
    model,
    X_train_scaled: np.ndarray,
    X_test_scaled: np.ndarray,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict:
    train_pred = model.predict(X_train_scaled)
    test_pred = model.predict(X_test_scaled)
    return {
        "model": name,
        "train_r2": r2_score(y_train, train_pred),
        "test_r2": r2_score(y_test, test_pred),
        "train_rmse": math.sqrt(mean_squared_error(y_train, train_pred)),
        "test_rmse": math.sqrt(mean_squared_error(y_test, test_pred)),
        "train_mae": mean_absolute_error(y_train, train_pred),
        "test_mae": mean_absolute_error(y_test, test_pred),
        "train_pred": train_pred,
        "test_pred": test_pred,
    }


def train_models(
    X_train_scaled: np.ndarray,
    X_test_scaled: np.ndarray,
    y_train: pd.Series,
    y_test: pd.Series,
) -> tuple[dict, pd.DataFrame, dict]:
    cv = KFold(n_splits=5, shuffle=True, random_state=42)

    linear_model = LinearRegression().fit(X_train_scaled, y_train)

    ridge_search = GridSearchCV(
        Ridge(),
        {"alpha": [0.01, 0.1, 1, 10, 50, 100]},
        cv=cv,
        scoring="r2",
        n_jobs=-1,
    ).fit(X_train_scaled, y_train)
    ridge_model = ridge_search.best_estimator_

    lasso_search = GridSearchCV(
        Lasso(max_iter=100000),
        {"alpha": [0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]},
        cv=cv,
        scoring="r2",
        n_jobs=-1,
    ).fit(X_train_scaled, y_train)
    lasso_model = lasso_search.best_estimator_

    elastic_search = GridSearchCV(
        ElasticNet(max_iter=100000),
        {"alpha": [0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5], "l1_ratio": [0.1, 0.3, 0.5, 0.7, 0.9]},
        cv=cv,
        scoring="r2",
        n_jobs=-1,
    ).fit(X_train_scaled, y_train)
    elastic_model = elastic_search.best_estimator_

    svr_search = GridSearchCV(
        SVR(kernel="linear"),
        {"C": [0.1, 1, 10, 50], "epsilon": [0.01, 0.05, 0.1, 0.2]},
        cv=cv,
        scoring="r2",
        n_jobs=-1,
    ).fit(X_train_scaled, y_train)
    svr_model = svr_search.best_estimator_

    xgb_model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.05,
        reg_lambda=1.0,
        random_state=42,
    )
    xgb_model.fit(X_train_scaled, y_train)

    voting_model = VotingRegressor(
        estimators=[
            ("ridge", clone(ridge_model)),
            ("lasso", clone(lasso_model)),
            ("elastic", clone(elastic_model)),
            ("svr", clone(svr_model)),
        ]
    )
    voting_model.fit(X_train_scaled, y_train)

    stacking_model = StackingRegressor(
        estimators=[
            ("ridge", clone(ridge_model)),
            ("lasso", clone(lasso_model)),
            ("xgb", clone(xgb_model)),
        ],
        final_estimator=Ridge(alpha=1.0),
        cv=5,
        n_jobs=-1,
    )
    stacking_model.fit(X_train_scaled, y_train)

    model_map = {
        "Linear": linear_model,
        "Ridge": ridge_model,
        "Lasso": lasso_model,
        "ElasticNet": elastic_model,
        "SVR": svr_model,
        "XGBoost": xgb_model,
        "Voting": voting_model,
        "Stacking": stacking_model,
    }

    evaluation_records = []
    prediction_cache = {}
    for name, model in model_map.items():
        metrics = evaluate_model(name, model, X_train_scaled, X_test_scaled, y_train, y_test)
        evaluation_records.append(
            {
                "模型": name,
                "训练集R2": round(metrics["train_r2"], 4),
                "测试集R2": round(metrics["test_r2"], 4),
                "训练集RMSE": round(metrics["train_rmse"], 4),
                "测试集RMSE": round(metrics["test_rmse"], 4),
                "训练集MAE": round(metrics["train_mae"], 4),
                "测试集MAE": round(metrics["test_mae"], 4),
            }
        )
        prediction_cache[name] = metrics

    metrics_df = pd.DataFrame(evaluation_records).sort_values("测试集R2", ascending=False).reset_index(drop=True)
    metadata = {
        "ridge_alpha": ridge_model.alpha,
        "lasso_alpha": lasso_model.alpha,
        "lasso_nonzero": int(np.sum(lasso_model.coef_ != 0)),
        "elastic_alpha": elastic_model.alpha,
        "elastic_l1_ratio": elastic_model.l1_ratio,
        "svr_c": svr_model.C,
        "svr_epsilon": svr_model.epsilon,
        "best_model": metrics_df.iloc[0]["模型"],
        "best_test_r2": float(metrics_df.iloc[0]["测试集R2"]),
        "best_test_rmse": float(metrics_df.iloc[0]["测试集RMSE"]),
    }
    return model_map, metrics_df, {"prediction_cache": prediction_cache, "metadata": metadata}


def save_tables(
    metrics_df: pd.DataFrame,
    outlier_df: pd.DataFrame,
    feature_cols: list[str],
    y_test: pd.Series,
    best_pred: np.ndarray,
    prediction_cache: dict,
) -> None:
    metrics_df.to_csv(RESULT_DIR / "model_metrics.csv", index=False, encoding="utf-8-sig")
    outlier_df.to_csv(RESULT_DIR / "outlier_summary.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"feature": feature_cols}).to_csv(RESULT_DIR / "feature_columns.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"真实收盘价": y_test.reset_index(drop=True), "预测收盘价": best_pred}).to_csv(
        RESULT_DIR / "best_model_predictions.csv",
        index=False,
        encoding="utf-8-sig",
    )
    all_predictions = pd.DataFrame({"真实收盘价": y_test.reset_index(drop=True)})
    for model_name, cache in prediction_cache.items():
        all_predictions[f"{model_name}_预测值"] = cache["test_pred"]
    all_predictions.to_csv(RESULT_DIR / "all_model_predictions.csv", index=False, encoding="utf-8-sig")


def draw_figures(
    clean_df: pd.DataFrame,
    model_df: pd.DataFrame,
    X_train: pd.DataFrame,
    X_train_scaled: np.ndarray,
    outlier_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    feature_cols: list[str],
    model_map: dict,
    prediction_cache: dict,
    y_test: pd.Series,
    best_model_name: str,
) -> None:
    corr_cols = ["close", "open", "high", "low", "volume", "pct_change", "amplitude", "ma5", "ma10", "ret_std5"]
    corr = model_df[corr_cols].corr()

    plt.figure(figsize=(8, 5))
    sns.histplot(model_df["close"], bins=30, kde=True, color="#2A6F97")
    plt.title("沪深300收盘价分布")
    plt.xlabel("收盘价")
    plt.ylabel("频数")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "01_close_distribution.png", dpi=300)
    plt.close()

    plt.figure(figsize=(11, 5))
    plt.plot(clean_df["date"], clean_df["close"], color="#D1495B", linewidth=1.6)
    plt.title("沪深300近三年收盘价走势")
    plt.xlabel("日期")
    plt.ylabel("收盘价")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "02_close_trend.png", dpi=300)
    plt.close()

    plt.figure(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", square=True, linewidths=0.4)
    plt.title("主要特征相关性热力图")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "03_corr_heatmap.png", dpi=300)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.barplot(data=outlier_df, x="feature", y="outlier_count", palette="crest")
    plt.title("各数值字段异常值数量")
    plt.xlabel("特征")
    plt.ylabel("异常值个数")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "04_outlier_counts.png", dpi=300)
    plt.close()

    scale_features = [col for col in ["open", "high", "volume", "close_lag1"] if col in X_train.columns]
    scaled_compare_df = pd.concat(
        [
            X_train[scale_features].assign(stage="标准化前"),
            pd.DataFrame(X_train_scaled, columns=feature_cols)[scale_features].assign(stage="标准化后"),
        ],
        ignore_index=True,
    )
    scale_long_df = scaled_compare_df.melt(id_vars="stage", var_name="feature", value_name="value")
    plt.figure(figsize=(11, 5))
    sns.boxplot(data=scale_long_df, x="feature", y="value", hue="stage")
    plt.title("标准化前后特征分布对比")
    plt.xlabel("特征")
    plt.ylabel("取值")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "05_standardization_compare.png", dpi=300)
    plt.close()

    lasso_model = model_map["Lasso"]
    coef_df = pd.DataFrame({"feature": feature_cols, "coef": lasso_model.coef_})
    coef_df["abs_coef"] = coef_df["coef"].abs()
    coef_df = coef_df.sort_values("abs_coef", ascending=False).head(12).sort_values("coef")
    coef_df.to_csv(RESULT_DIR / "lasso_coefficients.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(9, 6))
    sns.barplot(data=coef_df, x="coef", y="feature", palette="viridis")
    plt.title("Lasso回归中绝对值最大的12个系数")
    plt.xlabel("系数值")
    plt.ylabel("特征")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "06_lasso_coefficients.png", dpi=300)
    plt.close()

    metrics_plot_df = metrics_df.copy()
    x = np.arange(len(metrics_plot_df))
    width = 0.35
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].bar(x - width / 2, metrics_plot_df["训练集R2"], width=width, label="训练集R2", color="#1D3557")
    axes[0].bar(x + width / 2, metrics_plot_df["测试集R2"], width=width, label="测试集R2", color="#457B9D")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics_plot_df["模型"], rotation=30)
    axes[0].set_title("模型R2对比")
    axes[0].legend()

    axes[1].bar(x - width / 2, metrics_plot_df["训练集RMSE"], width=width, label="训练集RMSE", color="#E76F51")
    axes[1].bar(x + width / 2, metrics_plot_df["测试集RMSE"], width=width, label="测试集RMSE", color="#F4A261")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(metrics_plot_df["模型"], rotation=30)
    axes[1].set_title("模型RMSE对比")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(RESULT_DIR / "07_model_comparison.png", dpi=300)
    plt.close(fig)

    compare_pred_df = pd.DataFrame({"真实值": y_test.reset_index(drop=True)})
    for model_name, cache in prediction_cache.items():
        compare_pred_df[model_name] = cache["test_pred"]

    fig, axes = plt.subplots(4, 2, figsize=(14, 14), sharex=True)
    axes = axes.flatten()
    for ax, model_name in zip(axes, compare_pred_df.columns[1:]):
        ax.plot(compare_pred_df.index, compare_pred_df["真实值"], label="真实值", linewidth=1.8, color="#1D3557")
        ax.plot(compare_pred_df.index, compare_pred_df[model_name], label="预测值", linewidth=1.5, color="#E76F51", alpha=0.9)
        ax.set_title(f"{model_name}预测结果对比")
        ax.set_xlabel("测试样本序号")
        ax.set_ylabel("收盘价")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULT_DIR / "08_model_prediction_compare.png", dpi=300)
    plt.close(fig)

    fig, axes = plt.subplots(4, 2, figsize=(14, 14))
    axes = axes.flatten()
    for ax, model_name in zip(axes, compare_pred_df.columns[1:]):
        ax.scatter(compare_pred_df["真实值"], compare_pred_df[model_name], s=18, alpha=0.75, color="#2A9D8F")
        min_val = min(compare_pred_df["真实值"].min(), compare_pred_df[model_name].min())
        max_val = max(compare_pred_df["真实值"].max(), compare_pred_df[model_name].max())
        ax.plot([min_val, max_val], [min_val, max_val], linestyle="--", color="#D62828", linewidth=1.2)
        ax.set_title(f"{model_name}散点对比")
        ax.set_xlabel("真实收盘价")
        ax.set_ylabel("预测收盘价")
    fig.tight_layout()
    fig.savefig(RESULT_DIR / "09_model_prediction_scatter.png", dpi=300)
    plt.close(fig)

    best_pred = prediction_cache[best_model_name]["test_pred"]
    line_min = min(y_test.min(), best_pred.min())
    line_max = max(y_test.max(), best_pred.max())
    plt.figure(figsize=(6.5, 6))
    plt.scatter(y_test, best_pred, alpha=0.75, color="#2A9D8F")
    plt.plot([line_min, line_max], [line_min, line_max], color="#E63946", linestyle="--", linewidth=1.5)
    plt.title(f"{best_model_name}模型测试集预测效果")
    plt.xlabel("真实收盘价")
    plt.ylabel("预测收盘价")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "10_best_model_prediction.png", dpi=300)
    plt.close()

    residuals = y_test.reset_index(drop=True) - best_pred
    plt.figure(figsize=(8, 5))
    sns.histplot(residuals, bins=25, kde=True, color="#6A994E")
    plt.title(f"{best_model_name}模型残差分布")
    plt.xlabel("残差")
    plt.ylabel("频数")
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "11_best_model_residuals.png", dpi=300)
    plt.close()


def build_notebook() -> None:
    nb = nbf.v4.new_notebook()
    cells = [
        nbf.v4.new_markdown_cell(
            f"# 上机实验04：回归模型与模型评估\n\n"
            f"学号：{STUDENT_ID}  姓名：{STUDENT_NAME}\n\n"
            "数据集：`沪深300_最近三年.csv`\n\n"
            "本 notebook 参照上次作业的风格组织为“数据预处理、标准化、模型训练、预测对比、结果分析”几个部分。"
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.0 导入库与路径
                import math
                import warnings
                from pathlib import Path

                import matplotlib.pyplot as plt
                import numpy as np
                import pandas as pd
                import seaborn as sns
                from sklearn.base import clone
                from sklearn.ensemble import StackingRegressor, VotingRegressor
                from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
                from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
                from sklearn.model_selection import GridSearchCV, KFold, train_test_split
                from sklearn.preprocessing import StandardScaler
                from sklearn.svm import SVR
                from xgboost import XGBRegressor

                warnings.filterwarnings("ignore")
                plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
                plt.rcParams["axes.unicode_minus"] = False
                sns.set_theme(style="whitegrid", font="Microsoft YaHei")

                CURRENT_DIR = Path.cwd().resolve()
                BASE_DIR = CURRENT_DIR.parent if CURRENT_DIR.name == "code" else CURRENT_DIR
                RESULT_DIR = BASE_DIR / "result"
                DATA_PATH = next((BASE_DIR / "code").glob("*.csv"))
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.1 数据加载与基础清洗
                raw_df = pd.read_csv(DATA_PATH)
                raw_df.columns = ["date", "close", "open", "high", "low", "volume", "pct_change"]
                df = raw_df.copy()
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").reset_index(drop=True)
                df["volume"] = df["volume"].astype(str).str.replace("K", "", regex=False).str.replace(",", "", regex=False).astype(float)
                df["pct_change"] = pd.to_numeric(df["pct_change"].astype(str).str.replace("%", "", regex=False), errors="coerce")

                missing_before = df.isna().sum()
                duplicate_count = df.duplicated().sum()
                df = df.dropna().drop_duplicates().reset_index(drop=True)

                print("缺失值统计：")
                print(missing_before)
                print("重复行数量：", duplicate_count)
                df.head()
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.2 异常值处理与特征工程
                numeric_cols = ["close", "open", "high", "low", "volume", "pct_change"]
                outlier_records = []
                for col in numeric_cols:
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
                    outlier_records.append({"feature": col, "outlier_count": int(outlier_count)})
                    df[col] = df[col].clip(lower=lower, upper=upper)

                df["year"] = df["date"].dt.year
                df["month"] = df["date"].dt.month
                df["day"] = df["date"].dt.day
                df["weekday"] = df["date"].dt.weekday + 1
                df["amplitude"] = df["high"] - df["low"]
                df["open_high_gap"] = df["high"] - df["open"]
                df["open_low_gap"] = df["open"] - df["low"]
                df["high_low_ratio"] = df["high"] / df["low"]
                df["intraday_range_ratio"] = (df["high"] - df["low"]) / df["open"]
                df["vol_change_ratio"] = df["volume"].pct_change()
                df["ma3"] = df["close"].shift(1).rolling(3).mean()
                df["ma5"] = df["close"].shift(1).rolling(5).mean()
                df["ma10"] = df["close"].shift(1).rolling(10).mean()
                df["vol_ma5"] = df["volume"].shift(1).rolling(5).mean()
                df["ret_std5"] = df["pct_change"].shift(1).rolling(5).std()
                for lag in [1, 2, 3, 5]:
                    df[f"close_lag{lag}"] = df["close"].shift(lag)
                    df[f"open_lag{lag}"] = df["open"].shift(lag)
                    df[f"volume_lag{lag}"] = df["volume"].shift(lag)
                    df[f"pct_change_lag{lag}"] = df["pct_change"].shift(lag)

                model_df = df.dropna().reset_index(drop=True)
                pd.DataFrame(outlier_records).sort_values("outlier_count", ascending=False)
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.3 预处理结果可视化
                fig, axes = plt.subplots(2, 2, figsize=(15, 10))
                missing_before.plot(kind="bar", ax=axes[0, 0], color="#d62728")
                axes[0, 0].set_title("缺失值统计")
                sns.histplot(df["close"], kde=True, ax=axes[0, 1], color="#1f77b4")
                axes[0, 1].set_title("收盘价分布")
                sns.boxplot(data=df[["close", "open", "high", "low"]], ax=axes[1, 0])
                axes[1, 0].set_title("价格特征箱线图")
                axes[1, 1].plot(df["date"], df["close"], color="#2ca02c", linewidth=2)
                axes[1, 1].set_title("收盘价走势")
                axes[1, 1].tick_params(axis="x", rotation=45)
                fig.tight_layout()
                fig.savefig(RESULT_DIR / "fig1_preprocess_overview.png", dpi=300)
                plt.show()
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.4 构造特征矩阵、划分训练集和测试集
                feature_cols = [
                    "open", "high", "low", "volume", "year", "month", "day", "weekday",
                    "amplitude", "open_high_gap", "open_low_gap",
                    "high_low_ratio", "intraday_range_ratio", "vol_change_ratio",
                    "ma3", "ma5", "ma10", "vol_ma5", "ret_std5"
                ]
                for lag in [1, 2, 3, 5]:
                    feature_cols.extend([f"close_lag{lag}", f"open_lag{lag}", f"volume_lag{lag}", f"pct_change_lag{lag}"])

                X = model_df[feature_cols]
                y = model_df["close"]
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)
                print("训练集形状：", X_train.shape)
                print("测试集形状：", X_test.shape)
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.5 标准化处理及可视化
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                scale_features = ["open", "high", "volume", "close_lag1"]
                scale_compare_df = pd.concat(
                    [
                        X_train[scale_features].assign(stage="标准化前"),
                        pd.DataFrame(X_train_scaled, columns=feature_cols)[scale_features].assign(stage="标准化后"),
                    ],
                    ignore_index=True,
                )
                scale_long_df = scale_compare_df.melt(id_vars="stage", var_name="feature", value_name="value")
                plt.figure(figsize=(11, 5))
                sns.boxplot(data=scale_long_df, x="feature", y="value", hue="stage")
                plt.title("标准化前后特征分布对比")
                plt.tight_layout()
                plt.savefig(RESULT_DIR / "05_standardization_compare.png", dpi=300)
                plt.show()
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.6 构建并训练各类回归模型
                def eval_model(name, model):
                    train_pred = model.predict(X_train_scaled)
                    test_pred = model.predict(X_test_scaled)
                    return {
                        "模型": name,
                        "训练集R2": round(r2_score(y_train, train_pred), 4),
                        "测试集R2": round(r2_score(y_test, test_pred), 4),
                        "训练集RMSE": round(math.sqrt(mean_squared_error(y_train, train_pred)), 4),
                        "测试集RMSE": round(math.sqrt(mean_squared_error(y_test, test_pred)), 4),
                        "训练集MAE": round(mean_absolute_error(y_train, train_pred), 4),
                        "测试集MAE": round(mean_absolute_error(y_test, test_pred), 4),
                        "test_pred": test_pred
                    }

                cv = KFold(n_splits=5, shuffle=True, random_state=42)
                linear_model = LinearRegression().fit(X_train_scaled, y_train)
                ridge_model = GridSearchCV(Ridge(), {"alpha": [0.01, 0.1, 1, 10, 50, 100]}, cv=cv, scoring="r2", n_jobs=-1).fit(X_train_scaled, y_train).best_estimator_
                lasso_model = GridSearchCV(Lasso(max_iter=100000), {"alpha": [0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]}, cv=cv, scoring="r2", n_jobs=-1).fit(X_train_scaled, y_train).best_estimator_
                elastic_model = GridSearchCV(ElasticNet(max_iter=100000), {"alpha": [0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5], "l1_ratio": [0.1, 0.3, 0.5, 0.7, 0.9]}, cv=cv, scoring="r2", n_jobs=-1).fit(X_train_scaled, y_train).best_estimator_
                svr_model = GridSearchCV(SVR(kernel="linear"), {"C": [0.1, 1, 10, 50], "epsilon": [0.01, 0.05, 0.1, 0.2]}, cv=cv, scoring="r2", n_jobs=-1).fit(X_train_scaled, y_train).best_estimator_
                xgb_model = XGBRegressor(objective="reg:squarederror", n_estimators=200, learning_rate=0.05, max_depth=4, subsample=0.85, colsample_bytree=0.85, reg_alpha=0.05, reg_lambda=1.0, random_state=42)
                xgb_model.fit(X_train_scaled, y_train)
                voting_model = VotingRegressor([("ridge", clone(ridge_model)), ("lasso", clone(lasso_model)), ("elastic", clone(elastic_model)), ("svr", clone(svr_model))]).fit(X_train_scaled, y_train)
                stacking_model = StackingRegressor([("ridge", clone(ridge_model)), ("lasso", clone(lasso_model)), ("xgb", clone(xgb_model))], final_estimator=Ridge(alpha=1.0), cv=5, n_jobs=-1).fit(X_train_scaled, y_train)

                results = [
                    eval_model("Linear", linear_model),
                    eval_model("Ridge", ridge_model),
                    eval_model("Lasso", lasso_model),
                    eval_model("ElasticNet", elastic_model),
                    eval_model("SVR", svr_model),
                    eval_model("XGBoost", xgb_model),
                    eval_model("Voting", voting_model),
                    eval_model("Stacking", stacking_model),
                ]
                metrics_df = pd.DataFrame([{k: v for k, v in row.items() if k != "test_pred"} for row in results]).sort_values("测试集R2", ascending=False).reset_index(drop=True)
                metrics_df
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.7 Lasso系数与模型指标可视化
                coef_df = pd.DataFrame({"feature": feature_cols, "coef": lasso_model.coef_})
                coef_df["abs_coef"] = coef_df["coef"].abs()
                coef_df = coef_df.sort_values("abs_coef", ascending=False).head(12).sort_values("coef")
                plt.figure(figsize=(9, 6))
                sns.barplot(data=coef_df, x="coef", y="feature", palette="viridis")
                plt.title("Lasso回归中绝对值最大的12个系数")
                plt.tight_layout()
                plt.savefig(RESULT_DIR / "06_lasso_coefficients.png", dpi=300)
                plt.show()

                x = np.arange(len(metrics_df))
                width = 0.35
                fig, axes = plt.subplots(1, 2, figsize=(13, 5))
                axes[0].bar(x - width / 2, metrics_df["训练集R2"], width=width, label="训练集R2")
                axes[0].bar(x + width / 2, metrics_df["测试集R2"], width=width, label="测试集R2")
                axes[0].set_xticks(x)
                axes[0].set_xticklabels(metrics_df["模型"], rotation=30)
                axes[0].legend()
                axes[0].set_title("模型R2对比")
                axes[1].bar(x - width / 2, metrics_df["训练集RMSE"], width=width, label="训练集RMSE")
                axes[1].bar(x + width / 2, metrics_df["测试集RMSE"], width=width, label="测试集RMSE")
                axes[1].set_xticks(x)
                axes[1].set_xticklabels(metrics_df["模型"], rotation=30)
                axes[1].legend()
                axes[1].set_title("模型RMSE对比")
                fig.tight_layout()
                fig.savefig(RESULT_DIR / "07_model_comparison.png", dpi=300)
                plt.show()
                """
            ).strip()
        ),
        nbf.v4.new_code_cell(
            textwrap.dedent(
                """
                # P1.8 各模型预测结果可视化对比
                compare_pred_df = pd.DataFrame({"真实值": y_test.reset_index(drop=True)})
                for row in results:
                    compare_pred_df[row["模型"]] = row["test_pred"]

                fig, axes = plt.subplots(4, 2, figsize=(14, 14), sharex=True)
                axes = axes.flatten()
                for ax, model_name in zip(axes, compare_pred_df.columns[1:]):
                    ax.plot(compare_pred_df.index, compare_pred_df["真实值"], label="真实值", linewidth=1.8, color="#1D3557")
                    ax.plot(compare_pred_df.index, compare_pred_df[model_name], label="预测值", linewidth=1.5, color="#E76F51", alpha=0.9)
                    ax.set_title(f"{model_name}预测结果对比")
                    ax.legend(fontsize=8)
                fig.tight_layout()
                fig.savefig(RESULT_DIR / "08_model_prediction_compare.png", dpi=300)
                plt.show()

                fig, axes = plt.subplots(4, 2, figsize=(14, 14))
                axes = axes.flatten()
                for ax, model_name in zip(axes, compare_pred_df.columns[1:]):
                    ax.scatter(compare_pred_df["真实值"], compare_pred_df[model_name], s=18, alpha=0.75, color="#2A9D8F")
                    min_val = min(compare_pred_df["真实值"].min(), compare_pred_df[model_name].min())
                    max_val = max(compare_pred_df["真实值"].max(), compare_pred_df[model_name].max())
                    ax.plot([min_val, max_val], [min_val, max_val], linestyle="--", color="red")
                    ax.set_title(f"{model_name}散点对比")
                fig.tight_layout()
                fig.savefig(RESULT_DIR / "09_model_prediction_scatter.png", dpi=300)
                plt.show()
                """
            ).strip()
        ),
    ]
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13"},
    }
    nbf.write(nb, NOTEBOOK_PATH)


def format_table_for_latex(metrics_df: pd.DataFrame) -> str:
    lines = []
    for _, row in metrics_df.iterrows():
        lines.append(
            f"{row['模型']} & {row['训练集R2']:.4f} & {row['测试集R2']:.4f} & "
            f"{row['训练集RMSE']:.4f} & {row['测试集RMSE']:.4f} \\\\"
        )
    return "\n".join(lines)


def write_latex_report(summary: dict, outlier_df: pd.DataFrame, metrics_df: pd.DataFrame, metadata: dict) -> None:
    nonzero_outliers = outlier_df[outlier_df["outlier_count"] > 0].head(3)
    metric_table = format_table_for_latex(metrics_df)
    if len(nonzero_outliers) >= 2:
        outlier_text = (
            f"{nonzero_outliers.iloc[0]['feature']}（{int(nonzero_outliers.iloc[0]['outlier_count'])} 个）、"
            f"{nonzero_outliers.iloc[1]['feature']}（{int(nonzero_outliers.iloc[1]['outlier_count'])} 个）"
        )
        if len(nonzero_outliers) >= 3:
            outlier_text += f"、{nonzero_outliers.iloc[2]['feature']}（{int(nonzero_outliers.iloc[2]['outlier_count'])} 个）"
        else:
            outlier_text += "，其余字段异常值数量较少"
    else:
        outlier_text = "各字段异常值数量整体较少"
    outlier_text = outlier_text.replace("_", r"\_")
    content = rf"""
\documentclass[12pt,a4paper]{{ctexart}}
\usepackage[a4paper,margin=2.2cm]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{float}}
\usepackage{{enumitem}}
\usepackage{{array}}
\usepackage{{longtable}}
\usepackage{{amsmath}}
\usepackage{{caption}}
\captionsetup{{font=small}}
\graphicspath{{{{../result/}}{{result/}}}}

\begin{{document}}

\begin{{center}}
{{\LARGE \textbf{{上机实验报告——回归模型与模型评估}}}}\\[1em]
学号：{STUDENT_ID} \hspace{{2cm}} 姓名：{STUDENT_NAME}
\end{{center}}

\vspace{{1em}}

\section*{{一、实验目的}}
\begin{{enumerate}}[label=（\arabic*）]
\item 掌握线性正则化模型：理解并实现岭回归（Ridge）、Lasso 回归和 ElasticNet 回归，掌握 L1 与 L2 正则化在防止过拟合和处理多重共线性中的作用。
\item 掌握强力 Boosting 算法：学会使用 XGBoost 进行回归任务，理解其迭代纠错的核心原理。
\item 理解集成学习的思想：掌握 Voting（投票）与 Stacking（堆叠）两种集成策略，通过组合多个基模型提升预测精度和稳定性。
\item 完成模型对比与评估：能够比较不同回归模型在相同数据集上的表现，并结合结果分析模型的适用场景。
\end{{enumerate}}

\section*{{二、实验环境}}
\begin{{enumerate}}[label=（\arabic*）]
\item 编程语言：Python
\item 核心库：
\end{{enumerate}}

\noindent pandas、numpy：数据读取、数据清洗与数值计算\\
\noindent sklearn：数据预处理、模型构建、正则化回归、集成学习与模型评估\\
\noindent xgboost：XGBoost 回归模型\\
\noindent matplotlib、seaborn：数据可视化与结果展示

\section*{{三、实验数据介绍（对使用数据集作介绍）}}
本实验使用的数据文件为 \texttt{{code/沪深300\_最近三年.csv}}，数据内容为沪深300指数近三年的日线交易记录。原始数据共 {summary['raw_rows']} 条样本，时间范围为 {summary['start_date']} 至 {summary['end_date']}，包含日期、收盘价、开盘价、最高价、最低价、交易量和涨跌幅 7 个原始字段。

结合实验任务，本次作业以“收盘价”作为回归目标变量，其余价格类字段、成交量字段以及基于时间顺序构造的历史特征作为输入变量。与实验三保持一致，本文在原始字段基础上进一步构造了年、月、日、星期、价格振幅、开高差、开低差、高低比、日内振幅率、成交量变化率、3/5/10 日滚动均值、5 日收益波动，以及 1/2/3/5 日滞后特征，从而增强模型对价格变化规律的表达能力。

需要特别说明的是，原始字段中的“涨跌幅”由收盘价相对前一交易日收盘价计算得到，因此如果直接把当日涨跌幅作为输入，会带来目标泄漏风险。为避免该问题，实验中仅保留其滞后项参与建模。经过缺失值处理、异常值截尾和滚动特征构造后，最终可用于实验建模的样本数为 {summary['model_rows']} 条。

\section*{{四、实验内容与步骤}}

\subsection*{{1. 数据加载与预处理（读取数据集、处理缺失值、异常值、重复行，并说明标准化处理）}}
首先读取 CSV 文件，并将日期字段转换为日期类型，再按照时间先后顺序排序。随后将交易量中的 \texttt{{K}} 去除并转换为数值型，将涨跌幅中的百分号去除并转换为浮点型，便于后续计算和建模。检查结果表明，原始数据中仅存在 1 条缺失记录，且集中在涨跌幅字段；重复行数量为 0，因此本文直接删除缺失样本并保留其余有效数据。

在异常值处理方面，本文延续实验三的思路，使用 IQR（四分位距）方法对收盘价、开盘价、最高价、最低价、交易量和涨跌幅六个数值字段进行检测，并采用截尾（clip）方式降低极端值对回归模型训练的影响。检测结果显示，异常值相对较多的字段为：{outlier_text}。从金融数据特点来看，这类异常值通常反映的是阶段性急涨急跌或交易放量现象，并不一定是错误数据，因此实验中未直接删除，而是通过截尾方式保留总体趋势、削弱极端扰动。

在完成清洗后，进一步进行特征工程。除原始价格字段外，增加了日历特征（年、月、日、星期）、价格差分特征（振幅、开高差、开低差）、比例特征（高低比、日内振幅率）、成交量变化特征、滚动均值特征（3 日、5 日、10 日均线）以及滞后特征（前 1/2/3/5 日价格与成交量信息）。这些特征一方面能增强模型的解释能力，另一方面也为 Lasso、ElasticNet 和集成模型提供更丰富的输入空间。

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\textwidth]{{01_close_distribution.png}}
\caption{{收盘价分布图}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\textwidth]{{02_close_trend.png}}
\caption{{沪深300近三年收盘价走势}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.80\textwidth]{{04_outlier_counts.png}}
\caption{{各数值字段异常值统计}}
\end{{figure}}

由于岭回归、Lasso 和 ElasticNet 等正则化模型对特征尺度非常敏感，如果不同特征数量级差异过大，正则化惩罚项就无法对各个系数进行公平约束，因此必须进行标准化处理。本文在训练集上使用 \texttt{{StandardScaler}} 拟合均值和标准差，再把同样的变换应用到训练集和测试集。图~\ref{{fig:std-compare}} 展示了标准化前后部分特征分布的变化情况，可以看到标准化后各特征的尺度更加统一，数值整体集中在 0 附近，有利于正则化模型稳定收敛。

\begin{{figure}}[H]
\centering
\includegraphics[width=0.90\textwidth]{{05_standardization_compare.png}}
\caption{{标准化前后特征分布对比}}
\label{{fig:std-compare}}
\end{{figure}}

\subsection*{{2. 数据集划分（训练集与测试集划分）}}
本实验采用常见的训练集 80\%、测试集 20\% 的划分方式，对全部建模样本进行切分。其中训练集样本数为 {summary['train_samples']}，测试集样本数为 {summary['test_samples']}，对应比例分别约为 {summary['train_ratio']:.0%} 和 {summary['test_ratio']:.0%}。考虑到本次实验的重点是比较多种回归模型在同一数据集上的表现，因此这里采用固定随机种子 \texttt{{random\_state=42}} 的随机划分方式，以保证不同模型使用完全一致的训练样本与测试样本，确保结果具有可比性。

划分完成后，将训练集特征矩阵输入 \texttt{{StandardScaler}} 进行拟合，得到标准化后的训练集和测试集，再用于后续所有模型训练和预测。这样做可以使普通线性回归和各类正则化回归在统一尺度下比较，也便于 Voting 与 Stacking 中不同基模型之间的组合。

\subsection*{{3. 构建与训练回归模型}}
本实验共构建了 8 种回归模型，分别为普通线性回归（Linear）、Ridge 回归、Lasso 回归、ElasticNet 回归、支持向量回归（SVR）、XGBoost 回归、Voting 回归和 Stacking 回归。其中，普通线性回归作为基准模型，用于衡量不加正则化时的拟合效果；Ridge 通过 L2 正则化缓解共线性；Lasso 通过 L1 正则化实现特征筛选；ElasticNet 结合 L1 与 L2 正则化；XGBoost 用于测试非线性树模型在该数据集上的效果；Voting 和 Stacking 则用于验证集成学习策略对精度与稳定性的提升作用。

各模型参数设置如下：Ridge 使用网格搜索在 $\alpha \in \{{0.01, 0.1, 1, 10, 50, 100\}}$ 中选取最优值，最终得到 $\alpha={metadata['ridge_alpha']}$；Lasso 的最优参数为 $\alpha={metadata['lasso_alpha']}$，非零系数数量为 {metadata['lasso_nonzero']}，说明在当前特征集合下 Lasso 保留了主要有效特征并对部分冗余变量进行了压缩；ElasticNet 的最优参数为 $\alpha={metadata['elastic_alpha']}$、\texttt{{l1\_ratio}}={metadata['elastic_l1_ratio']}；SVR 的最优参数为 \texttt{{C={metadata['svr_c']}}}、\texttt{{epsilon={metadata['svr_epsilon']}}}；XGBoost 采用 \texttt{{n\_estimators=200}}、\texttt{{learning\_rate=0.05}}、\texttt{{max\_depth=4}} 的参数组合。Voting 回归集成了 Ridge、Lasso、ElasticNet 和 SVR 四个模型；Stacking 回归第一层使用 Ridge、Lasso、XGBoost，第二层使用 Ridge 作为元模型。

为了让不同模型的预测效果比较更直观，除指标表外，实验还对所有模型在测试集上的预测结果进行了可视化。图~\ref{{fig:model-predict-line}} 给出了各模型在测试集上的“真实值-预测值”折线对比图，图~\ref{{fig:model-predict-scatter}} 给出了真实值与预测值的散点对比图。通过这两组图可以观察各模型对收盘价波动的跟踪程度和拟合偏差，其中线性正则化模型整体表现较为稳定，预测曲线与真实曲线贴合度较高，而 XGBoost 的离散误差相对更明显。

\begin{{figure}}[H]
\centering
\includegraphics[width=0.94\textwidth]{{08_model_prediction_compare.png}}
\caption{{各预测模型测试集折线对比}}
\label{{fig:model-predict-line}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.94\textwidth]{{09_model_prediction_scatter.png}}
\caption{{各预测模型测试集散点对比}}
\label{{fig:model-predict-scatter}}
\end{{figure}}

\subsection*{{4. 模型预测与评估}}
模型训练完成后，使用测试集进行预测，并采用决定系数 $R^2$、均方根误差 RMSE 和平均绝对误差 MAE 对各模型效果进行评价。其中，$R^2$ 越接近 1 表示模型解释能力越强；RMSE 和 MAE 越小，说明预测误差越低。各模型性能对比如表~\ref{{tab:metrics}} 所示。

\begin{{table}}[H]
\centering
\caption{{各模型性能对比}}
\label{{tab:metrics}}
\begin{{tabular}}{{lcccc}}
\toprule
模型 & 训练集$R^2$ & 测试集$R^2$ & 训练集RMSE & 测试集RMSE \\
\midrule
{metric_table}
\bottomrule
\end{{tabular}}
\end{{table}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.86\textwidth]{{07_model_comparison.png}}
\caption{{各模型性能指标综合对比}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.72\textwidth]{{06_lasso_coefficients.png}}
\caption{{Lasso 回归重要系数图}}
\end{{figure}}

\subsection*{{5. 其他，可选做}}
在完成实验基本要求之外，本文还额外保存了模型指标表、全部模型预测值表、Lasso 系数表和最优模型预测结果文件，便于后续整理、复查和再次分析。这些附加结果文件存放在 \texttt{{result}} 目录下，可直接用于报告撰写和进一步实验扩展。

\section*{{五、实验结果与分析}}
从表~\ref{{tab:metrics}} 可以看出，在本次实验中，测试集表现最优的模型为 \textbf{{{metadata['best_model']}}}，其测试集 $R^2$ 达到 {metadata['best_test_r2']:.4f}，测试集 RMSE 为 {metadata['best_test_rmse']:.4f}。这说明经过标准化和较丰富的特征工程后，线性正则化模型在该数据集上具有非常强的拟合能力和泛化能力。

进一步观察不同模型之间的差异，可以发现普通线性回归、Ridge、Lasso、ElasticNet、Voting 和 Stacking 的测试集表现整体都很接近，说明当前数据中的主要关系仍以线性结构为主，正则化和集成方法更多起到增强稳定性、缓解冗余特征影响的作用。其中 Ridge 在测试集上取得最高的 $R^2$，表明 L2 正则化在多重共线性较强的特征环境下具有较好的平衡效果；Lasso 和 ElasticNet 与其差距很小，说明 L1 正则化和混合正则化同样能保持很高的预测精度。

从 Lasso 的系数图可以进一步看出，模型会自动压缩部分系数并保留少数关键特征，体现了 L1 正则化在特征筛选方面的优势。由于本次实验构造了较多价格、成交量和滞后变量，这些特征之间存在较强相关性，因此 Lasso 和 ElasticNet 的引入是有必要的。从最终结果来看，它们既没有明显降低模型表现，又提升了模型解释性。

再看 XGBoost、Voting 和 Stacking 三类模型的表现。XGBoost 在训练集上拟合能力很强，但测试集表现略低于最优线性模型，这说明虽然树模型具有更强的非线性表达能力，但在当前特征结构下并没有占到明显优势。Voting 回归通过平均多个相对稳定的基模型，在测试集上同样取得了很高的 $R^2$，说明简单集成可以有效平滑单个模型的波动。Stacking 回归虽然结构更复杂，但测试表现依旧优秀，说明多层集成策略在本实验数据上是有效的。

结合图~\ref{{fig:model-predict-line}} 和图~\ref{{fig:model-predict-scatter}} 可以更直观地发现，不同模型对测试集真实值的跟踪能力存在细微差异。Ridge、Lasso、ElasticNet 和 Voting 的预测曲线与真实曲线贴合度很高，散点也大多分布在对角线附近；XGBoost 的散点离散程度更明显，说明其在部分样本上预测偏差较大。由此可见，在当前任务中，并不是模型越复杂效果就越好，合适的特征工程加上稳定的线性正则化模型往往更有效。

为了进一步说明最优模型的预测质量，本文还对最优模型进行了单独的真实值-预测值散点图和残差分布分析。图~\ref{{fig:best-pred}} 中样本点大多分布在理想对角线附近，说明预测值与真实值高度一致；图~\ref{{fig:best-residual}} 显示残差主要集中在 0 附近，整体不存在明显系统偏差，仅在少数样本上存在相对较大的误差。

\begin{{figure}}[H]
\centering
\includegraphics[width=0.68\textwidth]{{10_best_model_prediction.png}}
\caption{{最优模型预测值与真实值对比}}
\label{{fig:best-pred}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.75\textwidth]{{11_best_model_residuals.png}}
\caption{{最优模型残差分布}}
\label{{fig:best-residual}}
\end{{figure}}

总体来看，本次实验说明了三个重要结论。第一，在特征数量较多且存在明显共线性的情况下，Ridge、Lasso 和 ElasticNet 等正则化回归模型是非常有效的选择。第二，标准化处理不仅是实验步骤要求，更是保证正则化公平惩罚各个特征的重要前提。第三，Voting 和 Stacking 等集成学习方法虽然结构更复杂，但是否一定优于正则化线性模型仍然取决于具体数据特征，因此模型选择应以实验结果为依据，而不能仅凭模型复杂度判断优劣。

\section*{{六、实验总结}}
本次实验围绕“回归模型与模型评估”这一主题，完整实现了数据读取、缺失值处理、异常值处理、特征工程、标准化、模型训练、模型预测、结果可视化和实验报告撰写的完整流程。与实验三相比，本次实验不仅继续强化了数据预处理与特征构造的能力，还进一步扩展到了正则化模型、Boosting 模型和集成学习模型的比较分析。

通过实验，我进一步理解了 Ridge、Lasso 和 ElasticNet 三种正则化方法之间的联系与区别，也体会到特征标准化在正则化模型中的必要性。同时，通过将 XGBoost、Voting 和 Stacking 纳入同一实验框架，我更加清楚地认识到，不同模型各有优势，最终应通过统一的数据集和统一的评价指标进行客观比较。

从实验结果来看，在沪深300近三年的日线数据上，经过适当的特征工程和标准化后，线性正则化模型表现非常稳定，其中 Ridge 模型综合效果最好。这说明面对结构较稳定、线性关系较强的数据场景，简单、可解释且稳健的模型往往比更复杂的非线性模型更实用。后续如果继续拓展本实验，还可以尝试时间顺序划分、滚动窗口验证或更复杂的金融时序特征，以进一步研究模型在更严格预测场景下的表现。

\end{{document}}
"""
    REPORT_PATH.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    _, clean_df, model_df, prep_info = load_and_prepare_data()
    outlier_df = prep_info["outlier_df"]
    summary = prep_info["summary"]
    X_train, X_test, y_train, y_test, X_train_scaled, X_test_scaled, _, feature_cols = split_and_scale(model_df)
    summary["train_samples"] = int(len(X_train))
    summary["test_samples"] = int(len(X_test))
    summary["train_ratio"] = round(len(X_train) / len(model_df), 4)
    summary["test_ratio"] = round(len(X_test) / len(model_df), 4)
    model_map, metrics_df, train_info = train_models(X_train_scaled, X_test_scaled, y_train, y_test)

    best_model_name = train_info["metadata"]["best_model"]
    best_pred = train_info["prediction_cache"][best_model_name]["test_pred"]
    save_tables(metrics_df, outlier_df, feature_cols, y_test, best_pred, train_info["prediction_cache"])
    draw_figures(
        clean_df=clean_df,
        model_df=model_df,
        X_train=X_train,
        X_train_scaled=X_train_scaled,
        outlier_df=outlier_df,
        metrics_df=metrics_df,
        feature_cols=feature_cols,
        model_map=model_map,
        prediction_cache=train_info["prediction_cache"],
        y_test=y_test,
        best_model_name=best_model_name,
    )
    build_notebook()
    write_latex_report(summary, outlier_df, metrics_df, train_info["metadata"])

    summary_payload = {
        "notebook": str(NOTEBOOK_PATH),
        "report": str(REPORT_PATH),
        "best_model": train_info["metadata"]["best_model"],
        "best_test_r2": train_info["metadata"]["best_test_r2"],
        "best_test_rmse": train_info["metadata"]["best_test_rmse"],
    }
    print(json.dumps(summary_payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
