import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, arma_order_select_ic
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.arima.model import ARIMA
from arch import arch_model
from statsmodels.tsa.holtwinters import Holt
import warnings
from sklearn.metrics import r2_score, mean_squared_error

# 设置Matplotlib以正确显示中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # 'SimHei' 是黑体
plt.rcParams['axes.unicode_minus'] = False    # 正确显示负号

# === 1. 加载数据 ===
file_path = r"C:\study\时间序列分析\小组作业\CSI300_Tencent_2020_to_today.csv"

try:
    df_full = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
except FileNotFoundError:
    print(f"错误：文件未找到，请检查路径是否正确：{file_path}")
    exit()

df = df_full[df_full.index >= pd.Timestamp("2022-01-01")].copy()
ts = df['ClosePrice']
print(f"数据加载成功，已筛选 2022-01-01 至今的数据，共 {len(ts)} 条记录。")


# === 2. 原始序列探索性分析 ===
# (此部分与您原始代码相同，为简洁起见，此处省略其打印输出)
# print("\n--- 2. 原始序列探索性分析 ---")
# ... (ADF Test, etc.)
adf_result_orig = adfuller(ts)
if adf_result_orig[1] > 0.05:
    print("\n原始序列非平稳。")
else:
    print("\n原始序列平稳。")


# === 3. 因素分解与残差建模 (T + S + R) ===
print("\n--- 3. 因素分解与残差建模 (T + S + R) ---")
print("模型结构: Y_t = T_t (趋势) + S_t (季节) + R_t (残差)")

# --- 3.1 长期趋势拟合 (二次多项式) ---
print("\n--- 3.1 长期趋势拟合 (T_t) ---")
t = np.arange(len(ts))
coeffs = np.polyfit(t, ts.values, 2)
slope_sq, slope_lin, intercept = coeffs
trend_series = pd.Series(np.polyval(coeffs, t), index=ts.index, name='Trend')
print(f"二次多项式趋势拟合: T_t = {slope_sq:.4f}*t^2 + {slope_lin:.4f}*t + {intercept:.4f}")

# 绘制趋势拟合图
plt.figure(figsize=(10, 5))
plt.plot(ts, label='原始观测值', alpha=0.6)
plt.plot(trend_series, label='二次多项式趋势 (T_t)', color='red', linewidth=2)
plt.title("沪深300指数与拟合的长期趋势 (T_t)")
plt.xlabel("日期"); plt.ylabel("指数点位"); plt.legend(); plt.grid(True); plt.tight_layout(); plt.show()

# --- 3.2 季节性因素拟合 (星期效应) ---
print("\n--- 3.2 季节性因素拟合 (S_t) ---")
# S_t + R_t = Y_t - T_t
residuals_from_trend = ts - trend_series
# 使用 "星期几" (Day of Week) 作为季节性
df_seasonal = pd.DataFrame({'DeTrended': residuals_from_trend, 'DayOfWeek': ts.index.dayofweek})
# 计算周一到周五的平均效应
seasonal_factors_dow = df_seasonal.groupby('DayOfWeek')['DeTrended'].mean()
# 调整季节因子，使其总和（或均值）为0
seasonal_factors_dow = seasonal_factors_dow - seasonal_factors_dow.mean()
# 将季节因子映射回时间序列
seasonal_series = pd.Series(ts.index.dayofweek.map(seasonal_factors_dow), index=ts.index, name='Seasonal')
print("已拟合星期效应 (S_t)，各天均值（调整后）:")
print(seasonal_factors_dow)

# --- 3.3 (新增) 因素分解图 ---
print("\n--- 3.3 绘制因素分解图 (T+S+R) ---")
# R_t = (Y_t - T_t) - S_t
residuals_final = residuals_from_trend - seasonal_series
residuals_final.name = 'Remainder'

plt.figure(figsize=(10, 8))
# 1. 观测值
plt.subplot(4, 1, 1)
plt.plot(ts, label='观测值 (Y_t)')
plt.legend(loc='upper left'); plt.title("因素分解", fontsize=14)
# 2. 趋势
plt.subplot(4, 1, 2)
plt.plot(trend_series, label='趋势 (T_t)', color='red')
plt.legend(loc='upper left')
# 3. 季节
plt.subplot(4, 1, 3)
plt.plot(seasonal_series, label='季节 (S_t)', color='green')
plt.legend(loc='upper left')
# 4. 残差
plt.subplot(4, 1, 4)
plt.plot(residuals_final, label='残差 (R_t)', color='purple', alpha=0.7)
plt.legend(loc='upper left'); plt.xlabel("日期")
plt.tight_layout(); plt.show()


