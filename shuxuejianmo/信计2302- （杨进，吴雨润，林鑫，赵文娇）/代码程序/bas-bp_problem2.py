import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, mean_squared_error
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random # 用于BAS算法的随机性


# --- 在这里添加字体设置 ---
import matplotlib.font_manager as fm
plt.rcParams['font.sans-serif'] = ['SimHei']  # 尝试使用 SimHei 字体
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题
# --- 字体设置结束 ---

# ... 后续的数据加载、处理、模型定义和训练代码 ...
# ===== 数据路径 (保持不变) =====
wind_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\风速'
rain_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\降水量'
temp_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\温度数据'
soil_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\土壤湿度'
ssrd_folder = r'C:\Users\32610\Desktop\shuxuejianmo\数据\下行辐射强度_ssrd'

# ===== 通用数据读取函数 (保持不变) =====
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
            df.columns = ['datetime', col_name]
            df[col_name] = df[col_name].astype(str).str.replace(unit, '').str.strip().astype(float) * scale
            df['datetime'] = pd.to_datetime(df['datetime'])
            dfs.append(df)
    return pd.concat(dfs).sort_values('datetime').reset_index(drop=True)

# ===== 加载所有数据 (保持不变) =====
wind_df = load_data(wind_folder, 'wind', 'm/s')
rain_df = load_data(rain_folder, 'rain', 'mm')
temp_df = load_data(temp_folder, 'temp', '°C')
soil_df = load_data(soil_folder, 'soil', 'm³/m³', scale=100) # 土壤湿度单位转为百分比
ssrd_df = load_data(ssrd_folder, 'ssrd', 'W/m²')

# ===== 合并所有数据 (保持不变) =====
df_all = wind_df.merge(rain_df, on='datetime', how='inner') \
                 .merge(temp_df, on='datetime', how='inner') \
                 .merge(ssrd_df, on='datetime', how='inner') \
                 .merge(soil_df, on='datetime', how='left')

# ===== 只保留6-7月数据 (保持不变) =====
df_all = df_all[df_all['datetime'].dt.month.isin([6, 7])].reset_index(drop=True)

# ===== 引入时序特征 (新增部分) =====
# 提取年份，方便后续分组分析 (保持不变)
df_all['year'] = df_all['datetime'].dt.year

# 定义要进行滞后操作的特征和滞后步长
features_to_lag = ['wind', 'rain', 'temp', 'ssrd', 'soil']
lags = [1, 3, 6] # 滞后1小时、3小时、6小时

for feature in features_to_lag:
    for lag in lags:
        df_all[f'{feature}_t-{lag}'] = df_all[feature].shift(lag)

# 移除由于滞后操作而产生的NaN行
df_all.dropna(inplace=True)
df_all.reset_index(drop=True, inplace=True)

# 重新构造训练特征与标签
# 原始特征
current_features = ['wind', 'rain', 'temp', 'ssrd']
# 滞后特征
lagged_feature_names = [f'{f}_t-{l}' for f in features_to_lag for l in lags]

X_raw = df_all[current_features + lagged_feature_names] # 输入特征：当前和滞后气象变量、滞后土壤湿度
y_raw = df_all['soil'] # 标签：当前土壤湿度

print(f"原始特征数量: {len(current_features)}")
print(f"滞后特征数量: {len(lagged_feature_names)}")
print(f"总输入特征数量: {X_raw.shape[1]}")
print(f"经过滞后处理和NaN移除后，数据样本数量: {df_all.shape[0]}")


# ===== 标准化 (y_scaled 保持为 2D 数组) =====
scaler_X = StandardScaler()
scaler_y = StandardScaler()
X_scaled = scaler_X.fit_transform(X_raw.values) # 将 X_raw 转换为 NumPy 数组再拟合
y_scaled = scaler_y.fit_transform(y_raw.values.reshape(-1, 1))

