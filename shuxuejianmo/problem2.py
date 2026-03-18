import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, mean_squared_error
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ===== 数据路径 =====
# 定义各个气象和土壤湿度数据的文件夹路径
wind_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\风速'
rain_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\降水量'
temp_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\温度数据'
soil_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\土壤湿度'
ssrd_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\下行辐射强度_ssrd'

# ===== 通用数据读取函数 =====
def load_data(folder, col_name, unit, scale=1.0):
    """
    读取指定文件夹内所有xlsx文件的数据，提取两列：
    时间和对应气象变量列，清洗单位，转换为float，统一放入一个DataFrame。

    参数：
        folder: 数据文件夹路径
        col_name: 变量列名（如'wind','rain'等）
        unit: 数据中带的单位字符（用于去除）
        scale: 缩放系数（默认1.0），例如土壤湿度单位转换

    返回：
        拼接并按时间排序后的DataFrame，列为['datetime', col_name]
    """
    dfs = []
    for file in os.listdir(folder):
        if file.endswith('.xlsx') and not file.startswith('~$'):  # 忽略临时文件
            path = os.path.join(folder, file)
            df = pd.read_excel(path)
            df.columns = ['datetime', col_name]  # 统一列名
            # 去除单位字符，转float，乘以scale缩放
            df[col_name] = df[col_name].astype(str).str.replace(unit, '').str.strip().astype(float) * scale
            df['datetime'] = pd.to_datetime(df['datetime'])  # 转换时间格式
            dfs.append(df)
    return pd.concat(dfs).sort_values('datetime').reset_index(drop=True)

# ===== 加载所有数据 =====
# 依次调用通用函数加载所有气象数据和土壤湿度数据
wind_df = load_data(wind_folder, 'wind', 'm/s')
rain_df = load_data(rain_folder, 'rain', 'mm')
temp_df = load_data(temp_folder, 'temp', '°C')
soil_df = load_data(soil_folder, 'soil', 'm³/m³', scale=100)  # 土壤湿度单位转为百分比
ssrd_df = load_data(ssrd_folder, 'ssrd', 'W/m²')

# ===== 合并所有数据 =====
# 根据datetime列内连接多个数据表，保留共有时间戳的数据，土壤湿度用左连接（可能缺失）
df_all = wind_df.merge(rain_df, on='datetime', how='inner') \
                 .merge(temp_df, on='datetime', how='inner') \
                 .merge(ssrd_df, on='datetime', how='inner') \
                 .merge(soil_df, on='datetime', how='left')

# ===== 只保留6-7月数据并设置datetime为索引 =====
# 修改此处，直接设置datetime为索引，以便后续模拟循环中进行时间索引查找
df_all = df_all[df_all['datetime'].dt.month.isin([6, 7])].set_index('datetime').copy()

# ===== 构造训练特征与标签 =====
df_all['year'] = df_all.index.year  # 提取年份，方便后续分组分析，现在从索引获取年份
X = df_all[['wind', 'rain', 'temp', 'ssrd']]  # 输入特征：风速、降水、温度、辐射强度
y = df_all['soil']  # 标签：土壤湿度百分比

# ===== 标准化 =====
# 分别对特征和标签进行均值为0，方差为1的标准化处理，有助于模型训练收敛
scaler_X = StandardScaler()
scaler_y = StandardScaler()
X_scaled = scaler_X.fit_transform(X)
y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1)).ravel()  # y转成1D数组

# ===== 改进后的 BP 神经网络训练 =====
# 构建三层隐藏层的MLP神经网络，层结构128-128-64节点
mlp = MLPRegressor(
    hidden_layer_sizes=(128, 128, 64),    # 三层隐藏层，节点数依次减少
    activation='relu',                    # 激活函数ReLU
    solver='adam',                        # 优化算法Adam
    max_iter=3000,                        # 最大迭代次数3000
    learning_rate_init=0.001,             # 初始学习率0.001
    alpha=0.0001,                         # L2正则化参数，防止过拟合
    early_stopping=True,                  # 启用早停策略
    validation_fraction=0.1,              # 10%训练数据作为验证集
    n_iter_no_change=500,                 # 验证集误差连续1000代无提升则停止训练
    random_state=42                       # 随机种子保证结果可复现
)

