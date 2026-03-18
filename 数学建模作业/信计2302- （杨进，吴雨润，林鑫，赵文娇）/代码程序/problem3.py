import pandas as pd
import numpy as np
import os
import re
import matplotlib.pyplot as plt
import matplotlib as mpl # 导入 matplotlib 模块本身
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
mpl.rcParams['axes.unicode_minus'] = False # 解决负号 '-' 显示为方块的问题

# ===== 通用数据读取函数 (已优化，更健壮地处理数据清洗) =====
def load_data(folder, col_name, unit, scale=1.0):
    """
    读取指定文件夹内所有xlsx文件的数据，提取两列：
    时间、对应气象变量列，清洗单位，转换为float，统一放入一个DataFrame。
    """
    dfs = []
    for file in os.listdir(folder):
        if file.endswith('.xlsx') and not file.startswith('~$'):
            path = os.path.join(folder, file)
            df = pd.read_excel(path)
            
            # 确保DataFrame有足够的列，避免索引错误
            if df.shape[1] < 2:
                print(f"警告: 文件 {file} 列数不足，可能为空或格式错误。跳过。")
                continue
            
            # 假设第一列是时间，第二列是数据
            # 尝试查找包含“时间”或“日期”的列作为时间列
            time_col_candidates = [c for c in df.columns if '时间' in str(c) or '日期' in str(c)]
            # 尝试查找包含变量名或数值的列作为数据列
            data_col_candidates = [c for c in df.columns if col_name in str(c) or df[c].apply(lambda x: isinstance(x, (int, float)) or (isinstance(x, str) and re.match(r'([-+]?\d*\.?\d+)', x))).any()]

            if time_col_candidates and data_col_candidates:
                # 优先使用检测到的列，否则回退到默认的[0]和[1]
                time_col = time_col_candidates[0]
                data_col = data_col_candidates[0]
            else:
                # 如果自动检测失败，回退到默认的第一列和第二列
                print(f"警告: 文件 {file} 未能自动识别时间或数据列，尝试使用默认前两列。")
                time_col = df.columns[0]
                data_col = df.columns[1]

            # 重命名列以方便后续处理
            df.columns = ['datetime_raw' if c == time_col else 'data_raw' if c == data_col else c for c in df.columns]
            
            # 尝试将时间列转换为datetime，如果失败则该行转换为NaT，后续会丢弃
            df['datetime'] = pd.to_datetime(df['datetime_raw'], errors='coerce')
            
            # 健壮地清洗数据列：
            # 1. 确保是字符串类型
            # 2. 使用正则表达式提取所有数字、小数点和正负号。这将忽略任何单位符号。
            df['clean_data'] = df['data_raw'].astype(str).str.extract(r'([-+]?\d*\.?\d+)', expand=False)
            
            # 将提取出的字符串转换为数值类型，无法转换的变为NaN
            df[col_name] = pd.to_numeric(df['clean_data'], errors='coerce') * scale
            
            # 筛选掉时间或数据转换失败的行
            df = df.dropna(subset=['datetime', col_name])
            
            if not df.empty: # 只有当DataFrame非空时才添加
                dfs.append(df[['datetime', col_name]])
            else:
                print(f"警告: 文件 {file} 在清洗后没有有效数据。")

    if not dfs:
        print(f"错误: 未能从文件夹 {folder} 加载任何有效数据。请检查文件和路径。")
        return pd.DataFrame() # 返回空DataFrame
    return pd.concat(dfs).sort_values('datetime').reset_index(drop=True)


# ===== 文件夹路径定义 =====
wind_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\风速'
rain_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\降水量'
temp_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\温度数据'
soil_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\土壤湿度'
ssrd_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\下行辐射强度_ssrd'
dew_point_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\露点温度' 

# ===== 加载所有数据 =====
print("正在加载风速数据...")
wind_df = load_data(wind_folder, 'wind', 'm/s')
print("正在加载降水量数据...")
rain_df = load_data(rain_folder, 'rain', 'mm')
print("正在加载温度数据...")
temp_df = load_data(temp_folder, 'temp', '°C')
print("正在加载土壤湿度数据...")
soil_df = load_data(soil_folder, 'soil', 'm³/m³', scale=100) # 土壤湿度单位转为百分比
print("正在加载下行辐射强度数据...")
ssrd_df = load_data(ssrd_folder, 'ssrd', 'W/m²')
print("正在加载露点温度数据...")
dew_point_df = load_data(dew_point_folder, 'dew_point', '°C') # 加载露点温度数据

