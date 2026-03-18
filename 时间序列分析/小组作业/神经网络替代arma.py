import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys 
import warnings

# --- 1. 導入必需庫 ---
# (確保已安裝: pip install tensorflow scikit-learn pandas numpy matplotlib)
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LayerNormalization, Dropout, MultiHeadAttention, GlobalAveragePooling1D, TimeDistributed, Add, Embedding
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping # <-- 用於防止過擬合
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split # <-- 用於劃分數據集

# --- 2. 全局設置 ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')
# (設置隨機種子以保證可複現性)
tf.random.set_seed(42)
np.random.seed(42)

# === 3. 加載【所有】本地數據 (無日期篩選) ===
file_path_local = r"C:\study\时间序列分析\小组作业\CSI300_Tencent_2020_to_today.csv"

try:
    df_full = pd.read_csv(file_path_local, parse_dates=['Date'], index_col='Date')
except FileNotFoundError:
    print(f"错误：文件未找到 {file_path_local}")
    sys.exit()

# --- (修改點 1: 使用所有數據，僅 ClosePrice) ---
ts = df_full['ClosePrice'].dropna() 
print(f"本地 CSI300 【所有】數據加載成功: {len(ts)} 條記錄。")
# --- (修改結束) ---

# === 4. 數據準備 (縮放、創建監督學習數據集、劃分訓練/驗證集) ===
print("\n--- 4. 正在準備數據 ---")

# 4.1 數據縮放 (至 [0, 1])
scaler = MinMaxScaler(feature_range=(0, 1))
# (注意：reshape(-1, 1) 是因為 scaler 需要 2D 輸入)
dataset_scaled = scaler.fit_transform(ts.values.reshape(-1, 1))

# 4.2 創建監督學習數據集 (X=過去 look_back 天, y=今天)
def create_dataset(data, look_back=20): # <-- 嘗試用更長的 look_back
    X, Y = [], []
    for i in range(len(data) - look_back - 1):
        a = data[i:(i + look_back), 0]
        X.append(a)
        Y.append(data[i + look_back, 0])
    # 返回 NumPy 數組
    return np.array(X), np.array(Y)

look_back = 20 # <-- 超參數：用過去 20 天的價格預測第 21 天
X_scaled, y_scaled = create_dataset(dataset_scaled, look_back)

# 4.3 (關鍵!) 劃分訓練集和驗證集 (防止過擬合)
# 對於時間序列，必須按時間順序劃分，不能隨機打亂
# 我們用 80% 的數據訓練，最後 20% 的數據驗證
train_size = int(len(X_scaled) * 0.8)
val_size = len(X_scaled) - train_size

train_X, val_X = X_scaled[0:train_size,:], X_scaled[train_size:len(X_scaled),:]
train_y, val_y = y_scaled[0:train_size], y_scaled[train_size:len(y_scaled)]

# 4.4 重塑 X 以符合 Transformer 輸入要求 [samples, time_steps, features]
# (這裡是單變量，所以 features=1)
train_X = np.reshape(train_X, (train_X.shape[0], train_X.shape[1], 1))
val_X = np.reshape(val_X, (val_X.shape[0], val_X.shape[1], 1))

print(f"數據準備完成:")
print(f"  訓練集 X 形狀: {train_X.shape}, y 形狀: {train_y.shape}")
print(f"  驗證集 X 形狀: {val_X.shape}, y 形狀: {val_y.shape}")

# === 5. 构建 Transformer 模型 ===
print("\n--- 5. 正在构建 Transformer 模型 ---")

# (這是一個簡化的 Transformer Encoder 塊，與之前類似)
def transformer_encoder(inputs, head_size, num_heads, ff_dim, dropout=0):
    # Attention and Normalization
    x = MultiHeadAttention(
        key_dim=head_size, num_heads=num_heads, dropout=dropout
    )(inputs, inputs)
    x = Dropout(dropout)(x)
    x = LayerNormalization(epsilon=1e-6)(Add()([inputs, x])) # Residual connection

    # Feed Forward
    ffn = tf.keras.Sequential(
        [Dense(ff_dim, activation="relu"), Dense(inputs.shape[-1])]
    )
    x_ff = ffn(x)
    x_ff = Dropout(dropout)(x_ff)
    x = LayerNormalization(epsilon=1e-6)(Add()([x, x_ff])) # Residual connection
    return x