mlp.fit(X_scaled, y_scaled)  # 训练模型

# ===== 训练损失曲线 =====
plt.figure(figsize=(8,4))
plt.plot(mlp.loss_curve_)  # 画出每代训练损失变化曲线，观察收敛趋势
plt.xlabel('迭代次数')
plt.ylabel('损失值')
plt.title('训练损失曲线')
plt.grid(True)
plt.show()

# ===== 预测结果还原 =====
y_pred_scaled = mlp.predict(X_scaled)  # 预测标准化的标签
y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()  # 还原到百分比真实值
df_all['soil_pred'] = y_pred  # 将预测值加入原数据表

# ===== 误差评估 =====
print(f'整体 RMSE: {root_mean_squared_error(y, y_pred):.4f}')  # 均方根误差
print(f'整体 MAE: {mean_absolute_error(y, y_pred):.4f}')        # 平均绝对误差

# ===== 每年输出对比图 =====
for year in sorted(df_all['year'].unique()):
    df_year = df_all[df_all['year'] == year].reset_index(drop=True)
    plt.figure(figsize=(14, 5))
    # 真实土壤湿度折线
    plt.plot(df_year['datetime'], df_year['soil'], label='真实土壤湿度', color='green')
    # 预测土壤湿度折线
    plt.plot(df_year['datetime'], df_year['soil_pred'], label='预测土壤湿度', color='red')
    plt.title(f'{year}年6-7月土壤湿度预测对比（含辐射强度）')
    plt.xlabel('时间')
    plt.ylabel('土壤湿度 (%)')
    plt.legend()
    plt.grid(True)
    # 时间格式化为月-日
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    # 每5天显示一个主刻度
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()  # 日期标签倾斜显示
    plt.tight_layout()
    plt.show()

# ===== 连续晴天/雨天误差计算函数 =====
def calc_weather_period_errors(df, rain_col='rain', true_col='soil', pred_col='soil_pred', threshold_hours=12):
    """
    计算连续晴天和雨天期间的土壤湿度预测误差。

    参数:
        df: 含降水、真实值和预测值的DataFrame，且按时间升序排列
        rain_col: 降水量列名，默认'rain'
        true_col: 真实土壤湿度列名，默认'soil'
        pred_col: 预测土壤湿度列名，默认'soil_pred'
        threshold_hours: 连续晴/雨时间段的最小长度（小时），默认12小时

    返回:
        包含连续晴天段和雨天段的预测误差信息的字典
    """
    import numpy as np
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    
    df = df.copy()
    
    # --- 修改开始 ---
    # 如果 datetime 是索引，先按索引排序，再重置索引使其变为列
    if df.index.name == 'datetime':
        df = df.sort_index().reset_index()
    else: # 否则，按 datetime 列排序并重置索引
        df = df.sort_values('datetime').reset_index(drop=True)
    # --- 修改结束 ---
    
    # 标记晴天（降水==0）和雨天（降水>0）
    df['is_rain'] = df[rain_col] > 0
    
    # 计算降水状态是否变化，作为不同连续时间段的分割点
    df['rain_shift'] = df['is_rain'].shift(1)
    df['period_change'] = df['is_rain'] != df['rain_shift']
    df['period_id'] = df['period_change'].cumsum()  # 分配连续段ID
    
    results = {
        '晴天段': [],  # 存储所有符合长度阈值的连续晴天段误差信息
        '雨天段': []    # 存储所有符合长度阈值的连续雨天段误差信息
    }
    
    # 遍历每个连续时间段
    for period_id, group in df.groupby('period_id'):
        length = len(group)  # 该段持续的小时数
        is_rain = group['is_rain'].iloc[0]  # 该段是晴天还是雨天
        if length >= threshold_hours:  # 只考虑大于等于阈值的连续段
            true_vals = group[true_col].values
            pred_vals = group[pred_col].values
            # 计算该段的RMSE和MAE
            rmse = np.sqrt(mean_squared_error(true_vals, pred_vals))
            mae = mean_absolute_error(true_vals, pred_vals)
            period_info = {
                'start_time': group['datetime'].iloc[0],    # 段开始时间
                'end_time': group['datetime'].iloc[-1],    # 段结束时间
                'hours': length,                            # 持续小时数
                'rmse': rmse,
                'mae': mae
            }
            if is_rain:
                results['雨天段'].append(period_info)
            else:
                results['晴天段'].append(period_info)
                
    # 计算晴天段和雨天段的平均误差统计
    def summarize(period_list):
        if len(period_list) == 0:
            return {'rmse_mean': None, 'mae_mean': None, 'count': 0}
        rmse_mean = np.mean([p['rmse'] for p in period_list])
        mae_mean = np.mean([p['mae'] for p in period_list])
        return {'rmse_mean': rmse_mean, 'mae_mean': mae_mean, 'count': len(period_list)}
    
    sunny_summary = summarize(results['晴天段'])
    rainy_summary = summarize(results['雨天段'])
    
    # 打印总结结果
    print("连续晴天段数:", sunny_summary['count'])
    print(f"晴天平均 RMSE: {sunny_summary['rmse_mean']:.4f}，平均 MAE: {sunny_summary['mae_mean']:.4f}")
    print("连续雨天段数:", rainy_summary['count'])
    print(f"雨天平均 RMSE: {rainy_summary['rmse_mean']:.4f}，平均 MAE: {rainy_summary['mae_mean']:.4f}")
    
    return results

