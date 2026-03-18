import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, mean_squared_error
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ===== 数据路径 =====
wind_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\风速'
rain_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\降水量'
temp_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\温度数据'
soil_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\土壤湿度'
ssrd_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\下行辐射强度_ssrd'

# ===== 通用数据读取函数 =====
def load_data(folder, col_name, unit, scale=1.0):
    dfs = []
    for file in os.listdir(folder):
        if file.endswith('.xlsx') and not file.startswith('~$'):
            path = os.path.join(folder, file)
            df = pd.read_excel(path)
            df.columns = ['datetime', col_name]
            df[col_name] = df[col_name].astype(str).str.replace(unit, '').str.strip().astype(float) * scale
            df['datetime'] = pd.to_datetime(df['datetime'])
            dfs.append(df)
    return pd.concat(dfs).sort_values('datetime').reset_index(drop=True)

# ===== 加载所有数据 =====
wind_df = load_data(wind_folder, 'wind', 'm/s')
rain_df = load_data(rain_folder, 'rain', 'mm')
temp_df = load_data(temp_folder, 'temp', '°C')
soil_df = load_data(soil_folder, 'soil', 'm³/m³', scale=100)
ssrd_df = load_data(ssrd_folder, 'ssrd', 'W/m²')

# ===== 合并所有数据 =====
df_all = wind_df.merge(rain_df, on='datetime', how='inner') \
                .merge(temp_df, on='datetime', how='inner') \
                .merge(ssrd_df, on='datetime', how='inner') \
                .merge(soil_df, on='datetime', how='left')

# ===== 只保留6-7月数据 =====
df_all = df_all[df_all['datetime'].dt.month.isin([6, 7])].reset_index(drop=True)

# ===== 构造训练特征与标签 =====
df_all['year'] = df_all['datetime'].dt.year
X = df_all[['wind', 'rain', 'temp', 'ssrd']]
y = df_all['soil']

# ===== 标准化 =====
scaler_X = StandardScaler()
scaler_y = StandardScaler()
X_scaled = scaler_X.fit_transform(X)
y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1)).ravel()

# ===== 改进后的 BP 神经网络训练 =====
mlp = MLPRegressor(
    hidden_layer_sizes=(128, 128, 64),
    activation='relu',
    solver='adam',
    max_iter=2000,
    learning_rate_init=0.001,
    alpha=0.0001,
    early_stopping=True,
    validation_fraction=0.1,
    n_iter_no_change=30,
    random_state=42
)

mlp.fit(X_scaled, y_scaled)

# ===== 训练损失曲线 =====
plt.figure(figsize=(8,4))
plt.plot(mlp.loss_curve_)
plt.xlabel('迭代次数')
plt.ylabel('损失值')
plt.title('训练损失曲线')
plt.grid(True)
plt.show()

# ===== 预测结果还原 =====
y_pred_scaled = mlp.predict(X_scaled)
y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
df_all['soil_pred'] = y_pred

# ===== 误差评估 =====
print(f'整体 RMSE: {root_mean_squared_error(y, y_pred):.4f}')
print(f'整体 MAE: {mean_absolute_error(y, y_pred):.4f}')

# ===== 每年输出对比图 =====
for year in sorted(df_all['year'].unique()):
    df_year = df_all[df_all['year'] == year].reset_index(drop=True)
    plt.figure(figsize=(14, 5))
    plt.plot(df_year['datetime'], df_year['soil'], label='真实土壤湿度', color='green')
    plt.plot(df_year['datetime'], df_year['soil_pred'], label='预测土壤湿度', color='red')
    plt.title(f'{year}年6-7月土壤湿度预测对比（含辐射强度）')
    plt.xlabel('时间')
    plt.ylabel('土壤湿度 (%)')
    plt.legend()
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.show()

# ===== 连续晴天/雨天误差计算函数 =====
def calc_weather_period_errors(df, rain_col='rain', true_col='soil', pred_col='soil_pred', threshold_hours=12):
    import numpy as np
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    
    df = df.copy()
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # 标记晴天(0降水)和雨天(>0降水)
    df['is_rain'] = df[rain_col] > 0
    
    # 找出连续区间id
    df['rain_shift'] = df['is_rain'].shift(1)
    df['period_change'] = df['is_rain'] != df['rain_shift']
    df['period_id'] = df['period_change'].cumsum()
    
    results = {
        '晴天段': [],
        '雨天段': []
    }
    
    for period_id, group in df.groupby('period_id'):
        length = len(group)
        is_rain = group['is_rain'].iloc[0]
        if length >= threshold_hours:
            true_vals = group[true_col].values
            pred_vals = group[pred_col].values
            rmse = np.sqrt(mean_squared_error(true_vals, pred_vals))
            mae = mean_absolute_error(true_vals, pred_vals)
            period_info = {
                'start_time': group['datetime'].iloc[0],
                'end_time': group['datetime'].iloc[-1],
                'hours': length,
                'rmse': rmse,
                'mae': mae
            }
            if is_rain:
                results['雨天段'].append(period_info)
            else:
                results['晴天段'].append(period_info)
                
    def summarize(period_list):
        if len(period_list) == 0:
            return {'rmse_mean': None, 'mae_mean': None, 'count': 0}
        rmse_mean = np.mean([p['rmse'] for p in period_list])
        mae_mean = np.mean([p['mae'] for p in period_list])
        return {'rmse_mean': rmse_mean, 'mae_mean': mae_mean, 'count': len(period_list)}
    
    sunny_summary = summarize(results['晴天段'])
    rainy_summary = summarize(results['雨天段'])
    
    print("连续晴天段数:", sunny_summary['count'])
    print(f"晴天平均 RMSE: {sunny_summary['rmse_mean']:.4f}，平均 MAE: {sunny_summary['mae_mean']:.4f}")
    print("连续雨天段数:", rainy_summary['count'])
    print(f"雨天平均 RMSE: {rainy_summary['rmse_mean']:.4f}，平均 MAE: {rainy_summary['mae_mean']:.4f}")
    
    return results

# ===== 调用连续晴雨天误差计算 =====
weather_period_errors = calc_weather_period_errors(df_all, threshold_hours=12)