# ===== 自定义BP神经网络实现 (引入Adam优化器，无变化) =====
class CustomBPNeuralNetwork:
    def __init__(self, input_size, hidden_sizes, output_size, activation='relu', 
                 learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-8):
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.activation = activation
        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.weights = []
        self.biases = []
        self.loss_curve = [] # 记录训练损失
        self.m_w, self.v_w = [], []
        self.m_b, self.v_b = [], []
        self.t = 0 # time step for Adam

    def _initialize_weights_biases(self, initial_params=None):
        layer_sizes = [self.input_size] + list(self.hidden_sizes) + [self.output_size]
        
        if initial_params is not None:
            param_idx = 0
            for i in range(len(layer_sizes) - 1):
                w_shape = (layer_sizes[i], layer_sizes[i+1])
                b_shape = (layer_sizes[i+1],)
                
                num_weights = w_shape[0] * w_shape[1]
                num_biases = b_shape[0]
                
                self.weights.append(initial_params[param_idx : param_idx + num_weights].reshape(w_shape))
                param_idx += num_weights
                
                self.biases.append(initial_params[param_idx : param_idx + num_biases].reshape(b_shape))
                param_idx += num_biases
        else:
            for i in range(len(layer_sizes) - 1):
                w = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * np.sqrt(2.0 / layer_sizes[i])
                self.weights.append(w)
                b = np.zeros((layer_sizes[i+1],))
                self.biases.append(b)
        
        self.m_w = [np.zeros_like(w) for w in self.weights]
        self.v_w = [np.zeros_like(w) for w in self.weights]
        self.m_b = [np.zeros_like(b) for b in self.biases]
        self.v_b = [np.zeros_like(b) for b in self.biases]
        self.t = 0

    def _relu(self, x):
        return np.maximum(0, x)

    def _relu_derivative(self, x):
        return (x > 0).astype(float)

    def _forward(self, X):
        self.activations = [X]
        self.z_values = [] 

        a = X
        for i in range(len(self.weights)):
            z = np.dot(a, self.weights[i]) + self.biases[i]
            self.z_values.append(z)
            if i == len(self.weights) - 1: 
                a = z 
            else:
                a = self._relu(z)
            self.activations.append(a)
        return a

    def _backward(self, X, y_true, y_pred):
        grads_w = [np.zeros_like(w) for w in self.weights]
        grads_b = [np.zeros_like(b) for b in self.biases]

        delta = y_pred - y_true
        
        for i in reversed(range(len(self.weights))):
            grad_w = np.dot(self.activations[i].T, delta)
            grad_b = np.sum(delta, axis=0) 
            
            grads_w[i] = grad_w
            grads_b[i] = grad_b

            if i != 0: 
                delta = np.dot(delta, self.weights[i].T) * self._relu_derivative(self.z_values[i-1])
        
        return grads_w, grads_b

    def train(self, X, y, epochs=100, batch_size=32, validation_split=0.1, verbose=False):
        num_samples = X.shape[0]
        val_samples = int(num_samples * validation_split)
        train_X, val_X = X[val_samples:], X[:val_samples]
        train_y, val_y = y[val_samples:], y[:val_samples]

        n_batches_train = len(train_X) // batch_size
        
        best_val_loss = float('inf')
        epochs_no_improve = 0
        patience = 3000 # 早停机制的耐心值，连续多少个epoch验证损失没有改善就停止,
                        # 设置为3000相当于没有早停

        for epoch in range(epochs):
            self.t += 1 

            permutation = np.random.permutation(len(train_X))
            shuffled_X = train_X[permutation]
            shuffled_y = train_y[permutation]

            epoch_train_loss = 0
            for i in range(n_batches_train):
                start = i * batch_size
                end = start + batch_size
                X_batch = shuffled_X[start:end]
                y_batch = shuffled_y[start:end]

                y_pred = self._forward(X_batch)
                
                loss = np.mean((y_pred - y_batch)**2)
                epoch_train_loss += loss

                grads_w, grads_b = self._backward(X_batch, y_batch, y_pred)

                for j in range(len(self.weights)):
                    self.m_w[j] = self.beta1 * self.m_w[j] + (1 - self.beta1) * grads_w[j]
                    self.v_w[j] = self.beta2 * self.v_w[j] + (1 - self.beta2) * (grads_w[j]**2)
                    m_w_hat = self.m_w[j] / (1 - self.beta1**self.t)
                    v_w_hat = self.v_w[j] / (1 - self.beta2**self.t)
                    self.weights[j] -= self.learning_rate * m_w_hat / (np.sqrt(v_w_hat) + self.epsilon)

                    self.m_b[j] = self.beta1 * self.m_b[j] + (1 - self.beta1) * grads_b[j]
                    self.v_b[j] = self.beta2 * self.v_b[j] + (1 - self.beta2) * (grads_b[j]**2)
                    m_b_hat = self.m_b[j] / (1 - self.beta1**self.t)
                    v_b_hat = self.v_b[j] / (1 - self.beta2**self.t)
                    self.biases[j] -= self.learning_rate * m_b_hat / (np.sqrt(v_b_hat) + self.epsilon)
            
            avg_train_loss = epoch_train_loss / n_batches_train
            self.loss_curve.append(avg_train_loss)

            if len(val_X) > 0:
                val_pred = self._forward(val_X)
                val_loss = np.mean((val_pred - val_y)**2)
                if verbose:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}")

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    epochs_no_improve = 0
                else:
                    epochs_no_improve += 1
                    if epochs_no_improve >= patience:
                        if verbose:
                            print(f"Early stopping at epoch {epoch+1}")
                        break
            else:
                if verbose:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {avg_train_loss:.4f}")

    def predict(self, X):
        return self._forward(X)

    def get_flattened_params(self):
        params = []
        for w in self.weights:
            params.extend(w.flatten())
        for b in self.biases:
            params.extend(b.flatten())
        return np.array(params)

    def set_flattened_params(self, new_params):
        param_idx = 0
        for i in range(len(self.weights)):
            w_shape = self.weights[i].shape
            num_weights = w_shape[0] * w_shape[1]
            self.weights[i] = new_params[param_idx : param_idx + num_weights].reshape(w_shape)
            param_idx += num_weights
            
            b_shape = self.biases[i].shape
            num_biases = b_shape[0]
            self.biases[i] = new_params[param_idx : param_idx + num_biases].reshape(b_shape)
            param_idx += num_biases