# ===== 调用连续晴雨天误差计算 =====
weather_period_errors = calc_weather_period_errors(df_all, threshold_hours=12)

# --- 灌溉决策算法代码实现 ---

# 灌溉决策参数
OPTIMAL_LOWER_BOUND = 60.0 # % # 触发灌溉的湿度阈值 (新要求：60%)
OPTIMAL_UPPER_BOUND = 75.0 # % # 灌溉目标湿度，也是最适区间的上限 (新要求：75%)
SOIL_DEPTH_M = 0.3 # 米，根据论文中30cm垂直平均土壤湿度 (已根据您的要求修改为0.3)

# 用于分析和图表显示的“最适区间”下限 (新要求：65%)
ANALYSIS_OPTIMAL_LOWER_BOUND = 65.0

def calculate_irrigation_amount(current_soil_moisture_percent, soil_depth_m, target_soil_moisture_percent):
    """
    根据当前土壤湿度和目标湿度计算所需灌溉的水量。
    Args:
        current_soil_moisture_percent (float): 当前时刻的土壤湿度百分比。
        soil_depth_m (float): 有效土壤深度，单位米。
        target_soil_moisture_percent (float): 目标土壤湿度百分比。
    Returns:
        float: 所需灌溉的水量，单位毫米。
    """
    if current_soil_moisture_percent < target_soil_moisture_percent:
        moisture_deficit_fraction = (target_soil_moisture_percent - current_soil_moisture_percent) / 100.0
        water_needed_m = moisture_deficit_fraction * soil_depth_m
        water_needed_mm = water_needed_m * 1000
        return water_needed_mm
    else:
        return 0.0

print(f"\n==== 模拟最优灌溉决策算法 (仅限玉米抽穗期) ====\n")

# 将已训练的 mlp 模型赋值给 bas_bp_model，以便后续使用
bas_bp_model = mlp

# 定义模型输入特征，与 MLP 训练时保持一致
model_input_features = ['wind', 'rain', 'temp', 'ssrd']

# 修正点: 筛选出目标年份和玉米抽穗期的数据进行模拟
target_year = 2025
silking_start_date = f'{target_year}-06-7'
silking_end_date = f'{target_year}-06-28 23:59:59' # 确保包含28号全天

# 首先筛选出目标年份的数据
# df_all 在前面的代码中已经被设置为以 'datetime' 为索引
df_2025_subset = df_all[df_all.index.year == target_year].copy()

if df_2025_subset.empty:
    print(f"错误: df_all 中没有 {target_year} 年的数据。请检查数据范围。")
