import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from datetime import timedelta
import matplotlib.dates as mdates

import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体，支持中文
rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题


# ===== 文件路径（请按需修改）=====
ssrd_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\下行辐射强度_ssrd'
soil_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\土壤湿度'

# ===== 初始湿度（%）=====
theta0 = 40

# ===== 读取短波辐射数据（转换为北京时间 UTC+8）=====
def load_hourly_ssrd_data(folder):
    dfs = []
    for file in os.listdir(folder):
        if file.endswith('.xlsx') and 'ssrd' in file and not file.startswith('~$'):
            path = os.path.join(folder, file)
            df = pd.read_excel(path)
            df.columns = ['datetime', 'ssrd']
            df['ssrd'] = df['ssrd'].astype(str).str.replace('W/m²', '').str.strip().astype(float)
            df['datetime'] = pd.to_datetime(df['datetime']) + pd.Timedelta(hours=8)  # 转北京时间
            dfs.append(df)
    full_df = pd.concat(dfs)
    full_df.sort_values('datetime', inplace=True)
    return full_df

# ===== 读取土壤湿度数据（转换为北京时间 UTC+8）=====
def load_hourly_soil_data(folder):
    dfs = []
    for file in os.listdir(folder):
        if (file.endswith('.xlsx') or file.endswith('.csv')) and not file.startswith('~$'):
            path = os.path.join(folder, file)
            df = pd.read_excel(path) if file.endswith('.xlsx') else pd.read_csv(path)
            df.columns = ['datetime', 'soil']
            df['soil'] = df['soil'].astype(str).str.replace('m³/m³', '').str.strip().astype(float) * 100
            df['datetime'] = pd.to_datetime(df['datetime']) + pd.Timedelta(hours=8)  # 转北京时间
            dfs.append(df)
    full_df = pd.concat(dfs)
    full_df.sort_values('datetime', inplace=True)
    return full_df

print("⏳ 加载短波辐射数据...")
ssrd_df = load_hourly_ssrd_data(ssrd_folder)
print("⏳ 加载土壤湿度数据...")
soil_df = load_hourly_soil_data(soil_folder)

# ===== 拟合每天湿度衰减系数k 与 白天辐射强度R（北京时间 6-18点）=====
results = []
count_days = 0

start_date = soil_df['datetime'].min().floor('D')
end_date = soil_df['datetime'].max().floor('D')

for start_time in pd.date_range(start_date, end_date, freq='24H'):
    end_time = start_time + pd.Timedelta(hours=23)

    soil_sub = soil_df[(soil_df['datetime'] >= start_time) & (soil_df['datetime'] <= end_time)]
    ssrd_sub = ssrd_df[(ssrd_df['datetime'] >= start_time) & (ssrd_df['datetime'] <= end_time)]
    ssrd_daytime = ssrd_sub[(ssrd_sub['datetime'].dt.hour >= 6) & (ssrd_sub['datetime'].dt.hour <= 18)]

    if len(soil_sub) >= 10 and len(ssrd_daytime) >= 5:
        t = np.arange(len(soil_sub))
        theta = soil_sub['soil'].values
        if np.all(theta > 0) and theta[0] > theta[-1]:
            ln_ratio = np.log(theta / theta[0])
            k_fit = -np.polyfit(t, ln_ratio, 1)[0]
            R_avg = ssrd_daytime['ssrd'].mean()
            results.append((R_avg, k_fit))
            count_days += 1

print(f"\n✅ 共处理 {count_days} 天数据。")

results = np.array(results)
R_all = results[:, 0].reshape(-1, 1)
k_all = results[:, 1]

reg = LinearRegression().fit(R_all, k_all)
a, b = reg.coef_[0], reg.intercept_

print(f"\n✅ 线性拟合完成：k = {a:.8f} * R + {b:.8f}")


# ===== 预测未来48小时湿度变化（2025-07-12和07-13，北京时间）=====
def predict_R_for_date(target_date, ssrd_df):
    R_list = []
    for year in range(2021, 2025):
        hist_date = pd.to_datetime(f"{year}-{target_date.month:02}-{target_date.day:02}")
        ssrd_hist = ssrd_df[(ssrd_df['datetime'].dt.date == hist_date.date())]
        ssrd_daytime = ssrd_hist[(ssrd_hist['datetime'].dt.hour >= 6) & (ssrd_hist['datetime'].dt.hour <= 18)]
        if not ssrd_daytime.empty:
            R_list.append(ssrd_daytime['ssrd'].mean())
    if len(R_list) == 0:
        return None
    return np.mean(R_list)

