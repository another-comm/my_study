import pandas as pd
import numpy as np
import sys 
import time
import warnings

# --- 尝试导入库 ---
try:
    import yfinance as yf
except ImportError:
    print("错误：未找到 yfinance 库。请运行: pip install yfinance")
    sys.exit()
try:
    import akshare as ak
except ImportError:
    print("错误：未找到 akshare 库。请运行: pip install akshare")
    sys.exit()

warnings.filterwarnings('ignore') # 忽略一些 akshare 可能产生的警告

print("--- 正在尝试直接获取多变量外部数据... ---")

# --- 0. 设置参数 ---
# 从您的本地数据确定日期范围
# (假设您已加载 ts_orig = df['ClosePrice'])
try:
    # 假设 ts_orig 存在于您的环境中
    master_index = ts_orig.index
    start_date_ak = master_index.min().strftime("%Y%m%d") 
    start_date_yf = master_index.min().strftime("%Y-%m-%d")
    end_date_yf = master_index.max().strftime("%Y-%m-%d") # yfinance 需要结束日期
except NameError:
     print("错误：请先确保 'ts_orig' (沪深300收盘价Series) 已加载。")
     sys.exit()

# 用于存储获取的数据
data_store = {}

# --- 1. 获取全球市场数据 (使用 yfinance) ---
# (yfinance 相对稳定，且包含汇率)
yf_tickers = {
    "^GSPC": "SPX",     # 标普 500
    "^VIX": "VIX",      # 美国 VIX
    "USDCNH=X": "USD_CNH" # 美元/离岸人民币 (比 USDCNY=X 数据更全)
}
print(f"\n--- 正在使用 yfinance 获取 {list(yf_tickers.keys())} ---")
try:
    # 设置延迟，降低被限制的风险
    time.sleep(2) 
    yf_data = yf.download(list(yf_tickers.keys()), start=start_date_yf, end=end_date_yf)
    
    if yf_data.empty or yf_data['Close'].isnull().all().all():
        raise ValueError("Yfinance 返回了空数据或全是 NaN。")
        
    for ticker, name in yf_tickers.items():
        # yfinance 返回 MultiIndex 列名，需要处理
        if ('Close', ticker) in yf_data.columns:
             data_store[name] = yf_data[('Close', ticker)].rename(name)
             print(f"成功获取: {name}")
        elif ticker in yf_data['Close'].columns: # 有时层级不同
             data_store[name] = yf_data['Close'][ticker].rename(name)
             print(f"成功获取: {name}")
        else:
             print(f"警告: 在 yfinance 返回数据中未找到 {ticker} ('Close')")

except Exception as e:
    print(f"!!! 获取 yfinance 数据时出错: {e} !!!")
    print("这可能是暂时的速率限制。如果持续失败，请考虑手动下载。")


# --- 2. 获取中国市场/宏观数据 (使用 akshare) ---
print(f"\n--- 正在使用 akshare 获取 iVIX, PMI, LPR, M2 ---")

# 2.1 中国 VIX ("iVIX")
try:
    # 尝试最新的函数名 idx_option_risk_indicator_sse 或 option_sse_risk_indicator
    try:
        df_ivix = ak.idx_option_risk_indicator_sse(symbol="iVIX")
    except AttributeError:
        df_ivix = ak.option_sse_risk_indicator(symbol="iVIX") # 备用函数名
        
    df_ivix = df_ivix[['trade_date', 'close']].rename(columns={
        'trade_date': 'date', 'close': 'iVIX'
    })
    df_ivix['date'] = pd.to_datetime(df_ivix['date'])
    df_ivix = df_ivix.set_index('date')
    data_store['iVIX'] = df_ivix['iVIX']
    print("成功获取: 中国 VIX (iVIX)")
except Exception as e:
    print(f"获取 iVIX 失败: {e}")

# 2.2 官方制造业 PMI (月度)
try:
    df_pmi = ak.macro_china_pmi() 
    # (修正列名) 使用 akshare 返回的实际列名
    pmi_col_name = '制造业采购经理指数' if '制造业采购经理指数' in df_pmi.columns else 'pmi_mfg' # 兼容不同版本
    if pmi_col_name not in df_pmi.columns:
        raise KeyError(f"在 PMI 数据中未找到预期的列名 ('制造业采购经理指数' 或 'pmi_mfg')")
        
    df_pmi = df_pmi[['日期', pmi_col_name]].rename(columns={
        '日期': 'date', pmi_col_name: 'PMI'
    })
    # akshare 返回 "YYYY-MM" 格式, 转为月初日期
    df_pmi['date'] = pd.to_datetime(df_pmi['date'], format="%Y-%m") + pd.offsets.MonthBegin(0)
    df_pmi['PMI'] = pd.to_numeric(df_pmi['PMI'])
    df_pmi = df_pmi.set_index('date')
    data_store['PMI'] = df_pmi['PMI']
    print("成功获取: 制造业 PMI (月度)")
except Exception as e:
    print(f"获取 PMI 失败: {e}")