# 检查关键数据是否成功加载
if wind_df.empty or rain_df.empty or temp_df.empty or ssrd_df.empty or dew_point_df.empty:
    print("错误: 某些关键气象数据加载失败或为空，无法进行后续计算。请检查数据文件和路径。")
    exit() # 退出程序

# ===== 合并所有数据 =====
print("正在合并所有数据...")
df_all = wind_df.merge(rain_df, on='datetime', how='inner') \
                 .merge(temp_df, on='datetime', how='inner') \
                 .merge(ssrd_df, on='datetime', how='inner') \
                 .merge(dew_point_df, on='datetime', how='inner') \
                 .merge(soil_df, on='datetime', how='left') # 土壤湿度可能不是每天都有

# 去除重复的datetime，保留第一个，并按datetime排序
df_all = df_all.drop_duplicates(subset=['datetime']).sort_values('datetime').reset_index(drop=True)

# ===== IMPORTANT: Filter for 2025 data only =====
print("正在筛选2025年的数据...")
df_all_2025 = df_all[df_all['datetime'].dt.year == 2025].reset_index(drop=True)

if df_all_2025.empty:
    print("\n警告：在您提供的原始数据文件中，未找到任何2025年的气象数据。")
    print("本模拟将**无法**针对2025年进行计算。请确保您的Excel文件中包含2025年的数据（例如，数据时间戳为2025年）。")
    exit() # 如果没有2025年数据，则退出

df_all = df_all_2025 # 使用2025年过滤后的数据进行后续操作

# 确保 'datetime' 列是 datetime 格式
df_all['datetime'] = pd.to_datetime(df_all['datetime'])

# ===== 设定模拟日期范围 (与灌溉日期范围一致) =====
data_year_sim = 2025 # 显式设定模拟年份为2025
simulation_start = pd.Timestamp(f'{data_year_sim}-06-07') # 从6月7日开始模拟
simulation_end = pd.Timestamp(f'{data_year_sim}-06-28') # 模拟到6月28日

# 筛选出模拟期的数据
df_simulation_period = df_all[(df_all['datetime'].dt.date >= simulation_start.date()) & \
                              (df_all['datetime'].dt.date <= simulation_end.date())].copy()

if df_simulation_period.empty:
    print(f"错误: 在2025年的数据中，未找到 {simulation_start.date()} 至 {simulation_end.date()} 期间的数据。无法进行模拟。")
    exit()

# --- 灌溉决策参数 ---
OPTIMAL_MOISTURE_LOWER_BOUND = 65.0 # %
OPTIMAL_MOISTURE_UPPER_BOUND = 75.0 # %
FIELD_AREA_SQ_METERS = 1000.0 # 修改为 1000 平方米
CORN_ROOT_DEPTH_METERS = 1.0 # 示例值：1米，请根据农学数据或具体玉米品种调整

# --- 物理模型参数 ---
FIELD_CAPACITY = 78.0 # 土壤田间持水量 (%)，请根据您的土壤类型调整

# --- 作物阶段及对应Kc值 ---
# 根据您的要求，抽穗期为2025年6月7日至6月28日
CORN_GROWTH_STAGES = [
    {'stage': '初始阶段', 'start': '2025-05-15', 'end': '2025-06-06', 'Kc': 0.3}, # 调整结束日期
    {'stage': '中期阶段 (抽穗期)', 'start': '2025-06-07', 'end': '2025-06-28', 'Kc': 1.20}, # 用户要求：抽穗期
    {'stage': '晚期阶段', 'start': '2025-06-29', 'end': '2025-08-15', 'Kc': 0.6}, # 调整起始日期
]
# 将日期字符串转换为Timestamp对象以便比较
for stage in CORN_GROWTH_STAGES:
    stage['start'] = pd.Timestamp(stage['start'])
    stage['end'] = pd.Timestamp(stage['end'])

# --- Penman-Monteith 所需的站点及常数 (遵循FAO-56方法) ---
ELEVATION_M = 5.0 # 气象站海拔 (米)

# 纬度 (度)。FAO-56 Penman-Monteith需要，用于计算理论晴空辐射和日照时数。
# 这里使用无锡值，北纬31度。
# 请根据您的实际农田位置调整此值。
LATITUDE_DEG = 31.0 # 北纬31度

