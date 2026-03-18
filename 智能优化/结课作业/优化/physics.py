import torch
import torch.nn.functional as F
import numpy as np
from config import CFG

# 尝试导入 numba，如果不存在则使用纯 Python 降级
try:
    from numba import jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # 定义一个空的装饰器作为降级
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# === Numba JIT 加速内核 (用于 PSO 阶段，无需梯度) ===
@jit(nopython=True, cache=True)
def _integrate_numba(ds_seg, dy_seg, slopes, curvatures, cos_theta_nodes, 
                     gravity, mu, drag_coeff, enable_centrifugal):
    """
    Numba JIT 编译的物理积分核心函数
    输入: numpy 数组 (float64)
    返回: 总时间 (float64)
    """
    n_steps = len(ds_seg)
    v2_values = np.zeros(n_steps + 1, dtype=np.float64)
    
    for i in range(n_steps):
        v2 = v2_values[i]
        ds = ds_seg[i]
        dy_step = dy_seg[i]
        
        # 1. 重力做功
        work_gravity = gravity * dy_step
        
        # 2. 阻力做功
        normal_force = gravity * cos_theta_nodes[i]
        if enable_centrifugal:
            normal_force = normal_force + v2 * curvatures[i]
        
        # 摩擦力
        f_friction = mu * max(0.0, normal_force)
        # 空气阻力
        f_drag = drag_coeff * v2
        
        work_loss = (f_friction + f_drag) * ds
        
        # 3. 能量更新
        v2_next = v2 + 2.0 * (work_gravity - work_loss)
        v2_next = max(0.0, v2_next)  # 物理约束: v^2 >= 0
        
        v2_values[i + 1] = v2_next
    
    # 计算时间
    total_time = 0.0
    eps = 1e-8
    for i in range(n_steps):
        v_curr = np.sqrt(max(0.0, v2_values[i]) + eps)
        v_next = np.sqrt(max(0.0, v2_values[i + 1]) + eps)
        v_avg = (v_curr + v_next) * 0.5
        dt = ds_seg[i] / (v_avg + eps)
        total_time += dt
    
    return total_time


# === PyTorch 梯度兼容内核 (用于梯度下降阶段，需要梯度) ===
def _integrate_torch(ds_seg: torch.Tensor, dy_seg: torch.Tensor, 
                     slopes: torch.Tensor, curvatures: torch.Tensor, 
                     cos_theta_nodes: torch.Tensor, gravity: float, 
                     mu: float, drag_coeff: float, enable_centrifugal: bool) -> torch.Tensor:
    """
    PyTorch 原生物理积分核心函数（支持梯度）
    输入: torch 张量 (支持梯度)
    返回: 总时间 (torch.Tensor)
    """
    n_steps = len(ds_seg)
    # 使用列表存储中间值，避免 inplace 操作导致的梯度问题
    v2_values = [torch.zeros(1, device=ds_seg.device, dtype=ds_seg.dtype, requires_grad=False)]
    
    for i in range(n_steps):
        v2 = v2_values[-1]
        ds = ds_seg[i]
        dy_step = dy_seg[i]
        
        # 1. 重力做功
        work_gravity = gravity * dy_step
        
        # 2. 阻力做功
        normal_force = gravity * cos_theta_nodes[i]
        if enable_centrifugal:
            normal_force = normal_force + v2 * curvatures[i]
        
        # 摩擦力（使用 F.relu 而不是 clamp，更兼容梯度）
        f_friction = mu * F.relu(normal_force)
        # 空气阻力
        f_drag = drag_coeff * v2
        
        work_loss = (f_friction + f_drag) * ds
        
        # 3. 能量更新（创建新张量，避免 inplace 操作）
        v2_next = v2 + 2.0 * (work_gravity - work_loss)
        v2_next = F.relu(v2_next)  # 物理约束: v^2 >= 0
        
        v2_values.append(v2_next)
    
    # 拼接速度序列
    v2_seq = torch.cat(v2_values).squeeze(-1)
    
    # 计算时间
    v_curr = torch.sqrt(v2_seq[:-1] + 1e-8)
    v_next = torch.sqrt(v2_seq[1:] + 1e-8)
    v_avg = (v_curr + v_next) * 0.5
    step_times = ds_seg / (v_avg + 1e-8)
    total_time = torch.sum(step_times)
    
    return total_time