# --- 3.4 短期残差均值建模 (ARIMA) ---
print("\n--- 3.4 短期残差均值建模 (R_t) ---")
ts_no_trend_seasonal = residuals_final.dropna()
print("已创建最终残差序列 (R_t) 用于ARIMA建模。")

if adfuller(ts_no_trend_seasonal)[1] <= 0.05:
    d_order_final = 0
    modeling_series_for_ic = ts_no_trend_seasonal
else:
    d_order_final = 1
    modeling_series_for_ic = ts_no_trend_seasonal.diff().dropna()

warnings.filterwarnings('ignore')
trend_param = 'n'

print("\n正在进行ARIMA自动定阶 (BIC)...")
order_res = arma_order_select_ic(modeling_series_for_ic, max_ar=3, max_ma=3, ic=["bic"], trend=trend_param)

# === 打印 BIC 结果表 ===
print("\n--- ARIMA 自动定阶 (BIC) 结果表 ---")
print(" (p=AR, q=MA)")
print(order_res.bic.to_string(float_format="%.4f"))
best_p, best_q = order_res.bic_min_order
best_order = (best_p, d_order_final, best_q)

print(f"\nBIC 准则推荐的最佳 (p, d, q) 阶数为: {best_order}")

arima_model_residuals = ARIMA(ts_no_trend_seasonal, order=best_order, trend='n').fit()

print(f"\n--- 已对残差序列 R_t 拟合 ARIMA{best_order} 模型 ---")
print(arima_model_residuals.summary())
residuals_from_arima = arima_model_residuals.resid
lb_test = acorr_ljungbox(residuals_from_arima, lags=10, return_df=True)
if lb_test['lb_pvalue'].min() > 0.05:
    print("\n结论：ARIMA模型的残差是白噪声 (ε_t)，均值模型(R_t)拟合良好。")
else:
    print("\n结论：ARIMA模型的残差不是白噪声，均值模型(R_t)可能不充分。")

# --- 3.5 短期残差方差建模 (GARCH) ---
print("\n--- 3.5 短期残差方差建模 (ε_t) ---")
print("对ARIMA模型的残差（ε_t）进行异方差检验...")

# ARCH-LM 检验
arch_test_result = het_arch(residuals_from_arima, nlags=5)
print(f'LM Statistic: {arch_test_result[0]}')
print(f'p-value: {arch_test_result[1]}')

garch_result = None # 初始化 garch_result

if arch_test_result[1] < 0.05:
    print("结论：p-value < 0.05，残差 ε_t 存在显著的ARCH效应。")
    print("=> 适合使用GARCH模型来刻画其波动聚集特征。")
    
    # === (新增) GARCH 优化 ===
    print("\n--- GARCH 模型优化 (BIC) ---")
    print("正在尝试 GARCH(p,q) 和 EGARCH(p,1,q) (p,q in [1,2])...")
    
    residuals_for_garch = residuals_from_arima # 使用 ARIMA 残差 ε_t
    best_bic = np.inf
    best_model_result = None
    best_model_name = ""
    
    # 定义要测试的p, q阶数
    p_orders = [1, 2]
    q_orders = [1, 2]
    
    # 存储所有模型的BIC
    bic_results = {}

    for p in p_orders:
        for q in q_orders:
            
            # --- 1. GARCH 模型 (对称) ---
            model_name_garch = f'GARCH({p},{q})-t'
            try:
                # 使用 't' 分布
                gm_garch = arch_model(residuals_for_garch, vol='Garch', p=p, q=q, mean='Zero', dist='t')
                res_garch = gm_garch.fit(disp='off', update_freq=0)
                bic_results[model_name_garch] = res_garch.bic
                
                if res_garch.bic < best_bic:
                    best_bic = res_garch.bic
                    best_model_result = res_garch
                    best_model_name = model_name_garch
                    
            except Exception as e:
                # print(f"拟合 {model_name_garch} 失败: {e}")
                bic_results[model_name_garch] = np.nan

            # --- 2. EGARCH 模型 (非对称/杠杆效应) ---
            # o=1 表示杠杆效应项
            model_name_egarch = f'EGARCH({p},1,{q})-t'
            try:
                # 使用 't' 分布
                gm_egarch = arch_model(residuals_for_garch, vol='EGARCH', p=p, o=1, q=q, mean='Zero', dist='t')
                res_egarch = gm_egarch.fit(disp='off', update_freq=0)
                bic_results[model_name_egarch] = res_egarch.bic
                
                if res_egarch.bic < best_bic:
                    best_bic = res_egarch.bic
                    best_model_result = res_egarch
                    best_model_name = model_name_egarch

            except Exception as e:
                # print(f"拟合 {model_name_egarch} 失败: {e}")
                bic_results[model_name_egarch] = np.nan
    
    print("\n--- GARCH 模型 BIC 比较表 ---")
    # 排序并打印 BIC 结果
    bic_df = pd.Series(bic_results).sort_values()
    print(bic_df.to_string(float_format="%.4f"))

    # 将最优模型赋值给 garch_result，以便后续在第5部分使用
    garch_result = best_model_result 

    if garch_result:
        print(f"\n--- 最优 GARCH 模型拟合结果 ({best_model_name}) ---")
        print("BIC 值最低，模型最优。")
        print(garch_result.summary())

        # 绘制条件波动率图
        print(f"\n绘制 {best_model_name} 拟合的条件波动率...")
        plt.figure(figsize=(10, 5))
        garch_result.plot(annualize='D')
        plt.suptitle(f"{best_model_name} Conditional Volatility")
        plt.tight_layout()
        plt.show()
    else:
        print("所有 GARCH 模型拟合失败。")
    # === (GARCH T 优化结束) ===