# 常数
GSC = 0.082 # 太阳常数 (MJ m^-2 min^-1)
SIGMA = 4.903e-9 # 斯特芬-玻尔兹曼常数 (MJ K^-4 m^-2 day^-1)
LAMBDA_WATER = 2.45 # 水的汽化潜热 (MJ kg^-1)

# --- 辅助函数：计算饱和水汽压 (kPa) ---
def es_calc(T_celsius):
    return 0.6108 * np.exp(17.27 * T_celsius / (T_celsius + 237.3))

# --- 辅助函数：计算平均饱和水汽压 (kPa) ---
def mean_es(T_celsius):
    return es_calc(T_celsius)

# --- 辅助函数：计算理论晴空辐射 (Rso, MJ m^-2 day^-1) ---
def calculate_rso(day_of_year, latitude_deg, elevation_m):
    lat_rad = np.deg2rad(latitude_deg)
    delta_solar = 0.409 * np.sin(2 * np.pi * day_of_year / 365 - 1.39)
    omega_s = np.arccos(-np.tan(lat_rad) * np.tan(delta_solar))
    Ra = (24 * 60 / np.pi) * GSC * ( (omega_s * np.sin(lat_rad) * np.sin(delta_solar)) + \
                                    (np.cos(lat_rad) * np.cos(delta_solar) * np.sin(omega_s)) )
    Rso = (0.75 + 2e-5 * elevation_m) * Ra
    return Rso

# --- 获取初始土壤湿度作为预测起点 ---
# 在模拟开始日期的土壤湿度数据，如果没有，则使用默认值70%
initial_soil_data = df_simulation_period[df_simulation_period['datetime'].dt.date == simulation_start.date()]['soil']
INITIAL_SOIL_MOISTURE = initial_soil_data.iloc[0] if not initial_soil_data.empty and not pd.isna(initial_soil_data.iloc[0]) else 70.0 

# --- 预测模拟 ---
predicted_soil_moisture = INITIAL_SOIL_MOISTURE
simulated_decisions = []

print(f"\n模拟开始时的初始土壤湿度 (预测起点): {INITIAL_SOIL_MOISTURE:.2f}%")

# 定义灌溉限定日期范围 (现在与模拟范围一致)
IRRIGATION_START_DATE = simulation_start.date()
IRRIGATION_END_DATE = simulation_end.date()
print(f"灌溉决策将只在 {IRRIGATION_START_DATE} 至 {IRRIGATION_END_DATE} 期间进行判断和触发。")


