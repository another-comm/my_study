"""
全球 AI 发展能力评价模型（顶配深度学习方案）
三阶段深度评估流程：
1. Self-Attention 特征交互学习
2. GA-BP 混合驱动评分模型
3. SHAP 可解释性分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import torch
import torch.nn as nn
import torch.optim as optim
import shap
import warnings
warnings.filterwarnings('ignore')

# Use a common font fallback for English plots
plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 定义两种标准化方法（5维度汇总）
normalization_methods = {
    "minmax": "Min-Max Normalization",
    "sigmoid": "Sigmoid Normalization (Logistic Mapping)",
}

print("=" * 80)
print("全球AI发展能力评价模型 - 两种标准化方法（5维度）对比分析")
print("=" * 80)

# 循环处理三种标准化方法
for method_key, method_name in normalization_methods.items():
    print(f"\n{'='*80}")
    print(f"方法: {method_name} ({method_key})")
    print(f"{'='*80}")
    
    # 1. 数据加载和预处理
    print("\n" + "=" * 60)
    print("步骤1: 数据加载和预处理")
    print("=" * 60)
    
    # 从Excel文件读取 5 维度汇总数据
    import os
    excel_filename = f"normalized_data_{method_key}_5dims.xlsx"
    
    if not os.path.exists(excel_filename):
        print(f"⚠️  未找到标准化数据文件: {excel_filename}")
        print(f"   请先运行 EWM_Analysis.py 生成标准化数据。")
        continue
    
    print(f"正在从 {excel_filename} 读取 5 维度得分数据...")
    df = pd.read_excel(excel_filename, sheet_name='五维度得分')
    print(f"成功读取数据: {df.shape[0]} 个国家, 5 个维度 + Total")
    
    countries = df['Country'].values
    feature_names = ["Talent", "Research", "Infrastructure", "Economy", "Policy"]
    
    # 数据已经是维度得分（0-100），先缩放到0-1用于后续熵权/模型
    X_normalized = df[feature_names].values / 100.0
    n_samples, n_features = X_normalized.shape
    
    print(f"数据维度: {n_samples} 个国家, {n_features} 个指标")
    print(f"指标名称: {feature_names}")
    
    # 计算熵权法得分作为基准（用于GA适应度函数）
    def calculate_entropy_weights(df_norm):
        df_norm = df_norm + 1e-9
        p = df_norm / df_norm.sum(axis=0)  # 按列求和
        k = 1 / np.log(len(df_norm))
        e = -k * (p * np.log(p)).sum(axis=0)  # 按列求和
        d = 1 - e
        weights = d / d.sum()
        return np.array(weights)  # 确保返回numpy数组
    
    entropy_weights = calculate_entropy_weights(X_normalized)
    # 确保 entropy_weights 是一维数组
    entropy_weights = np.array(entropy_weights).flatten()
    y_entropy = X_normalized @ entropy_weights  # 熵权法得分
    y_entropy = y_entropy * 100  # 转换为0-100分制
    
    print(f"\n熵权法基准得分范围: [{y_entropy.min():.2f}, {y_entropy.max():.2f}]")
    
    
    # 2. Self-Attention 特征交互学习模块
    print("\n" + "=" * 60)
    print("步骤2: Self-Attention 特征交互学习")
    print("=" * 60)
    
    class SelfAttention(nn.Module):
        """自注意力机制模块"""
        def __init__(self, d_model, n_heads=1):
            super(SelfAttention, self).__init__()
            self.d_model = d_model
            self.n_heads = n_heads
            self.d_k = d_model // n_heads
            
            self.W_q = nn.Linear(d_model, d_model)
            self.W_k = nn.Linear(d_model, d_model)
            self.W_v = nn.Linear(d_model, d_model)
            self.W_o = nn.Linear(d_model, d_model)
            
        def forward(self, x):
            batch_size, seq_len, d_model = x.size()
            
            # 计算 Q, K, V
            Q = self.W_q(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
            K = self.W_k(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
            V = self.W_v(x).view(batch_size, seq_len, self.n_heads, self.d_k).transpose(1, 2)
            
            # 计算注意力分数: Attention(Q, K, V) = Softmax(QK^T / sqrt(d_k))V
            scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.d_k)
            attention_weights = torch.softmax(scores, dim=-1)
            attended = torch.matmul(attention_weights, V)
            
            # 重塑并输出
            attended = attended.transpose(1, 2).contiguous().view(batch_size, seq_len, d_model)
            output = self.W_o(attended)
            
            return output, attention_weights
    
    # 将数据转换为 PyTorch 张量
    X_tensor = torch.FloatTensor(X_normalized).unsqueeze(0)  # [1, n_samples, n_features]
    
    # 初始化 Self-Attention 模块
    attention_model = SelfAttention(d_model=n_features, n_heads=1)
    
    # 前向传播获取注意力权重
    with torch.no_grad():
        attention_output, attention_weights = attention_model(X_tensor)
    
    # attention_weights shape: [1, n_heads, n_samples, n_samples] (样本间注意力)
    # 我们需要计算特征重要性，所以使用attention_output的均值
    attention_matrix = attention_weights[0, 0].numpy()  # [n_samples, n_samples]
    
    # 计算特征重要性：通过attention_output的均值来反映特征重要性
    # 使用attention_output的绝对值均值作为特征重要性
    feature_importance = torch.abs(attention_output).mean(dim=[0, 1]).numpy()  # [n_features]
    
    # 计算平均注意力权重（全局重要性）
    global_attention = feature_importance  # [n_features]
    
    print(f"Self-Attention 输出维度: {attention_output.shape}")
    print(f"注意力权重矩阵维度: {attention_matrix.shape}")
    
    # 3. GA-BP 神经网络模型
    print("\n" + "=" * 60)
    print("步骤3: GA-BP 混合驱动评分模型")
    print("=" * 60)
    
    class BPNeuralNetwork(nn.Module):
        """BP神经网络"""
        def __init__(self, input_size, hidden_size1=32, hidden_size2=16, output_size=1):
            super(BPNeuralNetwork, self).__init__()
            self.fc1 = nn.Linear(input_size, hidden_size1)
            self.fc2 = nn.Linear(hidden_size1, hidden_size2)
            self.fc3 = nn.Linear(hidden_size2, output_size)
            self.relu = nn.ReLU()
            self.sigmoid = nn.Sigmoid()
            
        def forward(self, x):
            x = self.relu(self.fc1(x))
            x = self.relu(self.fc2(x))
            x = self.sigmoid(self.fc3(x)) * 100  # 输出0-100分
            return x
        
        def get_weights(self):
            """获取所有权重参数"""
            params = []
            for param in self.parameters():
                params.extend(param.data.flatten().numpy().tolist())
            return np.array(params)
        
        def set_weights(self, weights):
            """设置所有权重参数"""
            idx = 0
            for param in self.parameters():
                size = param.numel()
                param.data = torch.FloatTensor(weights[idx:idx+size]).reshape(param.shape)
                idx += size
    
    # 遗传算法参数
    POP_SIZE = 50
    N_GENERATIONS = 100
    MUTATION_RATE = 0.1
    CROSSOVER_RATE = 0.8
    ELITE_RATE = 0.2
    
    # 创建网络实例以计算参数数量
    model_template = BPNeuralNetwork(input_size=n_features)
    n_params = sum(p.numel() for p in model_template.parameters())
    
    print(f"神经网络参数数量: {n_params}")
    print(f"种群大小: {POP_SIZE}, 迭代次数: {N_GENERATIONS}")
    
    def fitness_function(weights):
        """适应度函数：预测值与熵权法得分的均方误差的倒数"""
        model = BPNeuralNetwork(input_size=n_features)
        model.set_weights(weights)
        model.eval()
        
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_normalized)
            predictions = model(X_tensor).squeeze().numpy()
        
        mse = mean_squared_error(y_entropy, predictions)
        fitness = 1 / (1 + mse)  # 避免除零
        return fitness
    
    def initialize_population():
        """初始化种群"""
        population = []
        for _ in range(POP_SIZE):
            # 随机初始化权重
            model = BPNeuralNetwork(input_size=n_features)
            weights = model.get_weights()
            # 添加小的随机扰动
            weights = weights + np.random.normal(0, 0.1, size=weights.shape)
            population.append(weights)
        return np.array(population)
    
    def selection(population, fitness_scores):
        """选择操作：轮盘赌选择"""
        fitness_scores = np.array(fitness_scores)
        fitness_scores = fitness_scores - fitness_scores.min() + 1e-6  # 确保为正
        probs = fitness_scores / fitness_scores.sum()
        indices = np.random.choice(len(population), size=len(population), p=probs)
        return population[indices]
    
    def crossover(parent1, parent2):
        """交叉操作：单点交叉"""
        if np.random.rand() < CROSSOVER_RATE:
            point = np.random.randint(1, len(parent1))
            child1 = np.concatenate([parent1[:point], parent2[point:]])
            child2 = np.concatenate([parent2[:point], parent1[point:]])
            return child1, child2
        return parent1.copy(), parent2.copy()
    
    def mutation(individual):
        """变异操作：高斯变异"""
        if np.random.rand() < MUTATION_RATE:
            mask = np.random.rand(len(individual)) < 0.1  # 只变异10%的参数
            individual[mask] += np.random.normal(0, 0.05, size=np.sum(mask))
        return individual
    
    # 遗传算法主循环
    print("\n开始遗传算法优化...")
    population = initialize_population()
    best_fitness_history = []
    avg_fitness_history = []
    
    for generation in range(N_GENERATIONS):
        # 计算适应度
        fitness_scores = [fitness_function(individual) for individual in population]
        best_fitness = max(fitness_scores)
        avg_fitness = np.mean(fitness_scores)
        best_fitness_history.append(best_fitness)
        avg_fitness_history.append(avg_fitness)
        
        if (generation + 1) % 20 == 0:
            print(f"Generation {generation + 1}/{N_GENERATIONS}, "
                  f"Best Fitness: {best_fitness:.6f}, Avg Fitness: {avg_fitness:.6f}")
        
        # 精英保留
        elite_size = int(POP_SIZE * ELITE_RATE)
        elite_indices = np.argsort(fitness_scores)[-elite_size:]
        elite = population[elite_indices]
        
        # 选择
        selected = selection(population, fitness_scores)
        
        # 交叉和变异生成新种群
        new_population = []
        new_population.extend(elite)
        
        while len(new_population) < POP_SIZE:
            idx1, idx2 = np.random.choice(len(selected), 2, replace=False)
            child1, child2 = crossover(selected[idx1], selected[idx2])
            child1 = mutation(child1)
            child2 = mutation(child2)
            new_population.extend([child1, child2])
        
        population = np.array(new_population[:POP_SIZE])
    
    # 获取最优个体
    final_fitness_scores = [fitness_function(individual) for individual in population]
    best_individual_idx = np.argmax(final_fitness_scores)
    best_weights = population[best_individual_idx]
    
    # 使用最优权重初始化最终模型
    final_model = BPNeuralNetwork(input_size=n_features)
    final_model.set_weights(best_weights)
    
    # 使用最优参数进行BP精修
    print("\n使用最优参数进行BP精修...")
    X_tensor_train = torch.FloatTensor(X_normalized)
    y_tensor_train = torch.FloatTensor(y_entropy).unsqueeze(1)
    
    optimizer = optim.Adam(final_model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    for epoch in range(500):
        optimizer.zero_grad()
        predictions = final_model(X_tensor_train)
        loss = criterion(predictions, y_tensor_train)
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 100 == 0:
            print(f"Epoch {epoch + 1}/500, Loss: {loss.item():.6f}")
    
    # 获取最终预测
    final_model.eval()
    with torch.no_grad():
        y_pred = final_model(X_tensor_train).squeeze().numpy()
    
    print(f"\n最终预测得分范围: [{y_pred.min():.2f}, {y_pred.max():.2f}]")
    print(f"预测得分与熵权法得分的MSE: {mean_squared_error(y_entropy, y_pred):.6f}")
    
    # 4. SHAP 可解释性分析
    print("\n" + "=" * 60)
    print("步骤4: SHAP 可解释性分析")
    print("=" * 60)
    
    # 将PyTorch模型包装为SHAP兼容的模型
    def model_wrapper(X):
        """包装模型以便SHAP使用"""
        X_tensor = torch.FloatTensor(X)
        final_model.eval()
        with torch.no_grad():
            pred = final_model(X_tensor).squeeze().numpy()
        # 确保返回的是数组格式
        if pred.ndim == 0:
            pred = np.array([pred])
        return pred
    
    # 使用KernelExplainer进行SHAP分析
    print("计算SHAP值...")
    try:
        # 使用背景样本（取前几个样本作为背景）
        background_samples = X_normalized[:5]  # 使用前5个样本作为背景
        explainer = shap.KernelExplainer(model_wrapper, background_samples)
        shap_values = explainer.shap_values(X_normalized, nsamples=50)  # 减少采样数量以加快速度
        
        # 确保shap_values是数组格式
        shap_values = np.array(shap_values)
        if shap_values.ndim == 1:
            shap_values = shap_values.reshape(-1, 1)
        
        print(f"SHAP值形状: {shap_values.shape}")
        
        # 计算全局特征重要性
        if shap_values.ndim == 2:
            shap_importance = np.abs(shap_values).mean(axis=0)
        else:
            shap_importance = np.abs(shap_values).flatten()
        
        # 确保长度匹配
        if len(shap_importance) != n_features:
            if len(shap_importance) > n_features:
                shap_importance = shap_importance[:n_features]
            else:
                shap_importance = np.pad(shap_importance, (0, n_features - len(shap_importance)), 'constant')
            
    except Exception as e:
        print(f"SHAP计算遇到问题: {e}")
        print("使用梯度方法作为替代...")
        # 使用梯度方法计算特征重要性
        X_tensor_grad = torch.FloatTensor(X_normalized)
        X_tensor_grad.requires_grad = True
        final_model.eval()
        
        pred = final_model(X_tensor_grad)
        pred.sum().backward()
        
        # 计算梯度的绝对值作为特征重要性
        gradients = X_tensor_grad.grad.data.numpy()
        shap_importance = np.abs(gradients).mean(axis=0)
        shap_values = gradients  # 使用梯度作为SHAP值的近似
        print(f"梯度重要性形状: {shap_importance.shape}")
        
        # 确保长度匹配
        if len(shap_importance) != n_features:
            if len(shap_importance) > n_features:
                shap_importance = shap_importance[:n_features]
            else:
                shap_importance = np.pad(shap_importance, (0, n_features - len(shap_importance)), 'constant')
    
    print("\nSHAP全局特征重要性（前10名）:")
    shap_importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': shap_importance
    }).sort_values('Importance', ascending=False)
    print(shap_importance_df.head(10))

    # 5. 结果可视化
    print("\n" + "=" * 60)
    print("步骤5: 生成可视化图表")
    print("=" * 60)
    
    # 创建结果目录（每个方法使用不同的目录）
    output_dir = f"output_figures_{method_key}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n结果将保存到: {output_dir}/")

    # 5.1 GA收敛曲线
    print("5.1 绘制GA收敛曲线...")
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, N_GENERATIONS + 1), best_fitness_history, label="Best Fitness", linewidth=2)
    plt.plot(range(1, N_GENERATIONS + 1), avg_fitness_history, label="Average Fitness", linewidth=2, alpha=0.7)
    plt.xlabel("Generation", fontsize=12)
    plt.ylabel("Fitness", fontsize=12)
    plt.title("Genetic Algorithm Convergence", fontsize=14, fontweight="bold")
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/GA_Convergence.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存: {output_dir}/GA_Convergence.png")
    
    # 5.2 Attention热力图
    print("5.2 绘制Attention热力图...")
    plt.figure(figsize=(12, 10))
    # 使用特征重要性
    attention_avg = global_attention.reshape(1, -1)
    sns.heatmap(
        attention_avg,
        xticklabels=feature_names,
        yticklabels=["Feature Importance"],
        annot=True,
        fmt=".3f",
        cmap="YlOrRd",
        cbar_kws={"label": "Attention Weight"},
    )
    plt.title("Self-Attention Feature Importance (Heatmap)", fontsize=14, fontweight="bold", pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Attention_Heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存: {output_dir}/Attention_Heatmap.png")

    # 5.3 SHAP贡献摘要图
    print("5.3 绘制SHAP贡献摘要图...")
    try:
        # 确保shap_values格式正确
        shap_values_array = np.array(shap_values)
        if shap_values_array.ndim == 1:
            shap_values_array = shap_values_array.reshape(-1, n_features)
        elif shap_values_array.shape[1] != n_features:
            # 如果维度不匹配，使用重要性条形图
            raise ValueError("SHAP值维度不匹配")
        
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values_array, X_normalized, feature_names=feature_names, show=False)
        plt.title("SHAP Summary (Feature Contributions)", fontsize=14, fontweight="bold", pad=20)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/SHAP_Summary.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  已保存: {output_dir}/SHAP_Summary.png")
    except Exception as e:
        print(f"  SHAP摘要图生成失败: {e}")
        # 使用简单的条形图替代
        plt.figure(figsize=(10, 8))
        shap_importance_df_sorted = shap_importance_df.sort_values('Importance', ascending=True)
        plt.barh(shap_importance_df_sorted['Feature'], shap_importance_df_sorted['Importance'])
        plt.xlabel("Mean |SHAP value|", fontsize=12)
        plt.title("Global SHAP Feature Importance", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(f'{output_dir}/SHAP_Importance.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  已保存: {output_dir}/SHAP_Importance.png (替代方案)")
    
    # 5.4 竞争力排名雷达图
    print("5.4 绘制竞争力排名雷达图...")
    # 获取前三名国家
    top3_indices = np.argsort(y_pred)[-3:][::-1]
    top3_countries = countries[top3_indices]
    
    # 直接使用 5 维度得分（feature_names 即5维）
    dim_scores = {}
    for country_idx in top3_indices:
        country_name = countries[country_idx]
        dim_scores[country_name] = {dim: X_normalized[country_idx, feature_names.index(dim)] * 100
                                    for dim in feature_names}
    
    # 绘制雷达图
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    dimensions = feature_names  # ['Talent', 'Research', 'Infrastructure', 'Economy', 'Policy']
    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    angles += angles[:1]  # 闭合图形
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    for idx, country in enumerate(top3_countries):
        values = [dim_scores[country][dim] for dim in dimensions]
        values += values[:1]  # 闭合图形
        ax.plot(angles, values, 'o-', linewidth=2, label=country, color=colors[idx])
        ax.fill(angles, values, alpha=0.25, color=colors[idx])
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Normalized Score", fontsize=12, labelpad=20)
    ax.set_title("Top 3 Countries Competitiveness (Radar)", fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Competitiveness_Radar.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存: {output_dir}/Competitiveness_Radar.png")
    
    # 5.5 最终排名对比图
    print("5.5 绘制最终排名对比图...")
    # 按预测得分排序
    ranking_indices = np.argsort(y_pred)[::-1]
    ranked_countries = countries[ranking_indices]
    ranked_scores = y_pred[ranking_indices]
    
    plt.figure(figsize=(10, 8))
    bars = plt.barh(range(len(ranked_countries)), ranked_scores, 
                    color=plt.cm.viridis(np.linspace(0, 1, len(ranked_countries))))
    plt.yticks(range(len(ranked_countries)), ranked_countries)
    plt.xlabel("AI Competitiveness Score", fontsize=12)
    plt.title("Global AI Capability Ranking (Deep Learning Model, 2025)", fontsize=14, fontweight="bold")
    plt.xlim(0, 100)
    for i, (country, score) in enumerate(zip(ranked_countries, ranked_scores)):
        plt.text(score + 1, i, f'{score:.2f}', va='center', fontsize=10)
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Final_Ranking.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存: {output_dir}/Final_Ranking.png")
    
    # 6. 输出详细结果
    print("\n" + "=" * 60)
    print("步骤6: 输出详细结果")
    print("=" * 60)
    
    results_df = pd.DataFrame({
        '国家': countries,
        '深度学习模型得分': y_pred,
        '熵权法得分': y_entropy,
        '差异': y_pred - y_entropy
    })
    
    results_df = results_df.sort_values('深度学习模型得分', ascending=False)
    results_df['排名'] = range(1, len(results_df) + 1)
    results_df = results_df[['排名', '国家', '深度学习模型得分', '熵权法得分', '差异']]
    
    print("\n最终排名结果:")
    print(results_df.to_string(index=False))
    
    # 保存结果到CSV
    results_df.to_csv(f'{output_dir}/Final_Results.csv', index=False, encoding='utf-8-sig')
    print(f"\n结果已保存到: {output_dir}/Final_Results.csv")

    print("\n" + "=" * 60)
    print(f"方法 {method_name} 处理完成！")
    print("=" * 60)
    print(f"\n所有图表已保存到 '{output_dir}' 目录:")
    print("  1. GA_Convergence.png - 遗传算法收敛曲线")
    print("  2. Attention_Heatmap.png - Self-Attention热力图")
    print("  3. SHAP_Summary.png / SHAP_Importance.png - SHAP可解释性分析")
    print("  4. Competitiveness_Radar.png - 竞争力雷达图")
    print("  5. Final_Ranking.png - 最终排名对比图")

print(f"\n{'='*80}")
print("所有标准化方法处理完成！")
print("="*80)
print("\n生成的结果目录：")
for method_key in normalization_methods.keys():
    print(f"  - output_figures_{method_key}/")