else:
    print("结论：p-value > 0.05，残差中没有显著的ARCH效应，无需建立GARCH模型。")
    garch_result = None # 确保在无ARCH效应时 garch_result 为 None

# === 4. 组合模型预测 ===
print("\n--- 4. 组合模型预测 (Y_t = T_t + S_t + R_t) ---")
n_forecast = 10

# 1. 预测 T_t
future_t = np.arange(len(ts), len(ts) + n_forecast)
trend_forecast = np.polyval(coeffs, future_t)

# 2. 预测 S_t
last_date = ts.index[-1]
# freq='B' (Business Day) 确保了星期的正确性
forecast_index = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=n_forecast, freq='B')
# 映射未来日期的星期效应
seasonal_forecast = pd.Series(forecast_index.dayofweek.map(seasonal_factors_dow), index=forecast_index).values

# 3. 预测 R_t
forecast_obj = arima_model_residuals.get_forecast(steps=n_forecast)
residuals_forecast = forecast_obj.predicted_mean
residuals_conf_int = forecast_obj.conf_int(alpha=0.05)

# 4. 组合预测 Y_t
final_forecast_values = trend_forecast + seasonal_forecast + residuals_forecast.values
final_conf_int_lower = trend_forecast + seasonal_forecast + residuals_conf_int.iloc[:, 0].values
final_conf_int_upper = trend_forecast + seasonal_forecast + residuals_conf_int.iloc[:, 1].values

# 整理为 DataFrame
forecast_series = pd.Series(final_forecast_values, index=forecast_index)
final_conf_int_df = pd.DataFrame({'Lower 95%': final_conf_int_lower, 'Upper 95%': final_conf_int_upper}, index=forecast_index)

print(f"\n--- 最终组合预测结果 ---")
prediction_summary_df = pd.DataFrame({
    '预测值': forecast_series,
    '95%置信下限': final_conf_int_df['Lower 95%'],
    '95%置信上限': final_conf_int_df['Upper 95%']
})
print(f"未来 {n_forecast} 个交易日的预测值及95%置信区间：")
print(prediction_summary_df.to_string(float_format="%.4f"))

# --- 绘制包含历史拟合的预测图 (完整版) ---
print("\n绘制组合模型拟合与预测图 (完整版)...")
# 历史拟合值 = T_t + S_t + R_t(fitted)
model_fitted_values = trend_series + seasonal_series + arima_model_residuals.fittedvalues
model_fitted_values = model_fitted_values.dropna()

plt.figure(figsize=(12, 6))
plt.plot(ts, label='原始观测值', alpha=0.6)
plt.plot(model_fitted_values, label='模型拟合值 (历史 T+S+R)', color='green', linestyle='--')
plt.plot(forecast_series, label="组合模型预测值 (未来)", color='red', marker='o')
plt.fill_between(forecast_index, final_conf_int_df['Lower 95%'], final_conf_int_df['Upper 95%'], color='red', alpha=0.15, label="95% 置信区间 (未来)")
plt.title(f"趋势(T)-季节(S)-ARIMA-GARCH 组合模型拟合与预测")
plt.xlabel("日期"); plt.ylabel("指数点位"); plt.legend(); plt.grid(True); plt.tight_layout(); plt.show()

