import torch
import numpy as np
from config import CFG

class PhysicsEngine:
    @staticmethod
    def get_derivatives(model, x_tensor):
        """
        利用 PyTorch 自动微分计算一阶导(斜率)和二阶导(用于曲率)
        """
        x = x_tensor.clone().requires_grad_(True)
        y = model(x)
        
        # 一阶导 dy/dx
        dy_dx = torch.autograd.grad(y.sum(), x, create_graph=True)[0]
        
        # 二阶导 d2y/dx2
        d2y_dx2 = torch.autograd.grad(dy_dx.sum(), x, create_graph=False)[0]
        
        return y.detach().numpy().flatten(), \
               dy_dx.detach().numpy().flatten(), \
               d2y_dx2.detach().numpy().flatten()

    @staticmethod
    def evaluate_time(model):
        """
        使用 Runge-Kutta 风格的微元累加法计算总时间
        包含：重力加速、摩擦力损耗、空气阻力损耗、曲率离心力效应
        """
        # 生成高密度积分网格
        x_eval = torch.linspace(0, CFG.X_END, CFG.RK_STEPS)
        
        # 1. 获取几何信息
        y, dy, d2y = PhysicsEngine.get_derivatives(model, x_eval)
        
        # 物理几何约束: y不能小于0 (不能飞到起点上方)
        # 注意：这里坐标系 y轴向下为正，所以 y < -0.01 是非法的
        if np.any(y < -0.01): 
            return 1e6

        total_time = 0.0
        v = 0.0  # 初始速度
        
        # 2. 沿路径积分
        for i in range(len(x_eval) - 1):
            dx_step = x_eval[i+1].item() - x_eval[i].item()
            
            slope = dy[i]           # tan(theta) = y'
            
            # 曲率 k = |y''| / (1+y'^2)^1.5
            curvature_k = abs(d2y[i]) / ((1 + slope**2)**1.5 + 1e-8)
            radius_rho = 1.0 / (curvature_k + 1e-8)
            
            # 计算弧长微分 ds 和角度 theta
            ds = np.sqrt(1 + slope**2) * dx_step
            sin_theta = slope / np.sqrt(1 + slope**2)
            cos_theta = 1.0 / np.sqrt(1 + slope**2)
            
            # --- 动力学核心方程 ---
            # 支持力 N = mg*cos(theta) + m*v^2/rho (离心力增强正压力)
            # 摩擦力 f = mu * N
            # 阻力 f_drag = k * v^2
            # 驱动力 f_drive = mg * sin(theta)
            
            v2 = v**2
            
            f_drive = CFG.GRAVITY * sin_theta
            # 暂时移除离心力项，只保留重力垂直分量
            normal_force = CFG.GRAVITY * cos_theta
            f_friction = CFG.MU * max(0, normal_force) # 确保 N >= 0
            f_drag = CFG.DRAG_COEFF * v2
            
            # 牛顿第二定律 F_net = ma
            acc = f_drive - f_friction - f_drag
            
            # 运动学更新: v_next^2 = v_now^2 + 2 * a * ds
            v2_next = v2 + 2 * acc * ds
            
            if v2_next <= 1e-6:
                return 1e6 # 陷入停滞，能量耗尽
                
            v_next = np.sqrt(v2_next)
            v_avg = (v + v_next) / 2.0
            
            total_time += ds / (v_avg + 1e-8)
            v = v_next
            
        return total_time

    # === 新增: 可微分版本 (Differentiable) ===
    @staticmethod
    def evaluate_time_tensor(model):
        # 生成高密度积分网格
        x_eval = torch.linspace(0, CFG.X_END, CFG.RK_STEPS)
        
        # 1. 获取几何信息
        y, dy, d2y = PhysicsEngine.get_derivatives(model, x_eval)
        
        # 物理几何约束: y不能小于0 (不能飞到起点上方)
        # 注意：这里坐标系 y轴向下为正，所以 y < -0.01 是非法的
        if np.any(y < -0.01): 
            return 1e6

        total_time = 0.0
        v = 0.0  # 初始速度
        
        # 2. 积分循环
        for i in range(len(x_eval) - 1):
            dx_step = x_eval[i+1].item() - x_eval[i].item()
            
            slope = dy[i]           # tan(theta) = y'
            
            # 曲率 k = |y''| / (1+y'^2)^1.5
            curvature_k = abs(d2y[i]) / ((1 + slope**2)**1.5 + 1e-8)
            radius_rho = 1.0 / (curvature_k + 1e-8)
            
            # 计算弧长微分 ds 和角度 theta
            ds = np.sqrt(1 + slope**2) * dx_step
            sin_theta = slope / np.sqrt(1 + slope**2)
            cos_theta = 1.0 / np.sqrt(1 + slope**2)
            
            # 动力学
            f_drive = CFG.GRAVITY * sin_theta
            
            # --- 修改位置开始 ---
            # 原始代码: normal_force = CFG.GRAVITY * cos_theta + v2 / radius_rho
            # 修改后: 暂时移除离心力项
            normal_force = CFG.GRAVITY * cos_theta
            # --- 修改位置结束 ---

            # Softplus 平滑处理
            f_friction = CFG.MU * torch.nn.functional.softplus(normal_force * 10) / 10
            
            f_drag = CFG.DRAG_COEFF * v2
            
            acc = f_drive - f_friction - f_drag
            
            # 运动学更新: v_next^2 = v_now^2 + 2 * a * ds
            v2_next = v2 + 2 * acc * ds
            
            if v2_next <= 1e-6:
                return 1e6 # 陷入停滞，能量耗尽
                
            v_next = np.sqrt(v2_next)
            v_avg = (v + v_next) / 2.0
            
            total_time += ds / (v_avg + 1e-8)
            v = v_next
            
        return total_time + penalty
