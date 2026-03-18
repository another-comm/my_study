import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# ==========================================
# 1. 配置与超参数 (Configuration)
# ==========================================
class Config:
    # 环境参数
    X_END = 1.0
    Y_END = 1.0
    GRAVITY = 9.8
    MU = 0            # 摩擦系数
    DRAG_COEFF = 0   # 空气阻力系数
    
    # 数值计算
    NUM_NODES = 50      # 离散节点数 (用于 PSO)
    RK_STEPS = 100      # 积分步数 (用于物理评估)
    
    # 神经网络
    HIDDEN_SIZE = 16
    
    # 优化器
    NUM_PARTICLES = 64
    MAX_ITER = 150

CFG = Config()

# ==========================================
# 2. PyTorch 神经网络与硬约束 (The Brain)
# ==========================================
class NeuralPath(nn.Module):
    def __init__(self, hidden_size=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
    def forward(self, x):
        """
        Ansatz 硬约束变换:
        y_hat = x * (x - x_end) * NN(x) + (y_end / x_end) * x
        
        确保:
        1. x=0 时, y=0
        2. x=x_end 时, y=y_end
        """
        x_col = x.view(-1, 1)
        nn_out = self.net(x_col)
        
        # 线性基底 (连接起点和终点的直线)
        linear_bias = (CFG.Y_END / CFG.X_END) * x_col
        
        # 边界修正因子 (在两端为0)
        boundary_factor = x_col * (x_col - CFG.X_END)
        
        return linear_bias + boundary_factor * nn_out

# 辅助: 将扁平向量加载到模型
def vector_to_model(vec, model):
    idx = 0
    for param in model.parameters():
        numel = param.numel()
        # 确保数据类型一致
        param.data.copy_(torch.tensor(vec[idx:idx+numel], dtype=torch.float32).view_as(param))
        idx += numel

def get_model_size(model):
    return sum(p.numel() for p in model.parameters())

# ==========================================
# 3. 物理引擎 (Physics Engine) - 核心重构
# ==========================================
class PhysicsEngine:
    @staticmethod
    def get_derivatives(model, x_tensor):
        """
        利用自动微分计算一阶导(斜率)和二阶导(曲率相关)
        """
        x = x_tensor.clone().requires_grad_(True)
        y = model(x)
        
        # 一阶导 y'
        dy_dx = torch.autograd.grad(y.sum(), x, create_graph=True)[0]
        
        # 二阶导 y''
        d2y_dx2 = torch.autograd.grad(dy_dx.sum(), x, create_graph=False)[0]
        
        # 转换为 numpy
        y_np = y.detach().numpy().flatten()
        dy_np = dy_dx.detach().numpy().flatten()
        d2y_np = d2y_dx2.detach().numpy().flatten()
        
        return y_np, dy_np, d2y_np

    @staticmethod
    def evaluate_time(model):
        """
        使用 Runge-Kutta 风格的微元累加法
        """
        # 生成高密度网格进行物理积分
        x_eval = torch.linspace(0, CFG.X_END, CFG.RK_STEPS)
        
        # 1. 获取几何信息 (利用 AutoGrad 计算精确导数)
        y, dy, d2y = PhysicsEngine.get_derivatives(model, x_eval)
        
        # 物理检查: y 不能小于 0 (不能飞到起点上方)
        # 注意 y 轴向下为正，所以 y < -0.01 是不合法的
        if np.any(y < -0.01): 
            return 1e6

        total_time = 0.0
        v = 0.0  # 初始速度
        
        # 2. 沿路径积分
        for i in range(len(x_eval) - 1):
            # 微元几何属性
            dx_step = x_eval[i+1].item() - x_eval[i].item()
            slope = dy[i]           # tan(theta) = y'
            curvature_k = abs(d2y[i]) / ((1 + slope**2)**1.5 + 1e-8)
            radius_rho = 1.0 / (curvature_k + 1e-8)
            
            # 计算 ds 和 theta
            ds = np.sqrt(1 + slope**2) * dx_step
            sin_theta = slope / np.sqrt(1 + slope**2)
            cos_theta = 1.0 / np.sqrt(1 + slope**2)
            
            # --- 动力学方程 ---
            # ma = F_gravity - F_friction - F_drag
            # a = g*sin(theta) - mu*(g*cos(theta) + v^2/rho) - k*v^2
            # 注意: 曲率产生的离心力 N_centrifugal = m * v^2 / rho
            # 支持力 N = m*g*cos(theta) + m*v^2/rho (假设下凸)
            
            # 为了数值稳定性，限制 v^2
            v2 = v**2
            
            # 驱动力 (重力沿切线分量)
            f_drive = CFG.GRAVITY * sin_theta
            
            # 阻力 1: 摩擦力 (库仑摩擦 + 离心力效应)
            normal_force = CFG.GRAVITY * cos_theta + v2 / radius_rho
            f_friction = CFG.MU * normal_force
            
            # 阻力 2: 空气阻力
            f_drag = CFG.DRAG_COEFF * v2
            
            # 合加速度
            acc = f_drive - f_friction - f_drag
            
            # 运动学更新: v_next^2 = v_now^2 + 2 * a * ds
            v2_next = v2 + 2 * acc * ds
            
            if v2_next <= 1e-6:
                return 1e6 # 陷入停滞，无法到达
                
            v_next = np.sqrt(v2_next)
            v_avg = (v + v_next) / 2.0
            
            total_time += ds / (v_avg + 1e-8)
            v = v_next
            
        return total_time

# ==========================================
# 4. 进化算法 (Evolutionary Solver)
# ==========================================
def run_evolution():
    # 1. 初始化
    template_model = NeuralPath(hidden_size=CFG.HIDDEN_SIZE)
    dim = get_model_size(template_model)
    print(f"🧬 基因长度: {dim}")
    
    # 粒子群初始化
    particles = np.random.uniform(-0.5, 0.5, (CFG.NUM_PARTICLES, dim))
    velocities = np.random.uniform(-0.1, 0.1, (CFG.NUM_PARTICLES, dim))
    
    pbest_pos = particles.copy()
    pbest_score = np.full(CFG.NUM_PARTICLES, float('inf'))
    
    gbest_pos = np.zeros(dim)
    gbest_score = float('inf')
    
    loss_history = []
    
    print("🚀 开始进化...")
    
    for it in range(CFG.MAX_ITER):
        # 2. 评估
        for i in range(CFG.NUM_PARTICLES):
            # 将基因注入模型
            vector_to_model(particles[i], template_model)
            
            # 物理模拟
            try:
                score = PhysicsEngine.evaluate_time(template_model)
            except Exception:
                score = 1e6
                
            # 更新 Pbest
            if score < pbest_score[i]:
                pbest_score[i] = score
                pbest_pos[i] = particles[i].copy()
                
            # 更新 Gbest
            if score < gbest_score:
                gbest_score = score
                gbest_pos = particles[i].copy()
                
        loss_history.append(gbest_score)
        
        # 3. 更新粒子 (标准 PSO)
        w = 0.9 - 0.5 * (it / CFG.MAX_ITER) # 线性递减权重
        c1, c2 = 1.5, 1.5
        
        r1 = np.random.rand(CFG.NUM_PARTICLES, dim)
        r2 = np.random.rand(CFG.NUM_PARTICLES, dim)
        
        velocities = (w * velocities + 
                      c1 * r1 * (pbest_pos - particles) + 
                      c2 * r2 * (gbest_pos - particles))
        
        particles += velocities
        
        if it % 10 == 0:
            print(f"Gen {it:3d} | Min Time: {gbest_score:.4f} s")
            
    return gbest_pos, loss_history

# ==========================================
# 5. 可视化与验证
# ==========================================
def _calc_brachistochrone_cycloid(X, Y, num=200):
    """
    生成和终点(X, Y)匹配的摆线段
    返回: bx, by (numpy数组)
    """
    # 摆线参数:
    # x = R (theta - sin(theta))
    # y = -R (1 - cos(theta))
    # 目标: 摆线 x(0)=0,y(0)=0, x(theta_max)=X, y(theta_max)=Y

    def equations(theta):
        R = X / (theta - np.sin(theta))
        y1 = -R * (1 - np.cos(theta))
        return y1 - Y

    # 估算theta最大取值
    theta_max = fsolve(equations, 2.0)[0]
    R = X / (theta_max - np.sin(theta_max))

    # 生成0~theta_max的等间距采样
    theta = np.linspace(0, theta_max, num)
    bx = R * (theta - np.sin(theta))
    by = -R * (1 - np.cos(theta))
    return bx, by

def visualize_result(best_genes, loss_history):
    model = NeuralPath(hidden_size=CFG.HIDDEN_SIZE)
    vector_to_model(best_genes, model)
    
    # 生成高分辨率路径
    x_plot = torch.linspace(0, CFG.X_END, 200)
    with torch.no_grad():
        y_plot = model(x_plot).numpy().flatten()
    x_plot = x_plot.numpy()
    
    # 计算速度分布
    velocities = []
    v = 0
    # 简单重演一遍积分过程获取速度
    y_grad, dy_grad, d2y_grad = PhysicsEngine.get_derivatives(model, torch.from_numpy(x_plot))
    for i in range(len(x_plot)-1):
        dx = x_plot[i+1] - x_plot[i]
        slope = dy_grad[i]
        radius = ((1+slope**2)**1.5) / (abs(d2y_grad[i]) + 1e-8)
        
        ds = np.sqrt(1 + slope**2) * dx
        sin_theta = slope / np.sqrt(1+slope**2)
        cos_theta = 1.0 / np.sqrt(1+slope**2)
        
        # a = F_net / m
        f_drive = CFG.GRAVITY * sin_theta
        f_fric = CFG.MU * (CFG.GRAVITY*cos_theta + v**2/radius)
        f_drag = CFG.DRAG_COEFF * v**2
        
        acc = f_drive - f_fric - f_drag
        v = np.sqrt(max(0, v**2 + 2*acc*ds))
        velocities.append(v)
    velocities.append(v) # 补齐最后一点

    # ------- 生成理想摆线（最速曲线）用于对比 -------
    bx, by = _calc_brachistochrone_cycloid(CFG.X_END, -CFG.Y_END, num=400)

    # 绘图
    plt.figure(figsize=(15, 5))
    
    # 1. 收敛图
    plt.subplot(1, 3, 1)
    plt.plot(loss_history)
    plt.title("Convergence")
    plt.xlabel("Gen")
    plt.ylabel("Time (s)")
    plt.grid(True)
    
    # 2. 路径图
    plt.subplot(1, 3, 2)
    plt.plot(x_plot, -y_plot, 'r-', linewidth=2, label='AI Solution')
    plt.plot([0, CFG.X_END], [0, -CFG.Y_END], 'k:', alpha=0.3, label='Linear')
    plt.plot(bx, by, 'b--', linewidth=2, label='Brachistochrone (Cycloid)')
    plt.title(f"Trajectory (Mu={CFG.MU}, Cd={CFG.DRAG_COEFF})")
    plt.xlabel("x")
    plt.ylabel("-y")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    # 3. 速度图
    plt.subplot(1, 3, 3)
    plt.plot(x_plot, velocities, 'g-')
    plt.title("Velocity Profile")
    plt.xlabel("x")
    plt.ylabel("v (m/s)")
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('physics_engine_result.png')
    print("✅ 结果已保存: physics_engine_result.png")

if __name__ == "__main__":
    best_genes, history = run_evolution()
    visualize_result(best_genes, history)