def get_avg_soil_curve(month, day, soil_df):
    """ 获取指定月日（7月12日或7月13日）2021-2024年同期小时平均土壤湿度曲线 """
    curves = []
    for year in range(2021, 2025):
        day_start = pd.to_datetime(f"{year}-{month:02}-{day:02}")
        day_end = day_start + timedelta(hours=23)
        soil_sub = soil_df[(soil_df['datetime'] >= day_start) & (soil_df['datetime'] <= day_end)]
        if len(soil_sub) == 24:
            curves.append(soil_sub['soil'].values)
    if curves:
        avg_curve = np.mean(curves, axis=0)  # 24小时平均
        return avg_curve
    else:
        return None

theta_pred_all = []
time_index = []

for day_offset in [0, 1]:  # 7月12、13日
    date_target = pd.to_datetime('2025-07-12') + timedelta(days=day_offset)
    R_est = predict_R_for_date(date_target, ssrd_df)
    
    if R_est is None:
        print(f"❌ 无历史数据，无法预测 {date_target.date()} 的辐射强度")
        continue
    
    k_est = a * R_est + b
    print(f"📆 预测 {date_target.date()}（北京时间）：R = {R_est:.2f} W/m², k = {k_est:.5f} /h")
    
    for hour in range(24):
        t = hour
        theta = theta0 * np.exp(-k_est * t)
        theta_pred_all.append(theta)
        time_index.append(date_target + timedelta(hours=hour))  # 北京时间直接使用

# ===== 可视化结果（双子图）=====
import matplotlib.gridspec as gridspec

plt.figure(figsize=(10, 8))
gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])

# 子图1：k vs R 拟合
ax0 = plt.subplot(gs[0])
ax0.scatter(R_all, k_all, s=25, alpha=0.7, label='样本点')
ax0.plot(R_all, reg.predict(R_all), color='red', label=f'拟合线: k = {a:.8f}R + {b:.8f}')
ax0.set_xlabel('白天平均短波辐射强度 R (W/m^2)', fontsize=12)
ax0.set_ylabel('湿度衰减系数 k (1/h)', fontsize=12)
ax0.set_title('k = f(R) 拟合结果', fontsize=13)
ax0.legend()
ax0.grid(True)

# 子图2：模拟不同 k 的湿度变化 θ(t)
ax1 = plt.subplot(gs[1])
t_sim = np.linspace(0, 24, 100)
theta0_sim = theta0
k_vals = np.percentile(k_all, [20, 50, 80])  # 使用三种典型k值（慢速/中速/快速衰减）

colors = ['blue', 'green', 'orange']
for i, k_sim in enumerate(k_vals):
    theta_sim = theta0_sim * np.exp(-k_sim * t_sim)
    ax1.plot(t_sim, theta_sim, color=colors[i], label=f'k = {k_sim:.4f}')

ax1.set_xlabel('时间 t (小时)', fontsize=12)
ax1.set_ylabel('湿度 θ(t) (%)', fontsize=12)
ax1.set_title(r'湿度衰减曲线 $\theta(t) = \theta_0 e^{-kt}$（典型 $k$ 值）', fontsize=13)

ax1.legend()
ax1.grid(True)

plt.tight_layout()
plt.show()

# 绘制预测曲线 + 历史同期平均曲线
plt.figure(figsize=(12, 5))

# 预测曲线
plt.plot(time_index, theta_pred_all, marker='o', color='purple', label='2025年预测湿度')

# 历史同期曲线（2021-2024年7月12日和7月13日）
for day_offset in [0, 1]:
    month, day = 7, 12 + day_offset
    avg_curve = get_avg_soil_curve(month, day, soil_df)
    if avg_curve is not None:
        # 生成时间索引（北京时间）
        base_date = pd.to_datetime(f"2025-{month:02}-{day:02}")
        time_idx_hist = [base_date + timedelta(hours=h) for h in range(24)]
        plt.plot(time_idx_hist, avg_curve, linestyle='--', label=f'2021-2024年平均 {month}-{day}')

plt.xlabel('北京时间', fontsize=12)
plt.ylabel('湿度 θ(t) (%)', fontsize=12)
plt.title('土壤湿度预测与历史同期平均对比（2025年7月12-13日）', fontsize=14)
plt.legend()
plt.grid(True)
    
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.show()