# 遍历模拟期数据，进行每日预测和决策
for index, row in df_simulation_period.iterrows():
    current_date = row['datetime']
    
    # 确定当前日期的作物系数 Kc
    KC_CORN_CURRENT_DAY = None
    current_stage_name = '未知阶段'
    for stage_info in CORN_GROWTH_STAGES:
        # 使用 .date() 确保只比较日期部分
        if stage_info['start'].date() <= current_date.date() <= stage_info['end'].date():
            KC_CORN_CURRENT_DAY = stage_info['Kc']
            current_stage_name = stage_info['stage']
            break
    
    if KC_CORN_CURRENT_DAY is None:
        # 即使跳过预测，也应该更新 simulated_decisions 列表以保持日期完整性
        simulated_decisions.append({
            '日期': current_date.date(),
            '作物阶段': '未知阶段', # 保持列名一致
            '当前Kc值': np.nan,
            '当日气温 (°C)': round(row['temp'], 2),
            '当日露点温度 (°C)': round(row['dew_point'], 2) if pd.notna(row['dew_point']) else np.nan,
            '当日风速 (m/s)': round(row['wind'], 2) if pd.notna(row['wind']) else np.nan,
            '当日降雨量 (mm)': round(row['rain'], 2) if pd.notna(row['rain']) else np.nan,
            '当日辐射 (W/m²)': round(row['ssrd'], 2) if pd.notna(row['ssrd']) else np.nan,
            '预测起始湿度 (%)': predicted_soil_moisture, # 使用前一天的结束湿度作为起始点
            '预测蒸散发 (mm)': np.nan,
            '预测结束湿度 (%)': predicted_soil_moisture, # 未预测，湿度保持不变
            '行动': '未定义作物阶段，无法预测',
            '建议灌溉水量 (m³)': 0
        })
        continue

    # 获取当天气象数据
    temp = row['temp'] # 平均气温 °C
    wind = row['wind'] # 风速 m/s
    rain = row['rain'] # 降雨量 mm
    ssrd = row['ssrd'] # 下行短波辐射强度 W/m²
    dew_point = row['dew_point'] # 露点温度 °C

    # 检查气象数据完整性
    if pd.isna(temp) or pd.isna(wind) or pd.isna(rain) or pd.isna(ssrd) or pd.isna(dew_point):
        simulated_decisions.append({
            '日期': current_date.date(),
            '作物阶段': current_stage_name, # 保持列名一致
            '当前Kc值': round(KC_CORN_CURRENT_DAY, 2),
            '当日气温 (°C)': round(temp, 2) if pd.notna(temp) else np.nan,
            '当日露点温度 (°C)': round(dew_point, 2) if pd.notna(dew_point) else np.nan,
            '当日风速 (m/s)': round(wind, 2) if pd.notna(wind) else np.nan,
            '当日降雨量 (mm)': round(rain, 2) if pd.notna(rain) else np.nan,
            '当日辐射 (W/m²)': round(ssrd, 2) if pd.notna(ssrd) else np.nan,
            '预测起始湿度 (%)': predicted_soil_moisture, # 使用前一天的结束湿度作为起始点
            '预测蒸散发 (mm)': np.nan,
            '预测结束湿度 (%)': predicted_soil_moisture, # 未预测，湿度保持不变
            '行动': '数据缺失，无法预测',
            '建议灌溉水量 (m³)': 0
        })
        print(f"警告: {current_date.date()} 的部分气象数据缺失。跳过当天预测。")
        continue

    # --- 1. 计算 Penman-Monteith ET0 (mm/day) ---
    # 大气压 (kPa) - FAO-56 Eq. 7
    P_kPa = 101.3 * ((293 - 0.00617 * ELEVATION_M) / 293)**5.26
    
    # 湿度常数 (kPa/°C) - FAO-56 Eq. 8
    gamma = 0.0016286 * P_kPa / LAMBDA_WATER
    
    # 饱和水汽压 (kPa) - FAO-56 Eq. 11 (使用平均温度近似)
    es_avg = mean_es(temp)
    
    # 实际水汽压 (kPa) - FAO-56 Eq. 13 (从露点温度计算)
    ea_dew_point = es_calc(dew_point)

    # 饱和水汽压差 (kPa)
    es_minus_ea = es_avg - ea_dew_point
    
    # 饱和水汽压曲线斜率 (kPa/°C) - FAO-56 Eq. 5
    delta = (4098 * es_avg) / (temp + 237.3)**2
    
    # 2米高处风速 (m/s) - FAO-56 Eq. 33 (假设原始数据已经是2米高度)
    u2 = wind 

    # 下行短波辐射强度 (ssrd) 从 W/m² 转换为 MJ/m²/day (日太阳辐射 Rs)
    # FAO-56 Table 1: 1 W/m2 = 0.0864 MJ/m2/day
    Rs_MJ_m2_day = ssrd * 0.0864 

    # 理论晴空辐射 (Rso, MJ m^-2 day^-1) - FAO-56 Eq. 19
    day_of_year = current_date.timetuple().tm_yday
    Rso_MJ_m2_day = calculate_rso(day_of_year, LATITUDE_DEG, ELEVATION_M)

    # 净短波辐射 (Rns, MJ m^-2 day^-1) - FAO-56 Eq. 38
    Rns_MJ_m2_day = (1 - 0.23) * Rs_MJ_m2_day # 反射率 albedo = 0.23 (参考作物草地)

    # 净长波辐射 (Rnl, MJ m^-2 day^-1) - FAO-56 Eq. 39
    # Clamp Rs_MJ_m2_day / Rso_MJ_m2_day between 0.3 and 1.0 (FAO-56 Note)
    if Rso_MJ_m2_day <= 0.01: # 避免除以零或极小数，通常发生在夜晚或极阴天
        fcd = 0.3 # 假设为最低值
    else:
        fcd = np.clip(Rs_MJ_m2_day / Rso_MJ_m2_day, 0.3, 1.0) # 修正光照比率

    Rnl_MJ_m2_day = SIGMA * (temp + 273.15)**4 * (0.34 - 0.14 * np.sqrt(ea_dew_point)) * \
                     fcd 

    # 净辐射 (Rn, MJ m^-2 day^-1) - FAO-56 Eq. 40
    Rn_MJ_m2_day = Rns_MJ_m2_day - Rnl_MJ_m2_day
    
    # Penman-Monteith ET0 公式 (mm/day) - FAO-56 Eq. 6
    # 分子项
    numerator = (0.408 * delta * Rn_MJ_m2_day) + (gamma * (900 / (temp + 273.15)) * u2 * es_minus_ea)
    # 分母项
    denominator = delta + gamma * (1 + 0.34 * u2)
    
    # 检查分母是否接近于零，以防除以零错误
    if denominator == 0:
        et0_daily_mm = 0 
    else:
        et0_daily_mm = numerator / denominator
    
    if et0_daily_mm < 0: et0_daily_mm = 0 # ET0 不能为负

    # 计算作物实际蒸散发 ETc (mm/day)，使用当前阶段的Kc
    etc_daily_mm = et0_daily_mm * KC_CORN_CURRENT_DAY 
    
    # --- 2. 考虑降雨对土壤湿度的影响 ---
    # 有效降雨量 (Effective Rainfall)
    # 简化处理：假设所有降雨在当天都转化为有效入渗。
    effective_rain_mm = rain

    # 将 mm 转换为等效的土壤湿度百分比变化 (1mm水深在1m根深土壤中约等于0.1%的体积含水率)
    etc_daily_percent = (etc_daily_mm / 1000) / CORN_ROOT_DEPTH_METERS * 100 
    rain_daily_percent = (effective_rain_mm / 1000) / CORN_ROOT_DEPTH_METERS * 100 

    # --- 3. 模拟土壤湿度变化 ---
    # 土壤水分平衡方程：新的预测湿度 = 上一日预测湿度 + 降雨 - 蒸散发
    predicted_soil_moisture_before_irrigation = predicted_soil_moisture + rain_daily_percent - etc_daily_percent

    # --- 4. 考虑深层渗漏 (当超过田间持水量时) ---
    deep_percolation_percent = 0
    if predicted_soil_moisture_before_irrigation > FIELD_CAPACITY:
        deep_percolation_percent = predicted_soil_moisture_before_irrigation - FIELD_CAPACITY
        predicted_soil_moisture_before_irrigation = FIELD_CAPACITY # 湿度不能超过田间持水量

    # --- 5. 做出灌溉决策 (基于预测值，并限定日期) ---
    irrigation_volume_m3 = 0
    action = "无需灌溉"
    
    current_predicted_moisture_for_decision = predicted_soil_moisture_before_irrigation

    # 检查当前日期是否在允许灌溉的范围内
    # 由于 simulation_start 和 simulation_end 已经限定了范围，
    # 这里的 if 语句在当前设置下会始终为真，但保留以示逻辑完整性
    if IRRIGATION_START_DATE <= current_date.date() <= IRRIGATION_END_DATE:
        if current_predicted_moisture_for_decision <= OPTIMAL_MOISTURE_LOWER_BOUND:
            action = "预测触发灌溉"
            # 灌溉后目标是达到 UPPER_BOUND
            water_needed_percent = OPTIMAL_MOISTURE_UPPER_BOUND - current_predicted_moisture_for_decision
            irrigation_volume_m3 = (water_needed_percent / 100.0) * FIELD_AREA_SQ_METERS * CORN_ROOT_DEPTH_METERS
            
            # 模拟灌溉后的土壤湿度 (这会影响第二天的预测起始点)
            predicted_soil_moisture = OPTIMAL_MOISTURE_UPPER_BOUND 
        else:
            # 如果不需要灌溉，则今天的预测结束湿度就是计算得出的湿度
            predicted_soil_moisture = current_predicted_moisture_for_decision
    else:
        # 如果不在灌溉限定日期内，即使湿度低于下限也不灌溉 (理论上，在当前模拟范围设置下，此分支不会被触发)
        action = "日期不在灌溉窗口"
        predicted_soil_moisture = current_predicted_moisture_for_decision


    simulated_decisions.append({
        '日期': current_date.date(),
        '作物阶段': current_stage_name, 
        '当前Kc值': round(KC_CORN_CURRENT_DAY, 2), 
        '当日气温 (°C)': round(temp, 2),
        '当日露点温度 (°C)': round(dew_point, 2),
        '当日风速 (m/s)': round(wind, 2),
        '当日降雨量 (mm)': round(rain, 2),
        '当日辐射 (W/m²)': round(ssrd, 2),
        '预测起始湿度 (%)': round(predicted_soil_moisture_before_irrigation + etc_daily_percent - rain_daily_percent + deep_percolation_percent, 2), 
        '预测蒸散发 (mm)': round(etc_daily_mm, 2),
        '预测结束湿度 (%)': round(predicted_soil_moisture, 2), 
        '行动': action,
        '建议灌溉水量 (m³)': round(irrigation_volume_m3, 2)
    })

