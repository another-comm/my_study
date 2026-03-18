import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# ----------------- 配置 -----------------
# 目标加密货币的 CoinGecko ID 和对应的代号
coin_ids = {
    'BTC/USD': 'bitcoin',
    'ETH/USD': 'ethereum',
    'SOL/USD': 'solana',
    'BNB/USD': 'binancecoin',
    'DOGE/USD': 'dogecoin',
    'XRP/USD': 'ripple' 
}
base_currency = 'usd'
days = 370 # 获取过去 370 天的数据

all_data = {}
successful_symbols = []

print(f"开始获取数据 (使用 CoinGecko 公共 API)...")

for symbol, coin_id in coin_ids.items():
    print(f"\n  正在通过 CoinGecko API 获取 {symbol} 的数据...")
    
    # CoinGecko 的 API 接口：days=365 表示获取 365 天的历史日线数据
    # interval=daily 确保获取日线数据
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency={base_currency}&days={days}&interval=daily"
    
    try:
        # 发送 GET 请求
        response = requests.get(url, timeout=30)
        response.raise_for_status() # 如果状态码不是 200，则抛出异常
        data = response.json()
        
        # 提取价格数据 (prices 键下是 [timestamp, price] 列表)
        prices = data.get('prices')
        
        if prices and len(prices) >= 200:
            # 转换为 DataFrame
            df = pd.DataFrame(prices, columns=['timestamp', 'close'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            all_data[symbol] = df[['close']].rename(columns={'close': symbol})
            successful_symbols.append(symbol)
            print(f"  {symbol} 数据获取成功。共 {len(df)} 条记录。")
            
        else:
            print(f"  警告: {symbol} 数据量不足或 API 未返回价格数据。")
            
    except requests.exceptions.HTTPError as errh:
        print(f"  获取 {symbol} 失败 (HTTP 错误): {errh}. (可能是速率限制)")
    except requests.exceptions.RequestException as err:
        print(f"  获取 {symbol} 失败 (网络错误): {err}. (可能是连接超时)")
        
    # 🚨 遵守 CoinGecko 免费公共 API 的速率限制
    time.sleep(2) 

if all_data:
    # 将所有币种的收盘价合并到一个 DataFrame 中
    combined_df = pd.DataFrame({symbol: all_data[symbol][symbol] for symbol in successful_symbols})
    file_name = 'crypto_prices_1year_daily_coingecko_request.csv'
    combined_df.to_csv(file_name)
    print(f"\n--- 恭喜！数据获取成功 ---")
    print(f"成功获取的币种: {', '.join(successful_symbols)}")
    print(f"数据已保存到文件: {file_name}")
else:
    print("\n抱歉，所有自动化尝试均已失败。请使用手动下载 CoinGecko/Yahoo Finance CSV 的方法。")