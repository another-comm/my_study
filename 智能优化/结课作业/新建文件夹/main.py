import torch
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from config import CFG
from models import NeuralPath, vector_to_model, get_model_size
from physics import PhysicsEngine
from optimizers import StandardPSO, EntropyPSO, QPSO

def get_optimizer(algo_type, dim):
    if algo_type == 'PSO':
        return StandardPSO(dim, CFG.NUM_PARTICLES, CFG.MAX_ITER)
    elif algo_type == 'EntropyPSO':
        return EntropyPSO(dim, CFG.NUM_PARTICLES, CFG.MAX_ITER)
    elif algo_type == 'QPSO':
        return QPSO(dim, CFG.NUM_PARTICLES, CFG.MAX_ITER)
    else:
        raise ValueError(f"Unknown algo type: {algo_type}")

def run_evolution():
    # 1. 准备模型模版
    template_model = NeuralPath(hidden_size=CFG.HIDDEN_SIZE)
    dim = get_model_size(template_model)
    
    print(f"🔹 算法: {CFG.ALGO_TYPE}")
    print(f"🧬 基因长度: {dim}")
    print(f"🌍 环境: Mu={CFG.MU}, Drag={CFG.DRAG_COEFF}")
    
    # 2. 初始化优化器
    optimizer = get_optimizer(CFG.ALGO_TYPE, dim)
    
    print("🚀 开始进化...")
    
    for it in range(CFG.MAX_ITER):
        scores = []
        
        # 3. 种群评估
        for i in range(CFG.NUM_PARTICLES):
            # 将基因注入神经网络
            vector_to_model(optimizer.particles[i], template_model)
            
            # 物理引擎跑分
            try:
                t = PhysicsEngine.evaluate_time(template_model)
            except Exception:
                t = 1e6 # 异常惩罚
            scores.append(t)
            
        scores = np.array(scores)
        
        # 4. 更新优化器状态 (PBest, GBest)
        optimizer.update_pbest(scores)
        
        # 5. 进化一步
        optimizer.step(it)
        
        # 打印日志
        if it % 10 == 0:
            print(f"Gen {it:3d} | Min Time: {optimizer.gbest_score:.5f} s")
            
    return optimizer.gbest_pos, optimizer.history

# --- 新增: 理论摆线生成器 ---
def get_theoretical_cycloid(x_end, y_end, num_points=200):
    """求解通过 (0,0) 和 (x_end, y_end) 的标准摆线参数"""
    def equations(vars):
        r, theta = vars
        eq1 = r * (theta - np.sin(theta)) - x_end
        eq2 = r * (1 - np.cos(theta)) - y_end
        return [eq1, eq2]

    # 初始猜测
    try:
        r_sol, theta_sol = fsolve(equations, [0.5, np.pi])
    except:
        return np.zeros(num_points), np.zeros(num_points) # 求解失败返回零

    theta_vals = np.linspace(0, theta_sol, num_points)
    x_cyc = r_sol * (theta_vals - np.sin(theta_vals))
    y_cyc = r_sol * (1 - np.cos(theta_vals))
    
    return x_cyc, y_cyc

def visualize(best_genes, history):
    model = NeuralPath(hidden_size=CFG.HIDDEN_SIZE)
    vector_to_model(best_genes, model)
    
    # 1. AI 路径
    x_plot = torch.linspace(0, CFG.X_END, 200)
    with torch.no_grad():
        y_plot = model(x_plot).numpy().flatten()
    x_plot = x_plot.numpy()
    
    # 2. 理论摆线 (无摩擦基准)
    cyc_x, cyc_y = get_theoretical_cycloid(CFG.X_END, CFG.Y_END)
    
    # 重新计算速度分布 (用于绘图)
    velocities = []
    v = 0
    # 获取导数
    _, dy_grad, d2y_grad = PhysicsEngine.get_derivatives(model, torch.from_numpy(x_plot))
    
    for i in range(len(x_plot)-1):
        dx = x_plot[i+1] - x_plot[i]
        slope = dy_grad[i]
        radius = ((1+slope**2)**1.5) / (abs(d2y_grad[i]) + 1e-8)
        
        ds = np.sqrt(1 + slope**2) * dx
        sin_theta = slope / np.sqrt(1+slope**2)
        cos_theta = 1.0 / np.sqrt(1+slope**2)
        
        f_drive = CFG.GRAVITY * sin_theta
        
        # 根据配置决定是否加入离心力
        if CFG.ENABLE_CENTRIFUGAL:
            normal_force = CFG.GRAVITY*cos_theta + v**2/radius
        else:
            normal_force = CFG.GRAVITY*cos_theta
            
        f_fric = CFG.MU * normal_force
        f_drag = CFG.DRAG_COEFF * v**2
        
        acc = f_drive - f_fric - f_drag
        v = np.sqrt(max(0, v**2 + 2*acc*ds))
        velocities.append(v)
    velocities.append(v)
    
    # 绘图
    plt.figure(figsize=(15, 5))
    
    # 子图1: 收敛曲线
    plt.subplot(1, 3, 1)
    plt.plot(history)
    plt.title(f"{CFG.ALGO_TYPE} Convergence")
    plt.xlabel("Gen")
    plt.ylabel("Time (s)")
    plt.grid(True)
    
    # 子图2: 轨迹对比
    cent_status = "On" if CFG.ENABLE_CENTRIFUGAL else "Off"
    ai_label = f'AI (Mu={CFG.MU}, Cd={CFG.DRAG_COEFF}, Cent={cent_status})'
    
    plt.subplot(1, 3, 2)
    plt.plot(x_plot, -y_plot, 'r-', linewidth=2, label=ai_label)
    plt.plot(cyc_x, -cyc_y, 'b--', linewidth=2, label='Cycloid (Ideal)')
    plt.plot([0, CFG.X_END], [0, -CFG.Y_END], 'k:', alpha=0.3)
    
    plt.title(f"Trajectory (Centrifugal Force: {cent_status})")
    plt.xlabel("x")
    plt.ylabel("-y (Depth)")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    # 子图3: 速度分布
    plt.subplot(1, 3, 3)
    plt.plot(x_plot, velocities, 'g-')
    plt.title("Velocity Profile")
    plt.xlabel("x")
    plt.ylabel("v (m/s)")
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('final_result.png')
    print("✅ Result saved: final_result.png")

if __name__ == "__main__":
    best_pos, history = run_evolution()
    visualize(best_pos, history)