# ===== BAS算法 (无变化) =====
def bas_optimize_initial_params(X_train, y_train, input_size, hidden_sizes, output_size, 
                                max_bas_iterations=100, initial_delta=10, eta=0.95):
    
    temp_bp_net = CustomBPNeuralNetwork(input_size, hidden_sizes, output_size)
    temp_bp_net._initialize_weights_biases() 
    k = len(temp_bp_net.get_flattened_params()) 

    delta = initial_delta 
    best_fitness = float('inf')
    best_params = np.random.uniform(-0.5, 0.5, k) 

    for iter_bas in range(max_bas_iterations):
        b_vec = np.random.randn(k)
        b_vec = b_vec / np.linalg.norm(b_vec) 

        x_left = best_params - 0.5 * delta * b_vec
        x_right = best_params + 0.5 * delta * b_vec

        temp_bp_net.set_flattened_params(x_right)
        y_pred_right = temp_bp_net.predict(X_train)
        fitness_right = np.mean((y_pred_right - y_train)**2) 

        temp_bp_net.set_flattened_params(x_left)
        y_pred_left = temp_bp_net.predict(X_train)
        fitness_left = np.mean((y_pred_left - y_train)**2) 

        if fitness_right < fitness_left:
            best_params = best_params - delta * b_vec
        else:
            best_params = best_params + delta * b_vec
        
        delta = delta * eta

        current_fitness = min(fitness_left, fitness_right)
        if current_fitness < best_fitness:
            best_fitness = current_fitness
            
        if iter_bas % 10 == 0 or iter_bas == max_bas_iterations - 1:
            print(f"BAS Iter {iter_bas+1}/{max_bas_iterations}, Current Best Fitness: {best_fitness:.6f}, Delta: {delta:.6f}")
        if best_fitness < 0.0001: 
            print(f"BAS Optimization converged at iteration {iter_bas+1}.")
            break

    print(f"BAS Optimization Finished. Final Best Initial MSE: {best_fitness:.4f}")
    return best_params