class PhysicsEngine:
    @staticmethod
    def get_derivatives(model, x_tensor):
        """
        计算一阶导和二阶导 (支持梯度回传，优化版本)
        """
        x = x_tensor.clone().requires_grad_(True)
        y = model(x)
        
        # 修复：确保 y 为 1D 张量，避免 (N,1) 与 (N,) 广播带来的问题
        if y.dim() > 1 and y.shape[-1] == 1:
            y = y.squeeze(-1)
        
        # 优化：一次性计算一阶导
        dy_dx = torch.autograd.grad(y.sum(), x, create_graph=True, retain_graph=True)[0]
        
        # 计算二阶导 (仅在有摩擦力或需要曲率时必要，但为了通用性保留)
        d2y_dx2 = torch.autograd.grad(dy_dx.sum(), x, create_graph=True, retain_graph=True)[0]
        
        return y, dy_dx, d2y_dx2
        
    @staticmethod
    def evaluate_time_differentiable(model):
        """
        高性能物理评估函数
        自动切换：
        1. 无摩擦纯重力模式 -> 向量化计算 (极速，高精度2000步)
        2. 摩擦/阻力模式 -> 循环积分计算 (兼容复杂物理)
        """
        return PhysicsEngine._evaluate_time(model, with_penalty=True)

    @staticmethod
    def evaluate_time_physical(model):
        """
        仅计算物理时间（无惩罚项），用于最终指标报告。
        """
        return PhysicsEngine._evaluate_time(model, with_penalty=False)

    @staticmethod
    def _evaluate_time(model, with_penalty: bool):
        """
        核心时间计算函数
        with_penalty=True 用于训练/优化（包含边界与形状约束）
        with_penalty=False 用于最终物理时间评估（不含惩罚）
        """
        # 判定是否为保守力场 (无摩擦且无空气阻力)
        is_conservative = (CFG.MU == 0 and CFG.DRAG_COEFF == 0)
        
        # 动态调整步数：向量化模式下可以极其廉价地使用高精度，消除弦长误差
        actual_steps = 2000 if is_conservative else CFG.RK_STEPS
        
        # 1. 采样与几何计算
        with torch.enable_grad():
            x_eval = torch.linspace(0, CFG.X_END, actual_steps, device=CFG.DEVICE)
            y_raw, dy_raw, d2y_raw = PhysicsEngine.get_derivatives(model, x_eval)
        
        # 对模型输出做物理范围裁剪（仅在有惩罚的训练阶段启用，避免极端值破坏梯度）
        if with_penalty:
            y = torch.clamp(y_raw, 0.0, CFG.Y_END * 2.0)
            dy = torch.clamp(dy_raw, -50.0, 50.0)
            d2y = torch.clamp(d2y_raw, -200.0, 200.0)
        else:
            # 评估时使用更保守的物理范围，避免异常输出放大时间
            y = torch.clamp(y_raw, 0.0, CFG.Y_END)
            dy = dy_raw
            d2y = d2y_raw

        # 强制单调下坡并归一到终点：避免长时间停留在高位造成速度趋零
        y = torch.cummax(y, dim=0)[0]
        # 归一化使终点精确为 Y_END，同时保持起点为 0
        y = y / (y[-1] + 1e-8) * CFG.Y_END
        y[0] = 0.0
        y[-1] = CFG.Y_END
        
        # --- 软约束惩罚（仅在训练/优化时启用） ---
        if with_penalty:
            # 假设 y 为深度(正值)。如果 y < 0 (跑到地面上方)，则施加惩罚。
            penalty_height = torch.sum(F.relu(-y)) * 100.0
            penalty_range = torch.sum(F.relu(y - CFG.Y_END * 2.0)) * 100.0
            # 起点/终点边界：起点应为0，终点应为 Y_END
            penalty_bc = (y[0] ** 2) * 50_000.0 + ((y[-1] - CFG.Y_END) ** 2) * 50_000.0
        else:
            penalty_height = penalty_range = penalty_bc = 0.0
        
        # --- 路径微分量 ---
        # 使用差分计算弦长 (Secant approximation)
        dx_seg = x_eval[1:] - x_eval[:-1]
        dy_seg = y[1:] - y[:-1]
        ds_seg = torch.sqrt(dx_seg**2 + dy_seg**2 + 1e-10)
        
        # === 分支 1: 纯重力场 (极速向量化) ===
        if is_conservative:
            # 能量守恒: v = sqrt(2 * g * h)
            # 下落高度 = 当前深度 - 起点深度（起点非0时仍正确）
            h = y - y[0]
            
            # 限制 h >= 0 (避免数值误差导致负根号)
            h = F.relu(h)
            
            # 瞬时速度 v = sqrt(2gh)
            v = torch.sqrt(2 * CFG.GRAVITY * h + 1e-8)
            
            # 每一段的时间 dt = ds / v_avg
            # 梯形近似: v_avg = (v_start + v_end) / 2
            v_curr = v[:-1]
            v_next = v[1:]
            v_avg = (v_curr + v_next) * 0.5
            
            # 计算总时间 (防止除零)
            step_times = ds_seg / (v_avg + 1e-8)
            total_time = torch.sum(step_times)
            
            # 额外惩罚：不允许局部上坡（会降低能量却增加弧长）
            penalty_uphill = torch.sum(F.relu(-dy_seg)) * 1_000.0 if with_penalty else 0.0
            
            return total_time + penalty_height + penalty_range + penalty_bc + penalty_uphill

        # === 分支 2: 含摩擦/阻力 (优化计算) ===
        else:
            # 准备物理量
            slopes = dy[:-1]
            # 曲率计算 k = |y''| / (1+y'^2)^(3/2)
            curvatures = torch.abs(d2y[:-1]) / ((1 + slopes**2)**1.5 + 1e-8)
            # cos(theta) 用于计算法向力分量
            cos_theta_nodes = 1.0 / torch.sqrt(1 + slopes**2)
            
            # 根据是否需要梯度选择计算后端
            needs_grad = torch.is_grad_enabled()
            
            if needs_grad or not NUMBA_AVAILABLE:
                # === TorchScript 路径 (梯度下降阶段 或 numba 不可用时) ===
                total_time = _integrate_torch(
                    ds_seg, dy_seg, slopes, curvatures, cos_theta_nodes,
                    float(CFG.GRAVITY), float(CFG.MU), float(CFG.DRAG_COEFF), 
                    bool(CFG.ENABLE_CENTRIFUGAL)
                )
            else:
                # === Numba 路径 (PSO 阶段，极速) ===
                # 转换为 numpy 数组
                ds_seg_np = ds_seg.detach().cpu().numpy().astype(np.float64)
                dy_seg_np = dy_seg.detach().cpu().numpy().astype(np.float64)
                slopes_np = slopes.detach().cpu().numpy().astype(np.float64)
                curvatures_np = curvatures.detach().cpu().numpy().astype(np.float64)
                cos_theta_nodes_np = cos_theta_nodes.detach().cpu().numpy().astype(np.float64)
                
                # 调用 Numba JIT 内核
                total_time_np = _integrate_numba(
                    ds_seg_np, dy_seg_np, slopes_np, curvatures_np, cos_theta_nodes_np,
                    float(CFG.GRAVITY), float(CFG.MU), float(CFG.DRAG_COEFF),
                    bool(CFG.ENABLE_CENTRIFUGAL)
                )
                
                # 转换回 torch 张量
                total_time = torch.tensor(total_time_np, device=CFG.DEVICE, dtype=torch.float32)
            
            penalty_uphill = torch.sum(F.relu(-dy_seg)) * 1_000.0 if with_penalty else 0.0
            return total_time + penalty_height + penalty_range + penalty_bc + penalty_uphill
    
    @staticmethod
    def get_velocity_profile(model, x_eval):
        """
        计算速度分布，用于可视化动力学特性
        返回：x坐标, y坐标, 速度v
        """
        # 重新计算导数和坐标
        y_raw, dy_raw, d2y_raw = PhysicsEngine.get_derivatives(model, x_eval)
        
        # 应用与优化时相同的单调性约束和归一化，确保轨迹单调下降
        y_raw_clamped = torch.clamp(y_raw.flatten(), 0.0, CFG.Y_END * 2.0)
        # 强制单调下坡（深度单调增加）
        y = torch.cummax(y_raw_clamped, dim=0)[0]
        # 归一化使终点精确为 Y_END，同时保持起点为 0
        y = y / (y[-1] + 1e-8) * CFG.Y_END
        y[0] = 0.0
        y[-1] = CFG.Y_END
        
        is_conservative = (CFG.MU == 0 and CFG.DRAG_COEFF == 0)
        
        if is_conservative:
            # 向量化模式
            h = y # 深度
            v_profile = torch.sqrt(2 * CFG.GRAVITY * F.relu(h) + 1e-8)
        
        else:
            # 循环模式
            dx_seg = x_eval[1:] - x_eval[:-1]
            dy_seg = y[1:] - y[:-1]
            ds_seg = torch.sqrt(dx_seg**2 + dy_seg**2 + 1e-8)
            
            # 基于约束后的y计算slopes（用于曲率和法向力）
            slopes = dy_seg / (dx_seg + 1e-8)
            # 使用数值差分计算二阶导数用于曲率
            d2y_num = torch.diff(slopes) / (dx_seg[1:] + 1e-8)
            # 对齐长度：在开头补一个值（使用第一个差分值）
            if len(d2y_num) < len(slopes):
                d2y_num = torch.cat([d2y_num[:1], d2y_num])
            # 确保长度匹配
            d2y_num = d2y_num[:len(slopes)]
            curvatures = torch.abs(d2y_num) / ((1 + slopes**2)**1.5 + 1e-8)
            cos_theta_nodes = 1.0 / torch.sqrt(1 + slopes**2)
            
            v2_seq = torch.zeros(len(ds_seg) + 1, device=CFG.DEVICE)
            gravity = CFG.GRAVITY
            
            for i in range(len(ds_seg)):
                v2 = v2_seq[i]
                dy_step = dy_seg[i]
                
                work_gravity = gravity * dy_step
                
                normal_force = gravity * cos_theta_nodes[i]
                if CFG.ENABLE_CENTRIFUGAL:
                    normal_force += v2 * curvatures[i]
                
                work_loss = (CFG.MU * F.relu(normal_force) + CFG.DRAG_COEFF * v2) * ds_seg[i]
                
                v2_next = v2 + 2 * (work_gravity - work_loss)
                v2_seq[i+1] = F.relu(v2_next)
            
            v_profile = torch.sqrt(v2_seq)
        
        # 转换为 Numpy 并展平成 1D，避免 matplotlib fill_between 报 "'y2' is not 1-dimensional"
        x_np = x_eval.detach().cpu().numpy().flatten()
        y_np = y.detach().cpu().numpy().flatten()
        v_np = v_profile.detach().cpu().numpy().flatten()
        
        # 对齐长度，防止循环模式下长度差异
        min_len = min(len(x_np), len(y_np), len(v_np))
        return x_np[:min_len], y_np[:min_len], v_np[:min_len]
