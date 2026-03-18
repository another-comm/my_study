import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pykalman import KalmanFilter

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

years = np.arange(2000, 2025)

v_data_raw = np.array([
    64.05, 69.07, 74.18, 77.69, 80.72, 
    92.11, 95.14, 101.73, 103.23, 101.73, 
    87.73, 87.55, 92.64, 95.44, 96.10, 
    98.30, 101.50, 107.20, 115.10, 130.60, 
    0.00, 11.70, 116.70, 167.00, 165.00
])

g_data = np.array([35, 32, 40, 38, 42, 45, 48, 50, 52, 55, 58, 60, 62, 65, 68, 72, 75, 78, 82, 88, 95, 110, 135, 165, 175])
t_data = np.array([3.39, 2.83, 3.83, 3.94, 3.61, 3.89, 2.11, 2.67, 1.44, 3.78, 5.28, 3.67, 3.56, 5.11, 6.28, 6.33, 6.67, 5.72, 6.17, 6.72, 5.50, 5.28, 5.56, 6.00, 6.22])
hpi_data = np.array([
    142.5, 148.2, 155.8, 165.4, 178.9, 201.3, 215.6, 228.4, 235.1, 238.9, 
    242.1, 245.8, 251.2, 258.4, 262.1, 268.5, 275.2, 282.4, 291.8, 305.6, 
    320.1, 358.9, 412.5, 438.2, 455.8
])

v_data_masked = np.ma.asarray(v_data_raw.copy())
v_data_masked[20] = np.ma.masked
v_data_masked[21] = np.ma.masked
v_data_masked[22] = np.ma.masked

def apply_kalman_smoothing(data):
    kf = KalmanFilter(
        transition_matrices=[1],
        observation_matrices=[1],
        initial_state_mean=data[0],
        initial_state_covariance=1,
        observation_covariance=5,
        transition_covariance=1
    )
    state_means, _ = kf.smooth(data)
    return state_means.flatten()

v_smoothed = apply_kalman_smoothing(v_data_masked)

df_processed = pd.DataFrame({
    'Year': years,
    'Visitors_Raw': v_data_raw,
    'Visitors_Smoothed': v_smoothed.round(2),
    'Glacier_Retreat': g_data,
    'Temperature': t_data,
    'HPI': hpi_data
})

df_processed['Growth_Rate_Smoothed'] = df_processed['Visitors_Smoothed'].pct_change().fillna(0) * 100

print("数据预处理完成。前5行预览：")
print(df_processed.head())

cols_to_standardize = ['Visitors_Smoothed', 'Glacier_Retreat', 'Temperature', 'HPI']

print("\n------------------------------------------------")
print("变量标准化 (Z-Score Standardization)")
print("------------------------------------------------")

stats_df = pd.DataFrame({
    'Variable': cols_to_standardize,
    'Mean_Before': [df_processed[col].mean() for col in cols_to_standardize],
    'Std_Before': [df_processed[col].std() for col in cols_to_standardize]
})

for col in cols_to_standardize:
    mean_val = df_processed[col].mean()
    std_val = df_processed[col].std()
    df_processed[f'{col}_ZScore'] = (df_processed[col] - mean_val) / std_val
    print(f"{col}: 均值 = {mean_val:.2f}, 标准差 = {std_val:.2f}")

print("\n标准化后验证（应接近 0 和 1）：")
for col in cols_to_standardize:
    zcol = f'{col}_ZScore'
    mean_z = df_processed[zcol].mean()
    std_z = df_processed[zcol].std()
    print(f"{zcol}: 均值 = {mean_z:.6f}, 标准差 = {std_z:.6f}")

print("\n标准化后的数据预览（前5行）：")
print(df_processed[[col for col in df_processed.columns if 'ZScore' in col]].head())

plt.figure(figsize=(10, 6))
plt.plot(years, v_data_raw, 'o-', label='Raw Data (Pandemic Drop)', color='gray', alpha=0.6)
plt.plot(years, v_smoothed, 'r--', label='Kalman Smoothed (Potential Trend)', linewidth=2)
plt.axvspan(2020, 2022, color='yellow', alpha=0.2, label='Pandemic Gap')
plt.title('Juneau Tourist Visitors: Kalman Filter Imputation (2000-2024)')
plt.xlabel('Year')
plt.ylabel('Visitors (10k)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('visitor_trend_kalman.png', dpi=300, bbox_inches='tight')
print("\n图表已保存为 visitor_trend_kalman.png")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Z-Score Standardization: Before vs After (2000-2024)', fontsize=14, weight='bold')

variables = [
    ('Visitors_Smoothed', 'Visitors (10k)', 'Visitors'),
    ('Glacier_Retreat', 'Glacier Retreat (m)', 'Glacier Retreat'),
    ('Temperature', 'Temperature (°C)', 'Average Temperature'),
    ('HPI', 'Housing Price Index', 'Housing Price Index')
]

for idx, (var, ylabel, title) in enumerate(variables):
    ax = axes[idx // 2, idx % 2]
    ax.plot(years, df_processed[var], 'o-', label='Original', alpha=0.7, linewidth=2)
    ax.plot(years, df_processed[f'{var}_ZScore'], 's--', label='Z-Score Normalized', alpha=0.7, linewidth=2)
    ax.set_title(title, fontsize=11, weight='bold')
    ax.set_xlabel('Year', fontsize=10)
    ax.set_ylabel(ylabel + ' / Z-Score', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.tick_params(labelsize=9)

plt.tight_layout()
plt.savefig('standardization_comparison.png', dpi=300, bbox_inches='tight')
print("标准化对比图已保存为 standardization_comparison.png")

df_processed.to_csv('juneau_data_processed.csv', index=False)
print("\n清洗并标准化后的数据已保存为 juneau_data_processed.csv")
print("注意：CSV 包含原始值和平滑后的 Z-Score 标准化值，便于后续建模使用。")
