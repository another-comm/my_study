import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import itertools
from statsmodels.tsa.stattools import adfuller, grangercausalitytests, kpss
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen
from statsmodels.stats.diagnostic import acorr_ljungbox
from arch import arch_model
from scipy.stats import t
import warnings

warnings.filterwarnings("ignore")
plt.rcParams['font.sans-serif'] = ['SimHei'] # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False # 用来正常显示负号

# --- 1. 数据导入和预处理 ---
file_name = r"C:\study\时间序列分析\结课作业\data.xlsx"
df = pd.read_excel(file_name)
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
df.sort_index(inplace=True)
df_prices = df[['btc_close', 'eth_close']].copy().dropna()

print("数据加载成功，预处理完成。")
print("数据概览:")
print(df_prices.head())
print("\n数据信息:")
df_prices.info()

# --- 2. 数据基本统计分析 ---
print("\n--- 2. 描述性统计 ---")
print(df_prices.describe())

# 绘制价格时序图
print("正在显示图1: 原始价格时序图 (BTC vs ETH)...")
df_prices.plot(subplots=True, figsize=(10, 8))
plt.suptitle('图1: 原始价格时序图 (BTC vs ETH)')
plt.show()

# 计算对数收益率
df_returns = np.log(df_prices).diff().dropna()
df_returns.columns = ['btc_log_return', 'eth_log_return']

print("正在显示图2: 对数收益率时序图 (BTC vs ETH)...")
df_returns.plot(subplots=True, figsize=(10, 8))
plt.suptitle('图2: 对数收益率时序图 (BTC vs ETH)')
plt.show()

# 绘制对数收益率直方图
print("正在显示图3: 对数收益率分布直方图...")
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
sns.histplot(df_returns['btc_log_return'], kde=True, bins=30)
plt.title('BTC 对数收益率分布')
plt.subplot(1, 2, 2)
sns.histplot(df_returns['eth_log_return'], kde=True, bins=30)
plt.title('ETH 对数收益率分布')
plt.suptitle('图3: 对数收益率分布直方图')
plt.show()

# --- 改进 1: 检验尖峰厚尾 (Skewness, Kurtosis) 和 Q-Q 图 ---
print("\n--- 2.1 收益率分布检验 (尖峰厚尾) ---")
print(f"BTC 收益率 偏度 (Skewness): {df_returns['btc_log_return'].skew():.4f} (正态=0)")
print(f"BTC 收益率 峰度 (Kurtosis): {df_returns['btc_log_return'].kurtosis():.4f} (正态=0, 金融>0)")
print(f"ETH 收益率 偏度 (Skewness): {df_returns['eth_log_return'].skew():.4f}")
print(f"ETH 收益率 峰度 (Kurtosis): {df_returns['eth_log_return'].kurtosis():.4f}")

print("\n正在显示图3.1: 收益率 Q-Q 图 (对比正态分布)...")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sm.qqplot(df_returns['btc_log_return'].dropna(), line='s', ax=axes[0])
axes[0].set_title('BTC 收益率 Q-Q 图')
sm.qqplot(df_returns['eth_log_return'].dropna(), line='s', ax=axes[1])
axes[1].set_title('ETH 收益率 Q-Q 图')
plt.suptitle('图3.1: Q-Q 图 (证明尖峰厚尾特性)')
plt.show()


# --- 3. 平稳性检验和白噪声检验 ---
print("\n--- 3. 平稳性检验 (ADF) 与白噪声检验 ---")

# --- 检验函数定义 ---

# ADF 检验
def run_adf_test(series, name):
    """
    ADF 检验
    H0 (原假设): 序列存在单位根 (非平稳)
    """
    result = adfuller(series)
    print(f'序列 "{name}" 的 ADF 检验 (H0: 存在单位根):')
    print(f'  ADF 统计量: {result[0]:.4f}, p-value: {result[1]:.4e}')
    if result[1] > 0.05:
        print(f'  结论: 序列非平稳 (p > 0.05)')
    else:
        print(f'  结论: 序列平稳 (p <= 0.05)')
    return result[1]