else:
    # 进一步筛选出抽穗期的数据
    df_silking_period = df_2025_subset.loc[silking_start_date:silking_end_date].copy()

    if df_silking_period.empty:
        print(f"错误: 在 {target_year} 年的 {silking_start_date} 到 {silking_end_date} 期间没有数据。请检查数据范围或日期设置。")
    else:
        # 初始化模拟DataFrame，只包含玉米抽穗期的数据
        df_simulation_silking = df_silking_period.copy()
        # 初始时模拟土壤湿度等于真实值，后续会被预测和灌溉逻辑覆盖
        df_simulation_silking['simulated_soil'] = df_silking_period['soil']
        df_simulation_silking['irrigation_amount_mm'] = 0.0 # 记录每次灌溉量
        df_simulation_silking['irrigation_triggered'] = False # 记录是否触发灌溉

        total_irrigation_events_silking = 0
        total_irrigation_volume_mm_silking = 0.0

        print(f"开始模拟 {target_year} 年 {silking_start_date} 至 {silking_end_date} 玉米抽穗期灌溉决策过程...")

        # 循环进行模拟，遍历玉米抽穗期数据的每个时间点
        for current_dt_index in df_simulation_silking.index:
            # 构造当前时刻的输入特征
            # 由于前面的 MLP 模型是基于非滞后气象特征训练的，这里只使用这些特征
            current_features_values = df_all.loc[current_dt_index, model_input_features].values

            # 标准化当前输入特征
            current_features_scaled = scaler_X.transform(current_features_values.reshape(1, -1))

            # 使用模型预测下一个时刻的土壤湿度
            predicted_soil_scaled = bas_bp_model.predict(current_features_scaled)
            # 逆标准化回原始尺度，.item() 用于从单元素数组中取出标量值
            predicted_soil_percent = scaler_y.inverse_transform(predicted_soil_scaled).item()

            # --- 灌溉决策逻辑 ---
            irrigation_needed_mm = 0.0
            if predicted_soil_percent <= OPTIMAL_LOWER_BOUND: # 灌溉触发阈值 (60%)
                # 如果预测会低于下限，则触发灌溉。灌溉水量基于预测值和目标上限计算。
                irrigation_needed_mm = calculate_irrigation_amount(predicted_soil_percent, SOIL_DEPTH_M, OPTIMAL_UPPER_BOUND)

                # 记录灌溉事件
                df_simulation_silking.loc[current_dt_index, 'irrigation_amount_mm'] = irrigation_needed_mm
                df_simulation_silking.loc[current_dt_index, 'irrigation_triggered'] = True
                total_irrigation_events_silking += 1
                total_irrigation_volume_mm_silking += irrigation_needed_mm

                # 模拟灌溉后的土壤湿度立即达到目标上限
                df_simulation_silking.loc[current_dt_index, 'simulated_soil'] = OPTIMAL_UPPER_BOUND
            else:
                # 如果不需要灌溉，模拟土壤湿度就是预测的自然湿度
                df_simulation_silking.loc[current_dt_index, 'simulated_soil'] = predicted_soil_percent

        print(f"\n模拟结束。")
        print(f"{target_year} 年玉米抽穗期 ({silking_start_date} 至 {silking_end_date}) 总灌溉次数: {total_irrigation_events_silking}")
        print(f"{target_year} 年玉米抽穗期 ({silking_start_date} 至 {silking_end_date}) 总灌溉水量: {total_irrigation_volume_mm_silking:.2f} 毫米")


        # --- 绘制2025年玉米抽穗期模拟结果 ---
        print(f"\n绘制 {target_year} 年玉米抽穗期模拟灌溉决策下的土壤湿度变化图...")
        plt.figure(figsize=(18, 7))

        # 绘制原始真实土壤湿度（仅限玉米抽穗期）
        plt.plot(df_simulation_silking.index, df_simulation_silking['soil'],
                  label='真实土壤湿度', color='gray', linestyle=':', alpha=0.7)

        # 绘制模拟的土壤湿度（仅限玉米抽穗期）
        plt.plot(df_simulation_silking.index, df_simulation_silking['simulated_soil'],
                  label='模拟土壤湿度 (灌溉决策后)', color='green', linewidth=1.5)

        # 绘制最适湿度区间（使用 ANALYSIS_OPTIMAL_LOWER_BOUND 作为下限，OPTIMAL_UPPER_BOUND 作为上限）
        plt.axhspan(ANALYSIS_OPTIMAL_LOWER_BOUND, OPTIMAL_UPPER_BOUND, color='yellow', alpha=0.2, label=f'最适湿度区间 [{ANALYSIS_OPTIMAL_LOWER_BOUND}%, {OPTIMAL_UPPER_BOUND}%]')
        # 绘制灌溉触发阈值（仍为 OPTIMAL_LOWER_BOUND）
        plt.axhline(OPTIMAL_LOWER_BOUND, color='red', linestyle='--', linewidth=1, label=f'灌溉触发阈值 ({OPTIMAL_LOWER_BOUND}%)')

        # 标记灌溉事件（仅限玉米抽穗期）
        irrigation_points_silking = df_simulation_silking[df_simulation_silking['irrigation_triggered']]
        plt.scatter(irrigation_points_silking.index, irrigation_points_silking['simulated_soil'],
                    color='blue', marker='^', s=100, label='灌溉事件', zorder=5)

        plt.title(f'{target_year} 年玉米抽穗期 ({silking_start_date.split("-", 1)[1]} 至 {silking_end_date.split(" ")[0].split("-", 1)[1]}) 最优灌溉决策模拟')
        plt.xlabel('时间')
        plt.ylabel('土壤湿度 (%)')
        plt.legend()
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=24)) # 每1天一个刻度
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.show()

        # 进一步分析2025年玉米抽穗期灌溉决策下的土壤湿度维持情况
        # 计算维持在最适区间（使用 ANALYSIS_OPTIMAL_LOWER_BOUND 作为下限）的时间占比
        soil_in_optimal_range_silking = df_simulation_silking[(df_simulation_silking['simulated_soil'] >= ANALYSIS_OPTIMAL_LOWER_BOUND) &
                                                  (df_simulation_silking['simulated_soil'] <= OPTIMAL_UPPER_BOUND)]
        percentage_in_range_silking = len(soil_in_optimal_range_silking) / len(df_simulation_silking) * 100

        # 计算低于灌溉触发阈值（60%）的时间占比
        soil_below_lower_silking = df_simulation_silking[df_simulation_silking['simulated_soil'] < OPTIMAL_LOWER_BOUND]
        percentage_below_lower_silking = len(soil_below_lower_silking) / len(df_simulation_silking) * 100

        # 计算高于最适区间上限（75%）的时间占比
        soil_above_upper_silking = df_simulation_silking[df_simulation_silking['simulated_soil'] > OPTIMAL_UPPER_BOUND]
        percentage_above_upper_silking = len(soil_above_upper_silking) / len(df_simulation_silking) * 100

        print(f"\n--- {target_year} 年玉米抽穗期模拟灌溉效果分析 ---")
        print(f"土壤湿度维持在最适区间 [{ANALYSIS_OPTIMAL_LOWER_BOUND}%, {OPTIMAL_UPPER_BOUND}%] 的时间占比: {percentage_in_range_silking:.2f}%")
        print(f"土壤湿度低于 {OPTIMAL_LOWER_BOUND}% 的时间占比: {percentage_below_lower_silking:.2f}%")
        print(f"土壤湿度高于 {OPTIMAL_UPPER_BOUND}% 的时间占比: {percentage_above_upper_silking:.2f}%")

        # 总结灌溉决策
        print("\n--- 灌溉决策总结 ---")
        print(f"设计的灌溉触发阈值: {OPTIMAL_LOWER_BOUND}%") # 触发阈值仍为60%
        print(f"设计的每次灌溉目标湿度: {OPTIMAL_UPPER_BOUND}%")
        print(f"灌溉水量计算公式: (目标湿度% - 当前湿度%) / 100 * 有效土壤深度(米) * 1000 (毫米/米)")
        print(f"其中，有效土壤深度取 {SOIL_DEPTH_M} 米 (30厘米)")