df_simulated_decisions = pd.DataFrame(simulated_decisions)
print("\n--- 基于气象数据 (包含露点温度)、Penman-Monteith 模型和作物阶段Kc的模拟灌溉决策 ---")
print(f"模拟灌溉日期范围：从 {simulation_start.date()} 到 {simulation_end.date()}") 

# 移除了打印每日详细表格的代码行：
# print(df_simulated_decisions.set_index('日期'))

# === 新增：输出每次灌溉的日期和灌水量 ===
print("\n--- 详细灌溉事件列表 ---")
irrigation_events = df_simulated_decisions[df_simulated_decisions['行动'] == '预测触发灌溉']
if not irrigation_events.empty:
    for index, row in irrigation_events.iterrows():
        print(f"日期: {row['日期']} | 灌溉水量: {row['建议灌溉水量 (m³)']} m³")
else:
    print("模拟期间未触发任何灌溉事件。")
# ==========================================

# 总结模拟结果
total_sim_irrigations = df_simulated_decisions[df_simulated_decisions['行动'] == '预测触发灌溉'].shape[0]
total_water_used_m3 = df_simulated_decisions[df_simulated_decisions['行动'] == '预测触发灌溉']['建议灌溉水量 (m³)'].sum()

print(f"\n模拟总灌溉次数: {total_sim_irrigations}")
print(f"模拟总用水量: {total_water_used_m3:.2f} m³")