# 白噪声检验 (Ljung-Box)
def run_ljung_box_test(series, name, lags=10):
    """
    Ljung-Box 白噪声检验
    H0 (原假设): 序列是白噪声 (即序列值彼此独立, 无自相关)
    """
    # Ljung-Box test
    result_df = acorr_ljungbox(series, lags=[lags], return_df=True)
    p_value = result_df.iloc[0]['lb_pvalue']
    print(f'序列 "{name}" 的 Ljung-Box 白噪声检验 (H0: 序列为白噪声):')
    print(f'  L-B 统计量 (lag={lags}): {result_df.iloc[0]["lb_stat"]:.4f}, p-value: {p_value:.4e}')
    
    if p_value <= 0.05:
        print(f'  结论: 序列存在自相关 (非白噪声, 可建模) (p <= 0.05)')
    else:
        print(f'  结论: 序列为白噪声 (无信息) (p > 0.05)')
    return p_value

# --- 3.1 原始价格检验 ---
print("\n--- 3.1 原始价格平稳性检验 (预期: 非平稳) ---")
p_btc_price_adf = run_adf_test(df_prices['btc_close'], 'BTC 价格')
print("---")
p_eth_price_adf = run_adf_test(df_prices['eth_close'], 'ETH 价格')

# --- 3.2 对数收益率检验 ---
print("\n--- 3.2 对数收益率平稳性与白噪声检验 (预期: 平稳, 非白噪声) ---")
p_btc_return_adf = run_adf_test(df_returns['btc_log_return'], 'BTC 对数收益率')
p_btc_return_lb = run_ljung_box_test(df_returns['btc_log_return'], 'BTC 对数收益率')

print("---")
p_eth_return_adf = run_adf_test(df_returns['eth_log_return'], 'ETH 对数收益率')
p_eth_return_lb = run_ljung_box_test(df_returns['eth_log_return'], 'ETH 对数收益率')

# --- 4. 一元时间序列模型 (ARIMA & GARCH) ---
print("\n--- 4. 一元时间序列模型 (ARIMA & 升级版 GARCH) ---")

if True:
    # --- 自动寻优的函数 (遍历 p,q) ---
    def auto_arima_select(ts, d=0, max_p=3, max_q=3):
        best_aic = np.inf
        best_bic = np.inf
        best_aic_res = None
        best_bic_res = None
        best_aic_order = None
        best_bic_order = None
        
        for p in range(max_p + 1):
            for q in range(max_q + 1):
                # 增加 (0,0,0) 的跳过，因为 GARCH 会处理 const
                if p == 0 and q == 0:
                    continue
                try:
                    model = ARIMA(ts, order=(p, d, q))
                    res = model.fit()
                    if res.aic < best_aic:
                        best_aic = res.aic
                        best_aic_res = res
                        best_aic_order = (p, d, q)
                    if res.bic < best_bic:
                        best_bic = res.bic
                        best_bic_res = res
                        best_bic_order = (p, d, q)
                except Exception as e:
                    continue
        return {
            'best_aic_order': best_aic_order,
            'best_bic_order': best_bic_order,
            'best_aic_result': best_aic_res,
            'best_bic_result': best_bic_res
        }
    
    # --- 残差诊断与显著性检验函数 ---
    def arima_diagnostics(result, series_name="Series", lb_lags=[10, 20]):
        print(f"\n--- {series_name} ARIMA 模型摘要 ---")
        print(result.summary())
        
        print(f"\n{series_name} 参数显著性 (p-values):")
        pvals = result.pvalues
        for name, pval in pvals.items():
            print(f"  {name:20s} p = {pval:.6f} -> {'显著' if pval < 0.05 else '不显著'}")
        
        print(f"\n{series_name} 残差 Ljung-Box 检验 (lags = {lb_lags}):")
        for lag in lb_lags:
            try:
                # 使用 statsmodels 0.13+ 的 acorr_ljungbox 格式
                lb = acorr_ljungbox(result.resid, lags=[lag], return_df=True)
                pvalue = lb['lb_pvalue'].iloc[0]
                print(f"  lag={lag} -> lb_stat={lb['lb_stat'].iloc[0]:.4f}, p={pvalue:.6f} -> {'通过(白噪声)' if pvalue>0.05 else '未通过(非白噪声)'}")
            except Exception as e:
                print(f"  lag={lag} 检验失败: {e}")
        
        # 残差绘图
        resid = result.resid
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        axes[0, 0].plot(resid); axes[0, 0].set_title(f"{series_name} 残差时序")
        plot_acf(resid, lags=30, ax=axes[0, 1]); axes[0, 1].set_title(f"{series_name} 残差 ACF")
        plot_pacf(resid, lags=30, ax=axes[1, 0]); axes[1, 0].set_title(f"{series_name} 残差 PACF")
        sm.qqplot(resid, line='s', ax=axes[1, 1]); axes[1, 1].set_title(f"{series_name} 残差 Q-Q 图")
        plt.suptitle(f"{series_name} ARIMA 残差诊断")
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()
    
    # ========== 4.1 BTC ARIMA ==========
    print("\n--- 4.1 BTC 对数收益率 ARIMA 自动寻优 (基于 AIC/BIC) ---")
    # 确保 df_returns 存在 (在 Section 2 中创建)
    btc_res = auto_arima_select(df_returns['btc_log_return'], d=0, max_p=3, max_q=3)
    print(f"BTC 最优 AIC 阶数: {btc_res['best_aic_order']}")
    print(f"BTC 最优 BIC 阶数: {btc_res['best_bic_order']}")
    if btc_res['best_aic_result'] is not None:
        arima_result = btc_res['best_aic_result'] # 用于预测
        arima_diagnostics(arima_result, series_name="BTC 对数收益率")
    else:
        print("警告: 未能找到可拟合的 BTC ARIMA 模型。")

