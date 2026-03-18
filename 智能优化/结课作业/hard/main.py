import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. 配置参数 (Configuration)
# ==========================================
# 题目要求 n >= 3，你可以修改这里尝试 3, 4, 5 维
DIMENSION = 3          
BATCH_SIZE = 4096      # 每次迭代采样的向量个数
EPOCHS = 3000          # 训练总轮数
LEARNING_RATE = 1e-3   # 学习率
RADIUS = 5.0           # 采样区域半径 (近似 R^n)

# 理论最优值 (用于验证结果)
# Target = 1/C = (n-2)^2 / 4
THEORETICAL_MIN = ((DIMENSION - 2)**2) / 4.0

print(f"--- Setting Up ---")
print(f"Dimension (n): {DIMENSION}")
print(f"Theoretical Minimum Rayleigh Quotient: {THEORETICAL_MIN}")

# 检测是否有 GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# ==========================================
# 2. 定义神经网络 (u 函数近似器)
# ==========================================
class DeepRitzNet(nn.Module):
    def __init__(self, input_dim):
        super(DeepRitzNet, self).__init__()
        # 简单的全连接网络 (MLP)
        # 结构: Input(n) -> [Linear->Tanh] * 3 -> Output(1)
        # 使用 Tanh 是因为我们需要二阶导数光滑，ReLU 在 x=0 处不可导
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, 1) # 输出是一个标量 u
        )

    def forward(self, x):
        # x 的形状是 (Batch_Size, n)
        return self.layers(x)

# ==========================================
# 3. 损失函数 (核心物理部分)
# ==========================================
def calculate_rayleigh_quotient(model, x):
    """
    计算瑞利商 J(u) = (∫|∇u|² dx) / (∫(u/|x|)² dx)
    利用蒙特卡洛积分，积分符号转化为对 Batch 的求平均
    """
    # 必须开启梯度追踪，因为我们需要对 x 求导
    x.requires_grad_(True)
    
    # 1. 前向传播求 u(x)
    u = model(x)  # u shape: (Batch, 1)
    
    # 2. 计算梯度 ∇u (Vector Gradient)
    # torch.autograd.grad 返回的是对输入的梯度，形状同 x (Batch, n)
    # create_graph=True 允许对梯度再次求导（反向传播更新网络权重需要）
    grads = torch.autograd.grad(
        outputs=u, 
        inputs=x,
        grad_outputs=torch.ones_like(u),
        create_graph=True, 
        retain_graph=True,
        only_inputs=True
    )[0]
    
    # 3. 计算分子: Dirichlet Energy (梯度的模平方)
    # |∇u|² = (∂u/∂x1)² + ... + (∂u/∂xn)²
    # dim=1 表示在向量维度求和
    grad_squared_norm = torch.sum(grads**2, dim=1) 
    numerator = torch.mean(grad_squared_norm) # 对 Batch 求平均模拟积分
    
    # 4. 计算分母: Potential Energy (u²/|x|²)
    # |x|² = x1² + ... + xn² (L2 Norm Squared)
    # 加 1e-6 是为了防止采样点恰好在原点导致除零错误
    x_squared_norm = torch.sum(x**2, dim=1) + 1e-6
    
    # u 是 (Batch, 1)，squeeze 变成 (Batch)
    denominator = torch.mean((u.squeeze()**2) / x_squared_norm)
    
    # 5. 计算比值
    rayleigh_quotient = numerator / denominator
    
    return rayleigh_quotient

# ==========================================
# 4. 训练循环
# ==========================================
model = DeepRitzNet(DIMENSION).to(device)
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1000, gamma=0.5)

loss_history = []

print("\n--- Starting Optimization ---")
for epoch in range(EPOCHS):
    
    # --- A. 采样 (Sampling) ---
    # 在 n 维球体内均匀采样。
    # 这里的简单做法：先生成高斯分布，再归一化方向，再随机半径
    # 1. 随机方向
    x_raw = torch.randn(BATCH_SIZE, DIMENSION, device=device)
    direction = x_raw / (torch.norm(x_raw, dim=1, keepdim=True) + 1e-6)
    
    # 2. 随机半径 (r^(1/n) 保证在体积上均匀)
    r = (torch.rand(BATCH_SIZE, 1, device=device) ** (1/DIMENSION)) * RADIUS
    
    # 3. 组合得到输入向量 x
    x_input = direction * r
    
    # --- B. 优化步骤 ---
    optimizer.zero_grad()
    
    # 计算损失 (瑞利商)
    loss = calculate_rayleigh_quotient(model, x_input)
    
    # 反向传播
    loss.backward()
    optimizer.step()
    scheduler.step()
    
    # 记录
    loss_val = loss.item()
    loss_history.append(loss_val)
    
    if epoch % 200 == 0:
        print(f"Epoch {epoch:4d} | Current Value: {loss_val:.6f} | Target: {THEORETICAL_MIN:.6f}")

# ==========================================
# 5. 结果分析与绘图
# ==========================================
final_value = np.mean(loss_history[-100:]) # 取最后100次的平均值更稳定
error_percent = abs(final_value - THEORETICAL_MIN) / THEORETICAL_MIN * 100

print(f"\n--- Final Results ---")
print(f"Dimension n          : {DIMENSION}")
print(f"Theoretical Minimum  : {THEORETICAL_MIN:.6f}")
print(f"Algorithm Result     : {final_value:.6f}")
print(f"Relative Error       : {error_percent:.2f}%")

# 绘图
plt.figure(figsize=(10, 6))
plt.plot(loss_history, label='Estimated Min Value (Algorithm)', alpha=0.7)
plt.axhline(y=THEORETICAL_MIN, color='r', linestyle='--', linewidth=2, label=f'Theoretical Limit ({THEORETICAL_MIN})')
plt.title(f'Deep Ritz Method for Hardy Inequality (n={DIMENSION})')
plt.xlabel('Iterations')
plt.ylabel('Rayleigh Quotient')
plt.legend()
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.tight_layout()

# 保存图片以便查看
plt.savefig('hardy_inequality_result.png')
print("Result plot saved as 'hardy_inequality_result.png'")