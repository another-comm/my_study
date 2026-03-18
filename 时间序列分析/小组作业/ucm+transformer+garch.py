import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import warnings

# --- 导入模型库 ---
# 1. Prophet (替代 UCM)
from prophet import Prophet

# 2. Transformer (TensorFlow)
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Input, Dense, LayerNormalization, Dropout, MultiHeadAttention, GlobalAveragePooling1D
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

# 3. GARCH
try:
    from statsmodels.stats.diagnostic import het_arch
    from arch import arch_model
    garch_enabled = True
except ImportError:
    print("警告：未能导入 GARCH 依赖 (statsmodels 或 arch)。跳过第 4 步。")
    garch_enabled = False


# --- 1.A. 全局设置 ---
plt.rcParams['font.sans-serif'] = ['SimHei']  # 'SimHei' 是黑体
plt.rcParams['axes.unicode_minus'] = False    # 正确显示负号
warnings.filterwarnings('ignore')
# (设置随机种子以保证 Transformer 训练的可复现性)
tf.random.set_seed(42)
np.random.seed(42)

# === 1.B. 加载本地数据 ===
file_path_local = r"C:\study\时间序列分析\小组作业\CSI300_Tencent_2020_to_today.csv"

try:
    df_full = pd.read_csv(file_path_local, parse_dates=['Date'], index_col='Date')
except FileNotFoundError:
    print(f"错误：文件未找到 {file_path_local}")
    sys.exit()

df = df_full[df_full.index >= pd.Timestamp("2022-01-01")].copy()
ts = df['ClosePrice'].dropna() # <-- 这是我们唯一的数据 Y_t
print(f"本地 CSI300 数据加载成功: {len(ts)} 条记录。")


# === 2. (蓝图第1步) Prophet 动态分解 (替代 UCM) ===
print("\n--- 2. 正在运行 Prophet (第一步：拟合 T_t 和 S_t)... ---")

# (Prophet 需要 'ds' 和 'y' 格式的列名)
df_prophet = ts.reset_index().rename(columns={'Date': 'ds', 'ClosePrice': 'y'})

try:
    # 初始化 Prophet
    model_prophet = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05 
    )
    
    # 拟合 Prophet
    model_prophet.fit(df_prophet)

    # 获取历史拟合值 (用于计算残差)
    fitted_prophet = model_prophet.predict(df_prophet)
    
    # 提取残差 R_t = Y_t - (T_t + S_t)
    prophet_components = pd.Series(
        fitted_prophet['yhat'].values, 
        index=ts.index 
    )
    ucm_residual = ts - prophet_components
    ucm_residual.name = 'resid'
    
    print("正在绘制 Prophet 分解图...")
    fig = model_prophet.plot_components(fitted_prophet)
    plt.show()

except Exception as e:
    print(f"Prophet 拟合失败: {e}")
    sys.exit()

print(f"Prophet 分解完成。残差 (R_t) 序列长度: {len(ucm_residual)}")


# === 3. (蓝图第2步) Transformer 拟合残差 ===
print("\n--- 3. 正在准备 Transformer (第二步：拟合 R_t)... ---")

# 3.1 准备数据
dataset = ucm_residual.values.reshape(-1, 1)
scaler = MinMaxScaler(feature_range=(0, 1))
dataset_scaled = scaler.fit_transform(dataset)

# 3.2 创建监督学习数据集
def create_dataset(data, look_back=15): # look_back 设为 15
    X, Y = [], []
    for i in range(len(data) - look_back - 1):
        a = data[i:(i + look_back), 0]
        X.append(a)
        Y.append(data[i + look_back, 0])
    return np.array(X), np.array(Y)

look_back = 15
train_X, train_Y = create_dataset(dataset_scaled, look_back)

# 重塑 X [samples, time_steps, features]
train_X = np.reshape(train_X, (train_X.shape[0], train_X.shape[1], 1))
print(f"已创建监督学习数据集，X 形状: {train_X.shape}, Y 形状: {train_Y.shape}")

# 3.3 构建 Transformer 模型
def transformer_encoder(inputs, head_size=128, num_heads=4, ff_dim=128, dropout=0.1):
    x = MultiHeadAttention(
        key_dim=head_size, num_heads=num_heads, dropout=dropout
    )(inputs, inputs)
    x = Dropout(dropout)(x)
    x = LayerNormalization(epsilon=1e-6)(x + inputs) # Add & Norm
    ffn = Sequential(
        [Dense(ff_dim, activation="relu"), Dense(inputs.shape[-1])]
    )
    x_ff = ffn(x)
    x_ff = Dropout(dropout)(x_ff)
    x = LayerNormalization(epsilon=1e-6)(x + x_ff) # Add & Norm
    return x

inputs = Input(shape=(look_back, 1))
x = inputs
# --- !!! 修改 1: 增加了模型复杂度 !!! ---
x = transformer_encoder(x, head_size=128, num_heads=4, ff_dim=128, dropout=0.1)
x = GlobalAveragePooling1D(data_format="channels_last")(x)
outputs = Dense(1)(x)
model_transformer = Model(inputs, outputs)
model_transformer.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=1e-3))
model_transformer.summary()

# --- !!! 修改 2: 增加了训练周期 !!! ---
print("\n--- 开始训练 Transformer 模型 (epochs=300)... ---")
model_transformer.fit(train_X, train_Y, epochs=300, batch_size=32, verbose=1) # (原为 30)

# 3.4 获取拟合值与残差 (ε_t)
print("\n--- Transformer 拟合完成 ---")
fitted_values_scaled = model_transformer.predict(train_X, verbose=0)
fitted_values_tf = scaler.inverse_transform(fitted_values_scaled).flatten()
fitted_padding = [np.nan] * (len(ucm_residual) - len(fitted_values_tf))
fitted_values_full_R = pd.Series(fitted_padding + list(fitted_values_tf), index=ucm_residual.index)
residuals_from_tf = (ucm_residual - fitted_values_full_R).dropna() # 这是 epsilon_t