# --- (新增) 位置編碼 ---
# Transformer 需要知道序列中元素的位置信息
# 我們使用可學習的位置嵌入 (Learnable Positional Embedding)
def build_transformer_model(input_shape, head_size, num_heads, ff_dim, num_transformer_blocks, mlp_units, dropout=0, mlp_dropout=0):
    inputs = Input(shape=input_shape)
    x = inputs # Shape: (batch_size, sequence_length, feature_dim)
    
    # --- 位置嵌入 ---
    sequence_length = input_shape[0]
    position_indices = tf.range(start=0, limit=sequence_length, delta=1)
    position_embeddings = Embedding(input_dim=sequence_length, output_dim=input_shape[-1])(position_indices)
    # 將位置嵌入添加到輸入特徵 (Broadcasting)
    x = Add()([x, position_embeddings])
    # --- 位置嵌入結束 ---

    # --- Transformer 塊 ---
    for _ in range(num_transformer_blocks):
        x = transformer_encoder(x, head_size, num_heads, ff_dim, dropout)
    # --- Transformer 塊結束 ---

    # --- 輸出處理 ---
    x = GlobalAveragePooling1D(data_format="channels_last")(x)
    for dim in mlp_units:
        x = Dense(dim, activation="relu")(x)
        x = Dropout(mlp_dropout)(x)
    outputs = Dense(1)(x) # 最終輸出一個值
    # --- 輸出處理結束 ---
    
    return Model(inputs, outputs)

# --- 模型超參數 ---
input_shape = train_X.shape[1:] # (look_back, 1)
head_size = 64
num_heads = 2
ff_dim = 64 # 隱藏層大小
num_transformer_blocks = 2 # 堆疊 2 個 Transformer 塊
mlp_units = [32] # 輸出前的 MLP 層
dropout = 0.1
mlp_dropout = 0.1

model = build_transformer_model(
    input_shape,
    head_size=head_size,
    num_heads=num_heads,
    ff_dim=ff_dim,
    num_transformer_blocks=num_transformer_blocks,
    mlp_units=mlp_units,
    dropout=dropout,
    mlp_dropout=mlp_dropout,
)

model.compile(loss="mean_squared_error", optimizer=Adam(learning_rate=1e-4))
model.summary()

# --- (關鍵!) 早停法回調函數 ---
# 監控驗證集損失 (val_loss)，如果 5 個 epoch 沒有改善就停止訓練
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# === 6. 訓練 Transformer 模型 ===
print("\n--- 6. 開始訓練 Transformer 模型 (帶早停)... ---")
history = model.fit(
    train_X,
    train_y,
    validation_data=(val_X, val_y),
    epochs=100, # <-- 設置一個較大的數，讓早停來決定最佳輪數
    batch_size=32,
    callbacks=[early_stopping],
    verbose=1 # 顯示進度條
)

print("\n--- Transformer 訓練完成 ---")

# === 7. 評估模型 (在驗證集上) ===
print("\n--- 7. 正在評估模型 ---")

# 7.1 做出預測 ( scaled )
val_predictions_scaled = model.predict(val_X, verbose=0)

# 7.2 (關鍵!) 逆向縮放回原始價格尺度
val_predictions = scaler.inverse_transform(val_predictions_scaled)
val_y_orig = scaler.inverse_transform(val_y.reshape(-1, 1))

# 7.3 計算 RMSE (在原始尺度上)
rmse = np.sqrt(mean_squared_error(val_y_orig, val_predictions))
print(f"\n模型在驗證集上的 RMSE (原始尺度): {rmse:.4f}")
print("  - RMSE 越低越好，表示模型對【未見過數據】的預測準確度。")

# 7.4 繪製預測結果 vs 真實值 (在驗證集上)
plt.figure(figsize=(12, 6))
plt.plot(ts.index[-len(val_y_orig):], val_y_orig, label='真實收盤價 (驗證集)', color='blue', alpha=0.7)
plt.plot(ts.index[-len(val_predictions):], val_predictions, label=f'Transformer 預測值 (RMSE: {rmse:.2f})', color='red', linestyle='--')
plt.title("純 Transformer 模型預測 vs 真實值 (驗證集)")
plt.xlabel("日期")
plt.ylabel("指數點位")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

print("\n--- 完整分析代碼執行完畢 ---")