# ===== BAS-BP 神经网络训练 (优化：尝试更大的网络结构和调整超参数) =====
# 定义网络结构
input_neurons = X_scaled.shape[1] 
# 1. 网络结构改为 (128, 64, 32)
hidden_neurons = (128, 64, 32) 
output_neurons = 1

print("\n==== 开始 BAS-BP 神经网络优化训练 ====\n")
print("开始BAS算法优化BP神经网络初始参数...")
initial_weights_biases = bas_optimize_initial_params(X_scaled, y_scaled, 
                                                      input_size=input_neurons, 
                                                      hidden_sizes=hidden_neurons, 
                                                      output_size=output_neurons,
                                                      max_bas_iterations=500, # 可以根据需要调整
                                                      initial_delta=0.5, 
                                                      eta=0.98) 

# 使用BAS优化后的初始参数构建并训练BP神经网络
print("\n开始训练BAS-BP神经网络 (使用Adam优化器和调整后的网络结构)...")
bas_bp_model = CustomBPNeuralNetwork(input_neurons, hidden_neurons, output_neurons, learning_rate=0.001) 
bas_bp_model._initialize_weights_biases(initial_params=initial_weights_biases) 
# 2. 训练 epochs 提高至 3000，添加 early stopping (已在CustomBPNeuralNetwork中实现)
bas_bp_model.train(X_scaled, y_scaled, epochs=10000, batch_size=64, validation_split=0.1, verbose=True) 

# ===== 预测结果还原 (无变化) =====
y_pred_scaled = bas_bp_model.predict(X_scaled)
y_pred = scaler_y.inverse_transform(y_pred_scaled).ravel() 

df_all['soil_pred'] = y_pred

# ===== 训练损失曲线 (无变化) =====
plt.figure(figsize=(8,4))
plt.plot(bas_bp_model.loss_curve)
plt.xlabel('迭代次数')
plt.ylabel('损失值 (MSE)')
plt.title('BAS-BP 训练损失曲线 (Adam优化器)')
plt.grid(True)
plt.show()

# ===== 误差评估 (无变化) =====
print(f'\n整体 RMSE: {root_mean_squared_error(y_raw, y_pred):.4f}')
print(f'整体 MAE: {mean_absolute_error(y_raw, y_pred):.4f}')

# 3. 画出预测误差的分布直方图
errors = y_raw - y_pred
plt.figure(figsize=(10, 6))
plt.hist(errors, bins=50, edgecolor='black')
plt.title('预测误差分布直方图')
plt.xlabel('预测误差 (真实值 - 预测值)')
plt.ylabel('频数')
plt.grid(True)
plt.show()

# ===== 每年输出对比图 (无变化) =====
for year in sorted(df_all['year'].unique()):
    df_year = df_all[df_all['year'] == year].reset_index(drop=True)
    plt.figure(figsize=(14, 5))
    plt.plot(df_year['datetime'], df_year['soil'], label='真实土壤湿度', color='blue')
    plt.plot(df_year['datetime'], df_year['soil_pred'], label='预测土壤湿度', color='red')
    plt.title(f'{year}年6-7月土壤湿度预测对比 (BAS-BP)')
    plt.xlabel('时间')
    plt.ylabel('土壤湿度 (%)')
    plt.legend()
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.show()

# ===== 连续晴天/雨天误差计算函数 (保持不变) =====
def calc_weather_period_errors(df, rain_col='rain', true_col='soil', pred_col='soil_pred', threshold_hours=12):
    import numpy as np
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    
    df = df.copy()
    df = df.sort_values('datetime').reset_index(drop=True)
    
    df['is_rain'] = df[rain_col] > 0
    
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
    
    print("\n连续晴天段数:", sunny_summary['count'])
    print(f"晴天平均 RMSE: {sunny_summary['rmse_mean']:.4f}，平均 MAE: {sunny_summary['mae_mean']:.4f}")
    print("连续雨天段数:", rainy_summary['count'])
    print(f"雨天平均 RMSE: {rainy_summary['rmse_mean']:.4f}，平均 MAE: {rainy_summary['mae_mean']:.4f}")
    
    return results

# ===== 调用连续晴雨天误差计算 (无变化) =====
weather_period_errors = calc_weather_period_errors(df_all, threshold_hours=12)



