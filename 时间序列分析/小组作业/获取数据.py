import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt

# === 从腾讯财经获取沪深300指数历史数据 ===
df = ak.stock_zh_index_daily_tx(symbol="sh000300")
# === 重置索引、整理列 ===
df = df.reset_index().rename(columns={"date": "Date", "close": "ClosePrice"})
# === 强制转为 pandas 的 datetime 类型 ===
df["Date"] = pd.to_datetime(df["Date"])
# === 筛选 2020年1月1日之后的数据 ===
df = df[df["Date"] >= pd.Timestamp("2020-01-01")]
# === 保存  ===
df.to_csv("CSI300_Tencent_2020_to_today.csv", index=False, encoding="utf-8-sig")


print(df.head())
print(f"\n共 {len(df)} 条交易记录（从 {df['Date'].min()} 至 {df['Date'].max()}）")