# 2.3 LPR 利率 (月度)
try:
    df_lpr = ak.macro_china_lpr()
    df_lpr = df_lpr[['trade_date', 'LPR_1Y']].rename(columns={ 'trade_date': 'date'})
    df_lpr['date'] = pd.to_datetime(df_lpr['date'])
    df_lpr = df_lpr.set_index('date')
    data_store['LPR_1Y'] = df_lpr['LPR_1Y']
    print("成功获取: LPR 1年期利率 (月度)")
except Exception as e:
    print(f"获取 LPR 失败: {e}")

# 2.4 M2 货币供应量同比 (月度)
try:
    df_m2 = ak.macro_china_money_supply()
    # (修正列名) 使用实际列名
    m2_col_name = '货币和准货币(M2)同比增长(%)' if '货币和准货币(M2)同比增长(%)' in df_m2.columns else 'm2_yoy'
    if m2_col_name not in df_m2.columns:
         raise KeyError(f"在 M2 数据中未找到预期的列名 ('货币和准货币(M2)同比增长(%)' 或 'm2_yoy')")

    df_m2 = df_m2[['月份', m2_col_name]].rename(columns={
        '月份': 'date', m2_col_name: 'M2_YoY'
    })
    df_m2['date'] = pd.to_datetime(df_m2['date'], format="%Y%m") + pd.offsets.MonthBegin(0)
    df_m2['M2_YoY'] = pd.to_numeric(df_m2['M2_YoY'])
    df_m2 = df_m2.set_index('date')
    data_store['M2_YoY'] = df_m2['M2_YoY']
    print("成功获取: M2 同比增速 (月度)")
except Exception as e:
    print(f"获取 M2 失败: {e}")


# --- 3. 合并与处理数据 ---
print("\n--- 正在合并、对齐和处理数据... ---")

if not data_store:
    print("错误：未能成功获取任何外部数据。无法继续。")
    sys.exit()

# 3.1 准备主 DataFrame
df_features = pd.DataFrame(index=master_index)
df_features['ClosePrice'] = ts_orig # 目标变量 (Y)

# 添加本地成交量 (如果您有的话)
if 'Volume' in df.columns:
    df_features['Volume'] = df['Volume']
    print("已添加本地 Volume 数据。")

# 3.2 合并所有获取的数据
# 使用 .join() 逐个合并，避免索引类型冲突
for name, series in data_store.items():
    if series is not None and not series.empty:
        # 确保索引是 DatetimeIndex
        if not isinstance(series.index, pd.DatetimeIndex):
             try:
                 series.index = pd.to_datetime(series.index)
             except Exception as e_idx:
                 print(f"警告：无法将 {name} 的索引转换为 DatetimeIndex: {e_idx}")
                 continue
        # 使用 left join 合并到 df_features
        df_features = df_features.join(series, how='left')
        print(f"已合并: {name}")
    else:
        print(f"跳过空的或无效的数据: {name}")

print(f"合并后形状 (对齐A股交易日): {df_features.shape}")

# 3.3 填充月度和日度数据 (ffill)
fill_cols = ['PMI', 'LPR_1Y', 'M2_YoY', 'SPX', 'VIX', 'USD_CNH', 'iVIX', 'Volume']
for col in fill_cols:
    if col in df_features.columns:
        df_features[col] = df_features[col].fillna(method='ffill')
print("已填充 (ffill) 宏观和全球数据。")

# 3.4 (关键!) 应用滞后 (Lag)
exog_cols = [col for col in df_features.columns if col != 'ClosePrice']
for col in exog_cols:
    if col in df_features.columns:
        df_features[col] = df_features[col].shift(1)
print("已对所有外部变量应用 shift(1) 滞后处理。")

# 3.5 清理数据
# (先用 bfill 填充开头的 NaN, 再用 dropna 清理无法填充的行)
df_features = df_features.fillna(method='bfill')
df_features = df_features.dropna(subset=['ClosePrice']) # 确保目标列有效

# 检查是否有列几乎全是 NaN (如果 API 失败或数据缺失)
cols_mostly_nan = df_features.columns[df_features.isnull().mean() > 0.9].tolist()
if cols_mostly_nan:
    print(f"\n*** 警告: 以下列数据缺失严重，可能无法使用: {cols_mostly_nan} ***")
    # (您可以选择在这里 dropna(axis=1) 删除这些列)
    # df_features = df_features.drop(columns=cols_mostly_nan)

# 最终清理，删除任何仍然包含 NaN 的行
df_features = df_features.dropna()

print("\n--- 多变量数据准备完毕 ---")
print(f"最终特征矩阵形状: {df_features.shape}")

if df_features.empty:
    print("错误：最终 DataFrame 为空，可能是数据获取或处理失败。")
else:
    print("\n--- df_features.head() ---")
    print(df_features.head())
    print("\n--- df_features.tail() ---")
    print(df_features.tail())

    # --- (可选) 保存到文件 ---
    # output_file = "multivariate_data_programmatic.csv"
    # df_features.to_csv(output_file)
    # print(f"\n数据已保存到 {output_file}")