# --- 绘制2025年以来的局部放大图 ---
print("\n绘制组合模型拟合与预测图 (2025年以来局部放大)...")
ts_zoom = ts[ts.index.year >= 2025]
model_fitted_zoom = model_fitted_values[model_fitted_values.index.year >= 2025]
plt.figure(figsize=(10, 5))
plt.plot(ts_zoom, label='原始观测值 (2025+)', alpha=0.7)
plt.plot(model_fitted_zoom, label='模型拟合值 (2025+)', color='green', linestyle='--')
plt.plot(forecast_series, label="组合模型预测值 (未来)", color='red', marker='o')
plt.fill_between(forecast_index, final_conf_int_df['Lower 95%'], final_conf_int_df['Upper 95%'], color='red', alpha=0.15, label="95% 置信区间 (未来)")
plt.title(f"组合模型拟合与预测 (2025年以来局部放大)")
plt.xlabel("日期"); plt.ylabel("指数点位"); plt.legend(); plt.grid(True); plt.tight_layout(); plt.show()


# === 5. 组合模型表达式汇总 ===
print("\n--- 5. 组合模型表达式汇总 ---")
print(f"模型结构: Y_t = T_t + S_t + R_t")
print(f"其中 R_t = ARIMA(...) + ε_t")
print("-" * 30)

# 1. T_t (趋势)
print(f"T_t (趋势) = {coeffs[0]:.4f} * t^2 + {coeffs[1]:.4f} * t + {coeffs[2]:.4f}")
print("  (其中 t 是从 0 开始的时间索引)")
print("-" * 30)

# 2. S_t (季节)
print(f"S_t (季节) = 星期效应 (均值调整后):")
print(seasonal_factors_dow.to_string(float_format="%.4f"))
print("  (0=周一, 1=周二, 2=周三, 3=周四, 4=周五)")
print("-" * 30)

# 3. R_t (残差均值)
print(f"R_t (残差均值) = ARIMA{best_order} 模型:")
# (为简洁起见，我们直接打印 ARIMA 的系数表)
# --- 修正点 1 ---
# 移除了 .to_string()
print(arima_model_residuals.summary().tables[1])
print("-" * 30)

# 4. ε_t (残差波动)
if garch_result:
    print(f"ε_t (残差波动) = GARCH(1, 1) / t-distribution 模型:")
    # (打印 GARCH 的系数表)
    # --- 修正点 2 ---
    # 移除了 .to_string()
    print(garch_result.summary().tables[1])
else:
    print("ε_t (残差波动) = GARCH 模型未拟合 (无ARCH效应)")
print("-" * 30)


print("\n--- 分析代码执行完毕 ---")


# 提取 2025 年 9 月的数据
# (您可以将 '2025-09' 更改为您想看的任何月份, e.g., '2024-05')
ss_month = seasonal_series['2025-09']

plt.figure(figsize=(10, 5))
# 使用 'steps-post' 和 'marker' 来清晰地显示星期的跳变
plt.plot(ss_month, marker='o', drawstyle='steps-post', label='S_t (星期效应)')

plt.title(f"S_t (星期效应) 在 2025年9月 的表现")
plt.xlabel("日期")
plt.ylabel("季节效应 S_t (指数点位)")
plt.grid(True, linestyle=':')
plt.legend()
plt.tight_layout()
plt.show()


# === 6. (新增) 模型对比：Holt 两参数指数平滑 ===
print("\n--- 6. (新增) 模型对比：Holt 两参数指数平滑 ---")
print("拟合 Holt's 线性趋势模型 (两参数：alpha, beta)...")