# ===== 可视化展示灌水土壤湿度的变化 =====
plt.figure(figsize=(15, 7))
plt.plot(df_simulated_decisions['日期'], df_simulated_decisions['预测结束湿度 (%)'], 
          marker='o', linestyle='-', color='skyblue', label='预测结束土壤湿度')

# 添加最适湿度区间
plt.axhline(y=OPTIMAL_MOISTURE_LOWER_BOUND, color='red', linestyle='--', label=f'最适湿度下限 ({OPTIMAL_MOISTURE_LOWER_BOUND}%)')
plt.axhline(y=OPTIMAL_MOISTURE_UPPER_BOUND, color='green', linestyle='--', label=f'最适湿度上限 ({OPTIMAL_MOISTURE_UPPER_BOUND}%)')

# 标记灌溉事件 (调整了 s 参数，使其更大更明显)
irrigation_dates = df_simulated_decisions[df_simulated_decisions['行动'] == '预测触发灌溉']['日期']
irrigation_moisture = df_simulated_decisions[df_simulated_decisions['行动'] == '预测触发灌溉']['预测结束湿度 (%)']
if not irrigation_dates.empty:
    # 确保只在图例中显示一次“灌溉事件”
    plt.scatter(irrigation_dates, irrigation_moisture, color='purple', marker='^', s=150, zorder=5, label='灌溉事件') 
    # 绘制垂直线以更清晰地指示灌溉日期，不添加额外的图例项
    for date in irrigation_dates:
        plt.axvline(x=date, color='purple', linestyle=':', linewidth=1.5, alpha=0.7)

# 自定义图表
plt.title(f'2025年玉米 ({simulation_start.date()} - {simulation_end.date()}) 土壤湿度变化与灌溉决策\n(作物面积: {FIELD_AREA_SQ_METERS} m^2)\n注意：图中灌溉事件点可能因日期密集而重叠，实际触发次数请参考下方文字输出')
plt.xlabel('日期')
plt.ylabel('土壤湿度 (%)')
plt.ylim(min(OPTIMAL_MOISTURE_LOWER_BOUND - 5, df_simulated_decisions['预测结束湿度 (%)'].min() - 5), 
          max(OPTIMAL_MOISTURE_UPPER_BOUND + 5, df_simulated_decisions['预测结束湿度 (%)'].max() + 5))
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.xticks(rotation=45, ha='right') 
plt.tight_layout() 
plt.show()