import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from statsmodels.tsa.stattools import grangercausalitytests
from sklearn.metrics import r2_score

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

try:
    df = pd.read_csv('juneau_data_processed.csv')
except FileNotFoundError:
    print("错误：请先运行 data_preprocessing.py")
    exit()

df['dG_dt'] = df['Glacier_Retreat'].diff().fillna(0)

window_size = 5
df['T_acc'] = df['Temperature_ZScore'].rolling(window=window_size).mean()

df['V_effect'] = df['Visitors_Smoothed_ZScore']

model_data = df.dropna().reset_index(drop=True)

print(f"用于建模的样本量: {len(model_data)} (已去除前 {window_size} 年无积温数据的样本)")

print("\n=== Granger 因果检验: 物理累积量耦合验证 ===")
print("[检验 A] 累积气温 (T_acc) -> 冰川退缩率 (dG/dt) ?")
gc_res_T = grangercausalitytests(model_data[['dG_dt', 'T_acc']], maxlag=3, verbose=False)
for lag in range(1, 4):
    p_val = gc_res_T[lag][0]['ssr_ftest'][1]
    print(f"  Lag {lag}: p-value = {p_val:.4f} {'*' if p_val<0.05 else ''}")

print("\n[检验 B] 游客因子 (V_effect) -> 冰川退缩率 (dG/dt) ?")
gc_res_V = grangercausalitytests(model_data[['dG_dt', 'V_effect']], maxlag=3, verbose=False)
for lag in range(1, 4):
    p_val = gc_res_V[lag][0]['ssr_ftest'][1]
    print(f"  Lag {lag}: p-value = {p_val:.4f} {'*' if p_val<0.05 else ''}")

print("\n=== 非线性动力学拟合 ===")

def glacier_dynamics_model(X, a, gamma, b, c):
    T_val, V_val = X
    if abs(gamma) < 0.01:
        return a * T_val + b * V_val + c
    else:
        T_shifted = T_val + 3
        return a * np.power(T_shifted, gamma) + b * V_val + c

X_data = (model_data['T_acc'].values, model_data['V_effect'].values)
y_data = model_data['dG_dt'].values

p0 = [1.0, 1.5, 0.01, 0] 
bounds = ([0, 0, 0, -np.inf], [np.inf, 5, np.inf, np.inf])

try:
    popt, pcov = curve_fit(glacier_dynamics_model, X_data, y_data, p0=p0, bounds=bounds, maxfev=5000)
    
    a_fit, gamma_fit, b_fit, c_fit = popt
    print(f"拟合参数:")
    print(f"  a (气温系数) = {a_fit:.4f}")
    print(f"  γ (非线性指数) = {gamma_fit:.4f} (说明气温影响是{'超线性' if gamma_fit>1 else '亚线性'}的)")
    print(f"  b (游客系数) = {b_fit:.4f}")
    print(f"  c (常数项)   = {c_fit:.4f}")
    
    y_pred = glacier_dynamics_model(X_data, *popt)
    r2 = r2_score(y_data, y_pred)
    print(f"拟合优度 R² = {r2:.4f}")

    plt.figure(figsize=(10, 6))
    plt.plot(model_data['Year'], y_data, 'ko-', label='Observed Retreat Rate', alpha=0.6)
    plt.plot(model_data['Year'], y_pred, 'r--', label='Fitted Model', linewidth=2)
    
    y_pred_no_tourist = glacier_dynamics_model((model_data['T_acc'].values, np.zeros_like(model_data['V_effect'].values)), *popt)
    plt.plot(model_data['Year'], y_pred_no_tourist, 'b:', label='Temperature Only', alpha=0.7)
    
    plt.fill_between(model_data['Year'], y_pred, y_pred_no_tourist, color='orange', alpha=0.2, label='Additional Retreat from Visitors')
    
    plt.title(f'Nonlinear Time-Lagged Dynamics Fitting (R^2={r2:.2f})\n$dG/dt = {a_fit:.2f} \\cdot T_{{acc}}^{{{gamma_fit:.2f}}} + {b_fit:.3f} \\cdot V$')
    plt.ylabel('Annual Retreat Distance (m/yr)')
    plt.xlabel('Year')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.savefig('nonlinear_glacier_dynamics.png')
    print("\n动力学拟合图已保存为 nonlinear_glacier_dynamics.png")
    
except Exception as e:
    print(f"拟合失败: {e}")
    print("建议检查 T_acc 是否包含负值 (power函数不支持负底数)")
