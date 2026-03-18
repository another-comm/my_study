import datetime as dt
import requests
import pandas as pd

def to_k_str(v):
    v = float(v)
    return f"{v/1000:.2f}K"

def to_pct_str(x):
    if pd.isna(x):
        return ""
    return f"{x:.2f}%"

def fetch_csi300_last_3y_like_screenshot():
    end = dt.date.today()
    start = end.replace(year=end.year - 3)

    # 沪深300 常用：sh000300（备选 sz399300）
    codes = ["sh000300", "sz399300"]
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    last_err = None
    for code in codes:
        try:
            params = {"param": f"{code},day,{start},{end},1000,qfq"}
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            js = r.json()

            day = js["data"][code]["day"]  # [date, open, close, high, low, volume]
            df = pd.DataFrame(day, columns=["日期", "开盘", "收盘", "高", "低", "交易量"])
            df[["开盘", "收盘", "高", "低", "交易量"]] = df[["开盘", "收盘", "高", "低", "交易量"]].astype(float)

            # 先按日期升序算涨跌幅（当日收盘相对前一日收盘）
            df = df.sort_values("日期").reset_index(drop=True)
            df["涨跌幅"] = (df["收盘"].pct_change() * 100)

            # 格式化为截图风格
            df["交易量"] = df["交易量"].apply(to_k_str)
            df["涨跌幅"] = df["涨跌幅"].apply(to_pct_str)

            # 调整列顺序，并按最新在上
            df = df[["日期", "收盘", "开盘", "高", "低", "交易量", "涨跌幅"]]
            df = df.sort_values("日期", ascending=False).reset_index(drop=True)
            return df, code

        except Exception as e:
            last_err = e

    raise RuntimeError(f"拉取失败：{last_err}")

if __name__ == "__main__":
    df, used_code = fetch_csi300_last_3y_like_screenshot()
    print("使用代码：", used_code)
    print(df.head(10))

    df.to_csv("沪深300_最近三年.csv", index=False, encoding="utf-8-sig")
    df.to_excel("沪深300_最近三年.xlsx", index=False)
    print("已导出：沪深300_最近三年.csv / .xlsx")