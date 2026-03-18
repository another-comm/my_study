import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
from models import NeuralPath, FNOPath
from physics import PhysicsEngine
from config import CFG
import math


class Problem:
    def get_model(self):
        raise NotImplementedError
    
    def get_loss(self, model):
        raise NotImplementedError
        
    def visualize(self, model, history):
        raise NotImplementedError


# === 最速降线问题 ===
class BrachistochroneProblem(Problem):
    def get_model(self):
        if CFG.MODEL_TYPE == 'MLP':
            return NeuralPath(hidden_size=CFG.HIDDEN_SIZE)
        elif CFG.MODEL_TYPE == 'FNO':
            return FNOPath(modes=CFG.FNO_MODES, hidden_size=CFG.HIDDEN_SIZE)
        else:
            raise ValueError(f"Unknown model type: {CFG.MODEL_TYPE}")
        
    def get_loss(self, model):
        return PhysicsEngine.evaluate_time_differentiable(model)
        
    def visualize(self, model, history):
        # 配置中文字体与负号显示
        plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        # --- 1) 数据准备 ---
        x_plot = np.linspace(0, CFG.X_END, 200)
        x_tensor = torch.from_numpy(x_plot).float().to(CFG.DEVICE)
        with torch.no_grad():
            y_plot = model(x_tensor).cpu().numpy().flatten()

        # 解析最优摆线（无摩擦理想对比）
        def solve_theta_for_endpoint(x_end, y_end):
            target_ratio = y_end / x_end
            low, high = 1e-6, 10.0
            for _ in range(60):
                mid = (low + high) / 2
                ratio = (1 - math.cos(mid)) / (mid - math.sin(mid))
                if ratio > target_ratio:
                    low = mid
                else:
                    high = mid
            return (low + high) / 2

        theta_f = solve_theta_for_endpoint(CFG.X_END, CFG.Y_END)
        R = CFG.X_END / (theta_f - math.sin(theta_f))
        theta_vals = np.linspace(0, theta_f, 200)
        x_cyc = R * (theta_vals - np.sin(theta_vals))
        y_cyc = R * (1 - np.cos(theta_vals))

        # 速度剖面（长度与 x/y 对齐）
        x_eval = torch.linspace(0, CFG.X_END, 200, device=CFG.DEVICE)
        x_vel, y_vel, v_vel = PhysicsEngine.get_velocity_profile(model, x_eval)

        # 曲率分布
        x_tensor_curv = torch.from_numpy(x_plot).float().to(CFG.DEVICE)
        # 明确启用梯度，避免外层潜在的 no_grad 影响
        with torch.enable_grad():
            _, dy_curv, d2y_curv = PhysicsEngine.get_derivatives(model, x_tensor_curv)
        curvatures = torch.abs(d2y_curv) / ((1 + dy_curv**2) ** 1.5 + 1e-8)
        curv_np = curvatures.detach().cpu().numpy()

        # --- 2) 绘图 ---
        plt.figure(figsize=(14, 9))

        # 2.1 优化历史
        plt.subplot(2, 2, 1)
        plt.plot(history, 'b-', linewidth=1.5)
        if len(history) > 0:
            plt.axhline(y=history[-1], color='r', linestyle='--', alpha=0.5, label=f'Final: {history[-1]:.6f}')
            plt.legend()
        plt.title("优化历史", fontsize=12, fontweight='bold')
        plt.xlabel("迭代")
        plt.ylabel("损失")
        plt.grid(True, alpha=0.3)

        # 2.2 轨迹（速度着色）
        plt.subplot(2, 2, 2)
        scatter = plt.scatter(x_vel, -y_vel, c=v_vel, cmap='viridis', s=18, alpha=0.85, edgecolors='none')
        plt.colorbar(scatter, label='速度 (m/s)')
        plt.plot(x_plot, -y_plot, 'r-', linewidth=2, label='AI路径', alpha=0.7)
        if CFG.MU == 0 and CFG.DRAG_COEFF == 0:
            plt.plot(x_cyc, -y_cyc, 'g--', linewidth=2, label='理论摆线', alpha=0.6)
        plt.plot([0, CFG.X_END], [0, -CFG.Y_END], 'k:', alpha=0.3, label='直线参考')
        plt.title(f"轨迹规划 (μ={CFG.MU}, 向心力={CFG.ENABLE_CENTRIFUGAL})", fontsize=12, fontweight='bold')
        plt.xlabel("x (m)")
        plt.ylabel("-y (m)")
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.3)
        plt.axis('equal')

        # 2.3 速度分布
        plt.subplot(2, 2, 3)
        plt.plot(x_vel, v_vel, 'b-', linewidth=2, label='速度分布')
        plt.fill_between(x_vel, 0, v_vel, alpha=0.25)
        plt.title("速度分布", fontsize=12, fontweight='bold')
        plt.xlabel("x (m)")
        plt.ylabel("v (m/s)")
        plt.grid(True, alpha=0.3)
        plt.legend()

        # 2.4 曲率分布
        plt.subplot(2, 2, 4)
        plt.plot(x_plot, curv_np, 'purple', linewidth=2)
        plt.title("曲率分布", fontsize=12, fontweight='bold')
        plt.xlabel("x (m)")
        plt.ylabel("κ (1/m)")
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('result_brachistochrone.png', dpi=150, bbox_inches='tight')
        print("✅ Result saved: result_brachistochrone.png")