# 3.5 定义预测函数 (用于第5步)
def transformer_forecast(steps):
    print(f"正在使用 Transformer (look_back={look_back}) 进行 {steps} 步自回归预测...")
    last_input_scaled = dataset_scaled[-look_back:].reshape(1, look_back, 1)
    predictions_scaled = []
    current_input = last_input_scaled
    for _ in range(steps):
        pred_next = model_transformer.predict(current_input, verbose=0)
        predictions_scaled.append(pred_next[0, 0])
        current_input = np.roll(current_input, -1, axis=1)
        current_input[0, -1, 0] = pred_next[0, 0]
    predictions = scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1)).flatten()
    return predictions


# === 4. (蓝图第3步) GARCH 拟合 Transformer 残差 ===
print("\n--- 4. 正在运行 GARCH (第三步：拟合 ε_t)... ---")

if garch_enabled:
    residuals_for_garch = residuals_from_tf
    print("正在绘制 Transformer 残差 (ε_t) 时序图...")
    plt.figure(figsize=(10, 5))
    residuals_for_garch.plot(alpha=0.8, label='Transformer 残差 (ε_t)')
    plt.title("Transformer 模型残差 (ε_t) 时序图 (异方差观察)")
    plt.xlabel("日期"); plt.ylabel("残差值"); plt.axhline(0, color='grey', linestyle='--');
    plt.grid(True, linestyle=':'); plt.legend(); plt.tight_layout(); plt.show()
    
    arch_test_result = het_arch(residuals_for_garch, nlags=5)
    print(f'ARCH-LM 检验 P-value: {arch_test_result[1]}')
    garch_result = None
    if arch_test_result[1] < 0.05:
        print("结论：p-value < 0.05，残差 ε_t 存在显著ARCH效应。")
        print("正在拟合 GARCH(1,1)...")
        garch_model = arch_model(residuals_for_garch, vol='Garch', p=1, q=1, mean='Zero', dist='t')
        garch_result = garch_model.fit(disp='off')
        print(garch_result.summary())
    else:
        print("结论：p-value > 0.05，残差中没有显著的ARCH效应。")
else:
    print("已跳过 GARCH 分析 (库导入失败)。")


# === 5. 最终组合预测 (Prophet + Transformer) ===
print("\n--- 5. 最终组合预测 ---")
n_forecast = 10
last_date = ts.index[-1]

# 1. 预测 Prophet (T_t + S_t)
future_df = model_prophet.make_future_dataframe(periods=n_forecast, freq='B') 
prophet_forecast_obj = model_prophet.predict(future_df)
forecast_components = prophet_forecast_obj[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(n_forecast)

forecast_index = forecast_components['ds']
prophet_forecast_values = forecast_components['yhat'] # T_t + S_t 预测
prophet_conf_int_df = forecast_components[['yhat_lower', 'yhat_upper']]

# --- !!! 修改 3: 修复了 KeyError !!! ---
prophet_conf_int_df.columns = ['Lower 95%', 'Upper 95%'] # (原为 'Upper 95')

prophet_conf_int_df.index = forecast_index

# 2. 预测 Transformer (R_t)
tf_forecast = transformer_forecast(n_forecast)

# 3. 组合 (Y_t = (T_t + S_t) + R_t)
final_forecast_values = prophet_forecast_values.values + tf_forecast
final_conf_int_lower = prophet_conf_int_df['Lower 95%'].values + tf_forecast
final_conf_int_upper = prophet_conf_int_df['Upper 95%'].values + tf_forecast

forecast_series = pd.Series(final_forecast_values, index=forecast_index)
final_conf_int_df = pd.DataFrame({'Lower 95%': final_conf_int_lower, 'Upper 95%': final_conf_int_upper}, index=forecast_index)

print(f"\n--- 最终组合预测结果 ---")
print(final_conf_int_df.to_string(float_format="%.4f"))

# === 6. 绘图与评估 ===
print("\n--- 6. 绘图与评估 ---")
# 历史拟合值 = Prophet拟合(T_t + S_t) + Transformer拟合(R_t)
model_fitted_values = (prophet_components + fitted_values_full_R).dropna()

# 计算 RMSE
common_index = model_fitted_values.index
ts_aligned = ts.loc[common_index]
rmse_final = np.sqrt(mean_squared_error(ts_aligned, model_fitted_values))
print(f"\n模型 (Prophet+Transformer) 拟合优度 RMSE: {rmse_final:.4f}")

# 绘制 2025年以来局部放大图
ts_zoom = ts[ts.index.year >= 2025]
model_fitted_zoom = model_fitted_values[model_fitted_values.index.year >= 2025]
plt.figure(figsize=(10, 5))
plt.plot(ts_zoom, label='原始观测值 (2025+)', alpha=0.7)
plt.plot(model_fitted_zoom, label=f'Prophet+Transformer 拟合值 (RMSE: {rmse_final:.2f})', color='green', linestyle='--')
plt.plot(forecast_series, label="组合模型预测值 (未来)", color='red', marker='o')
plt.fill_between(forecast_index, final_conf_int_df['Lower 95%'], final_conf_int_df['Upper 95%'], color='red', alpha=0.15, label="95% 置信区间 (Prophet)")
plt.title(f"Prophet-Transformer-GARCH 组合模型拟合与预测 (2025年以来)")
plt.xlabel("日期"); plt.ylabel("指数点位"); plt.legend(); plt.grid(True); plt.tight_layout(); plt.show()

print("\n--- 完整分析代码执行完毕 ---")