try:
    # 6.1 拟合 Holt 模型
    model_holt = Holt(ts, exponential=False, damped_trend=False)
    fit_holt = model_holt.fit(optimized=True)
    
    print("\n--- Holt's 线性趋势模型拟合结果 ---")
    print(fit_holt.summary())
    
    # 6.2 (新增) 输出 Holt 模型表达式
    print("\n--- Holt's 模型表达式 ---")
    # 获取参数
    alpha = fit_holt.model.params['smoothing_level']
    beta = fit_holt.model.params['smoothing_trend']
    L0 = fit_holt.model.params['initial_level']
    b0 = fit_holt.model.params['initial_trend']
    
    print(f"  Level (水平): L_t = {alpha:.4f} * Y_t + (1 - {alpha:.4f}) * (L_(t-1) + b_(t-1))")
    print(f"  Trend (趋势): b_t = {beta:.4f} * (L_t - L_(t-1)) + (1 - {beta:.4f}) * b_(t-1)")
    print(f"  Forecast (预测): Y_t+h = L_t + h * b_t")
    print(f"  初始值 (t=0): L_0 = {L0:.4f}, b_0 = {b0:.4f}")

    # 6.3 (新增) 模型指标对比 (BIC 与 RMSE)
    print("\n--- 6.3 模型指标对比 ---")
    
    # --- 提取 BICs ---
    bic_holt = fit_holt.bic
    
    try:
        # 从 3.4 节获取 ARIMA(R_t) 的 BIC
        bic_arima = arima_model_residuals.bic
    except NameError:
        bic_arima = np.nan
        
    try:
        # 从 3.5 节获取 GARCH(ε_t) 的 BIC
        bic_garch = garch_result.bic
    except (NameError, AttributeError):
        bic_garch = np.nan # 如果 GARCH 未运行或失败
    
    # --- 提取 RMSE (均方根误差) ---
    # 我们必须在相同的、非NA的索引上比较 RMSE
    
    # 获取 T+S+ARIMA 的拟合值 (已在 4.4 节中 dropna())
    fitted_arima = model_fitted_values 
    # 获取 Holt 的拟合值
    fitted_holt_hist = fit_holt.fittedvalues
    
    # 对齐索引 (确保比较的是相同的时间段)
    common_index = fitted_arima.index.intersection(fitted_holt_hist.index)
    
    ts_aligned = ts.loc[common_index]
    arima_aligned = fitted_arima.loc[common_index]
    holt_aligned = fitted_holt_hist.loc[common_index]
    
    # 计算 RMSE
    rmse_arima = np.sqrt(mean_squared_error(ts_aligned, arima_aligned))
    rmse_holt = np.sqrt(mean_squared_error(ts_aligned, holt_aligned))

    # 打印对比表
    comparison_df = pd.DataFrame({
        '指标': ['BIC (模型/组件)', 'RMSE (拟合优度)'],
        'T+S+ARIMA+GARCH (模型1)': [f"ARIMA: {bic_arima:.2f}, GARCH: {bic_garch:.2f}", f"{rmse_arima:.4f}"],
        'Holt 两参数 (模型2)': [f"{bic_holt:.2f}", f"{rmse_holt:.4f}"]
    })
    print(comparison_df.to_string(index=False))
    
    print("\n指标说明:")
    print("  - BIC (贝叶斯信息准则): 越低越好 (用于模型选择)。")
    print("      (注意: T+S+ARIMA 的 BIC 是其组件的 BIC，Holt 的 BIC 是整个模型的，它们不完全可比。)")
    print("  - RMSE (均方根误差): 越低越好 (用于拟合优度)，表示模型历史拟合值与真实值的平均差异。")


    # 6.4 绘制对比图 (2025年以来)
    print("\n--- 6.4 绘制 Holt 模型与组合模型的拟合/预测对比图 (2025年以来) ---")
    
    # 预测 (确保索引正确)
    n_forecast = 10 # 确保 n_forecast 已定义
    forecast_holt_values = fit_holt.forecast(n_forecast).values
    forecast_holt = pd.Series(forecast_holt_values, index=forecast_index, name='Holt_Forecast')
    
    try:
        ts_zoom = ts[ts.index.year >= 2025]
        model_fitted_zoom = model_fitted_values[model_fitted_values.index.year >= 2025]
        fitted_holt_zoom = fitted_holt_hist[fitted_holt_hist.index.year >= 2025]
    except (NameError, AttributeError):
        print("错误：无法找到 'model_fitted_values' 或切片失败。")
        exit()

    plt.figure(figsize=(12, 6))
    
    # 1. 原始数据
    plt.plot(ts_zoom, label='原始观测值 (2025+)', alpha=0.6, color='black')
    
    # 2. 模型1: T+S+ARIMA+GARCH
    plt.plot(model_fitted_zoom, label='T+S+ARIMA 拟合值 (RMSE: {:.2f})'.format(rmse_arima), color='green', linestyle='--')
    plt.plot(forecast_series, label="T+S+ARIMA 预测值", color='red', marker='o')
    
    # 3. 模型2: Holt's
    plt.plot(fitted_holt_zoom, label="Holt's 拟合值 (RMSE: {:.2f})".format(rmse_holt), color='blue', linestyle=':')
    plt.plot(forecast_holt, label="Holt's 预测值", color='cyan', marker='x')

    plt.title("模型对比 (2025年以来)")
    plt.xlabel("日期"); plt.ylabel("指数点位")
    plt.legend(); plt.grid(True); plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"拟合 Holt's 模型时出错: {e}")

print("\n--- 模型对比部分执行完毕 ---")
print("\n--- 完整分析代码执行完毕 ---")