# --- 4.3 GARCH(1,1)-t 模型 (BTC 对数收益率) ---
print("\n--- 4.3 GARCH(1,1) 模型 (BTC 对数收益率) ---")

try:
    garch_model_btc = arch_model(df_returns['btc_log_return'].dropna() * 100, 
                                 vol='Garch', p=1, o=0, q=1, dist='t')
    garch_result_btc = garch_model_btc.fit(update_freq=5, disp='off')
    print("\nBTC GARCH(1,1)-t 模型摘要:")
    print(garch_result_btc.summary())
    print("正在显示图5: BTC GARCH(1,1)-t 标准化残差...")
    garch_std_resid_btc = garch_result_btc.resid / garch_result_btc.conditional_volatility
    plt.figure(figsize=(10, 4))
    plt.plot(garch_std_resid_btc)
    plt.title('图5: BTC GARCH(1,1)-t 标准化残差')
    plt.show()

except Exception as e:
    print(f"GARCH(1,1) 拟合失败: {e}")

# --- 4.4 ARIMA-GARCH 联合模型 (样本内拟合与样本外预测) ---
print("\n--- 4.4 ARIMA-GARCH 联合模型 (样本内拟合与样本外预测) ---")

if 'arima_result' in locals() and 'garch_result_btc' in locals() and 'df_prices' in locals():
    try:
        last_price = df_prices['btc_close'].iloc[-1]
        last_date = df_prices.index[-1]
        forecast_horizon = 10
        nu = garch_result_btc.params['nu']
        t_critical = t.ppf(0.975, nu)

        # --- 样本内拟合 ---
        in_sample_mu = arima_result.fittedvalues
        prev_actual_prices = df_prices['btc_close'].shift(1)
        in_sample_fitted_prices = prev_actual_prices * np.exp(in_sample_mu)
        
        in_sample_vol = garch_result_btc.conditional_volatility / 100
        in_sample_upper = prev_actual_prices * np.exp(in_sample_mu + t_critical * in_sample_vol)
        in_sample_lower = prev_actual_prices * np.exp(in_sample_mu - t_critical * in_sample_vol)

        # --- 样本外预测 ---
        arima_forecast = arima_result.get_forecast(steps=forecast_horizon)
        pred_returns = arima_forecast.predicted_mean
        garch_forecast = garch_result_btc.forecast(horizon=forecast_horizon, reindex=False)
        pred_volatility = np.sqrt(garch_forecast.variance.iloc[-1].values) / 100

        cum_pred_returns = np.cumsum(pred_returns)
        cum_pred_volatility = np.sqrt(np.cumsum(pred_volatility**2))

        pred_prices = last_price * np.exp(cum_pred_returns)
        upper_prices = last_price * np.exp(cum_pred_returns + t_critical * cum_pred_volatility)
        lower_prices = last_price * np.exp(cum_pred_returns - t_critical * cum_pred_volatility)

        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_horizon, freq='D')
        price_forecast_df = pd.DataFrame({
            'Predicted_Price': pred_prices,
            'Lower_Price_95': lower_prices,
            'Upper_Price_95': upper_prices
        }, index=future_dates)

        print(f"\n未来 {forecast_horizon} 天预测结果:")
        print(price_forecast_df)

        # --- 绘图 1: 全历史 ---
        print(f"正在显示图5.4: 全历史样本内拟合与样本外预测...")
        plt.figure(figsize=(14, 7))
        plt.plot(df_prices.index, df_prices['btc_close'], color='blue', alpha=0.5, label='历史真实价格')
        plt.plot(in_sample_fitted_prices.index, in_sample_fitted_prices, color='green', linestyle='--', alpha=0.8, linewidth=1, label='样本内拟合价格')
        plt.plot(future_dates, price_forecast_df['Predicted_Price'], color='red', marker='o', markersize=4, label='未来预测价格')
        plt.fill_between(future_dates, price_forecast_df['Lower_Price_95'], price_forecast_df['Upper_Price_95'], color='red', alpha=0.15, label='未来 95% 置信区间')

        plt.title(f'图5.4: BTC 价格全历史样本内拟合与未来 {forecast_horizon} 天预测')
        plt.xlabel('日期')
        plt.ylabel('BTC 价格 (USD)')
        plt.legend(loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        # --- 绘图 2: 局部放大 (2025-09-01 至今) ---
        print(f"正在显示图5.5: 局部样本内拟合与样本外预测 (2025年9月至今)...")
        start_date_zoom = '2025-09-01'
        df_zoom = df_prices[start_date_zoom:]
        fitted_zoom = in_sample_fitted_prices[start_date_zoom:]
        lower_zoom = in_sample_lower[start_date_zoom:]
        upper_zoom = in_sample_upper[start_date_zoom:]

        if not df_zoom.empty:
            plt.figure(figsize=(14, 7))
            plt.plot(df_zoom.index, df_zoom['btc_close'], color='blue', marker='.', linestyle='-', linewidth=2, alpha=0.6, label='真实价格')
            plt.plot(fitted_zoom.index, fitted_zoom, color='green', linestyle='--', linewidth=2.5, alpha=0.9, label='拟合价格')
            plt.fill_between(fitted_zoom.index, lower_zoom, upper_zoom, color='green', alpha=0.1, label='历史 95% 置信区间')
            plt.plot(future_dates, price_forecast_df['Predicted_Price'], color='red', marker='o', markersize=6, linewidth=2, label='未来预测')
            plt.fill_between(future_dates, price_forecast_df['Lower_Price_95'], price_forecast_df['Upper_Price_95'], color='red', alpha=0.25, label='未来 95% 置信区间')
            
            plt.title(f'图5.5: 局部样本内拟合 (带历史置信区间) 与未来预测')
            plt.xlabel('日期')
            plt.ylabel('BTC 价格 (USD)')
            plt.legend(loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.xticks(rotation=45)
            plt.show()
        else:
            print(f"警告: 数据中没有 {start_date_zoom} 之后的数据。")

    except Exception as e:
        print(f"模型拟合与预测失败: {e}")
else:
    print(f"错误: 缺少必要模型或数据。")

# --- 5. 多元时间序列分析 (VECM/VAR) ---
print("\n--- 5. 多元时间序列分析 (VECM / VAR) ---")

if 'df_prices' in locals() and 'df_returns' in locals():
    
    # --- 5.1 确定最优滞后阶数 ---
    print("\n--- 5.1 确定最优滞后阶数 (Lag Selection) ---")
    
    # A. VAR(df_returns) 滞后阶数
    model_returns = VAR(df_returns)
    lag_selection_returns = model_returns.select_order(maxlags=10)
    optimal_lag_returns = lag_selection_returns.aic
    print(f"VAR(df_returns) 最优滞后 (AIC): {optimal_lag_returns}")

    # B. VAR(df_prices) 滞后阶数
    model_prices = VAR(df_prices)
    lag_selection_prices = model_prices.select_order(maxlags=10)
    optimal_lag_prices = lag_selection_prices.aic
    print(f"VAR(df_prices) 最优滞后 (AIC): {optimal_lag_prices}")

    # --- 5.2 协整检验 (Johansen Test) ---
    print("\n--- 5.2 协整检验 (Johansen Test) ---")
    
    k_ar_diff = optimal_lag_prices - 1 
    if k_ar_diff < 0: k_ar_diff = 0 
    
    print(f"检验 'df_prices' (k_ar_diff = {k_ar_diff})")

    johansen_result = coint_johansen(df_prices, det_order=1, k_ar_diff=k_ar_diff)
    
    print("\n迹统计量 (Trace Statistic):")
    # H0: r=0
    print(f"  H0: r=0  (Trace Stat: {johansen_result.lr1[0]:.4f}, 95% Crit: {johansen_result.cvt[0, 1]:.4f})")
    # H0: r<=1
    print(f"  H0: r<=1 (Trace Stat: {johansen_result.lr1[1]:.4f}, 95% Crit: {johansen_result.cvt[1, 1]:.4f})")

    # --- 5.3 格兰杰因果检验 (Granger Causality Test) ---
    print("\n--- 5.3 格兰杰因果检验 (Granger Causality Test) ---")
    print(f"检验 'df_returns' (maxlag = {optimal_lag_returns})")

    # 检验 1: ETH 是否是 BTC 的格兰杰原因
    gc_result_eth_to_btc = grangercausalitytests(
        df_returns[['btc_log_return', 'eth_log_return']], 
        maxlag=optimal_lag_returns, 
        verbose=False
    )
    f_test_p_value_1 = gc_result_eth_to_btc[optimal_lag_returns][0]['ssr_ftest'][1]
    print(f"\nH0: ETH -/-> BTC (p-value): {f_test_p_value_1:.6f}")

    # 检验 2: BTC 是否是 ETH 的格兰杰原因
    gc_result_btc_to_eth = grangercausalitytests(
        df_returns[['eth_log_return', 'btc_log_return']], 
        maxlag=optimal_lag_returns, 
        verbose=False
    )
    f_test_p_value_2 = gc_result_btc_to_eth[optimal_lag_returns][0]['ssr_ftest'][1]
    print(f"\nH0: BTC -/-> ETH (p-value): {f_test_p_value_2:.6f}")
            
    # --- 5.4 拟合 VAR 模型 ---
    print("\n--- 5.4 拟合 VAR 模型 (在收益率上) ---")
    
    if 'df_returns' in locals() and 'optimal_lag_returns' in locals():
        try:
            # 1. 创建 VAR 模型实例
            model_var = VAR(df_returns)
            
            # 2. 拟合模型，使用之前确定的最优滞后阶数 (10)
            print(f"正在拟合 VAR({optimal_lag_returns}) 模型...")
            var_result = model_var.fit(optimal_lag_returns)
            
            # 3. 输出模型摘要
            print("\nVAR 模型摘要:")
            print(var_result.summary())

            # 4. 检查模型的稳定性 (根是否在单位圆内)
            print("\nVAR 模型稳定性检查 (所有根的模应 < 1):")
            is_stable = var_result.is_stable()
            print(f"模型是否稳定: {is_stable}")

        except Exception as e:
            print(f"VAR 模型拟合失败: {e}")
    else:
        print("错误: 缺少必要变量，无法拟合 VAR 模型。")
        
    # --- 5.5 脉冲响应分析 (IRF) ---
    print("\n--- 5.5 脉冲响应分析 (Impulse Response Analysis) ---")
    
    if 'var_result' in locals():
        try:
            # 设定分析的期数 (例如未来 20 天)
            irf_periods = 20

            irf = var_result.irf(irf_periods)
            
            print(f"正在显示图6: 正交化脉冲响应函数 (未来 {irf_periods} 期)...")
            plt.figure(figsize=(12, 8))
            # orth=True 表示使用正交化冲击
            irf.plot(orth=True, impulse='btc_log_return', response='eth_log_return', signif=0.05, subplot_params={'title': 'BTC 冲击 -> ETH 响应'})
            plt.show() 
            
            plt.figure(figsize=(12, 8))
            irf.plot(orth=True, impulse='eth_log_return', response='btc_log_return', signif=0.05, subplot_params={'title': 'ETH 冲击 -> BTC 响应'})
            plt.show()

            irf.plot(orth=True, signif=0.05, figsize=(12, 10))
            plt.suptitle('图6: VAR(10) 正交化脉冲响应分析 (95% 置信区间)')
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.show()

        except Exception as e:
            print(f"脉冲响应分析失败: {e}")
    else:
        print("错误: 缺少 VAR 模型结果 (var_result)，无法进行 IRF 分析。")
        
    # --- 5.6 方差分解分析 (FEVD) ---
    print("\n--- 5.6 方差分解分析 (Variance Decomposition) ---")
    
    if 'var_result' in locals():
        try:
            # 设定分析期数 (例如未来 10 天)
            fevd_periods = 10
            
            # 计算方差分解
            fevd = var_result.fevd(fevd_periods)
            print(f"\n方差分解结果 (未来 {fevd_periods} 天):")
            print(fevd.summary())
            print(f"正在显示图7: 方差分解堆叠图...")
            # 绘制方差分解图
            fevd.plot(figsize=(12, 8))
            plt.suptitle(f'图7: VAR(10) 方差分解 (未来 {fevd_periods} 天)')
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.show()

        except Exception as e:
            print(f"方差分解分析失败: {e}")
    else:
        print("错误: 缺少 VAR 模型结果 (var_result)，无法进行 FEVD 分析。")

else:
    print("错误: 缺少 'df_prices' 或 'df_returns' DataFrame，跳过多维分析。")

# --- 6. 风险价值 (VaR) 计算与回测 ---
print("\n--- 6. 风险价值 (VaR) 计算与回测 (基于 GARCH-t 模型) ---")

if 'garch_result_btc' in locals():
    try:
        # 1. 获取模型参数
        garch_params = garch_result_btc.params
        mu = garch_params['mu']
        nu = garch_params['nu'] # t分布自由度
        
        # 2. 获取条件波动率 (Conditional Volatility)
        conditional_volatility = garch_result_btc.conditional_volatility
        # 3. 计算 95% VaR (alpha = 0.05)
        alpha = 0.05
        # t.ppf 是 t 分布的百分位点函数 (逆累积分布函数)
        q_t = t.ppf(alpha, nu)
        var_95 = (mu + conditional_volatility * q_t) / 100
        # 4. 创建用于绘图的 DataFrame
        var_df = pd.DataFrame({
            'Actual_Return': df_returns['btc_log_return'],
            'VaR_95': var_95
        }, index=df_returns.index).dropna()
        # 5. 绘制 VaR 回测图
        print("正在显示图8: BTC 每日收益率与 95% VaR 对比图...")
        plt.figure(figsize=(12, 6))
        plt.plot(var_df.index, var_df['Actual_Return'], color='blue', alpha=0.5, label='实际收益率')
        plt.plot(var_df.index, var_df['VaR_95'], color='red', linewidth=2, label='95% VaR (GARCH-t)')
        plt.title('图8: BTC 每日收益率 vs. 95% 动态风险价值 (VaR)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()
        
        # 6. 计算 VaR 突破次数 (Backtesting)
        exceptions = var_df[var_df['Actual_Return'] < var_df['VaR_95']]
        num_exceptions = len(exceptions)
        total_obs = len(var_df)
        actual_alpha = num_exceptions / total_obs
        
        print(f"\nVaR 回测结果 (95% 置信水平, 理论突破率应接近 5%):")
        print(f"  总观测天数: {total_obs}")
        print(f"  实际突破次数: {num_exceptions}")
        print(f"  实际突破率: {actual_alpha:.2%}")
        if abs(actual_alpha - 0.05) < 0.01: # 简单判断，实际应做 Kupiec 检验
            print("  -> 模型表现良好 (实际突破率接近理论值 5%)")
        else:
            print("  -> 模型可能需要改进 (实际突破率偏离理论值)")

        # 7. 预测下一交易日的 VaR
        forecast = garch_result_btc.forecast(horizon=1)
        next_vol = np.sqrt(forecast.variance.iloc[-1, 0])
        next_var_95 = (mu + next_vol * q_t) / 100
        
        print(f"\n未来一日风险预测:")
        print(f"  下一交易日 95% VaR: {next_var_95:.4%}")
        print(f"  (解读: 有 95% 的把握，明天 BTC 的损失不会超过 {abs(next_var_95):.2%})")

    except Exception as e:
        print(f"VaR 计算失败: {e}")
else:
    print("错误: 缺少 GARCH 模型结果 (garch_result_btc)，无法计算 VaR。")