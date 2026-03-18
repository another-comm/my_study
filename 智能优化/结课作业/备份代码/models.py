import torch
import torch.nn as nn
import math
from config import CFG

# === 1. MLP 参数化模型 (1D -> 1D) ===
class NeuralPath(nn.Module):
    """
    标准多层感知机参数化控制器
    保证轨迹的无限阶可微性（光滑性），对机器人运动控制至关重要
    """
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
        Ansatz 硬约束: 确保起点(0,0)和终点(x_end, y_end)
        """
        x_col = x.view(-1, 1)
        nn_out = self.net(x_col)
        
        linear_bias = (CFG.Y_END / CFG.X_END) * x_col
        boundary_factor = x_col * (x_col - CFG.X_END)
        
        return linear_bias + boundary_factor * nn_out

# === 2. FNO 参数化模型 (基于谱方法的参数化策略) ===
class FNOPath(nn.Module):
    """
    基于Fourier Neural Operator的参数化控制器
    利用物理轨迹的低频特性，进一步压缩搜索空间
    适用于具有平滑特性的轨迹规划问题
    """
    def __init__(self, modes=8, hidden_size=16):
        super().__init__()
        self.modes = modes  # 保留的Fourier模式数
        self.hidden_size = hidden_size
        
        # Fourier变换的权重（可学习，使用实数）
        self.fourier_weights = nn.Parameter(torch.randn(modes, hidden_size) * 0.1)
        
        # 从Fourier空间映射回物理空间的MLP
        self.net = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
    def forward(self, x):
        """
        使用Fourier变换提取低频特征，然后通过MLP映射
        """
        x_col = x.view(-1, 1)
        batch_size = x_col.shape[0]
        
        # 归一化到 [0, 2π] 用于Fourier变换
        x_norm = (x_col / CFG.X_END) * 2 * math.pi
        
        # 构建Fourier基函数（低频模式：sin和cos）
        # 使用sin和cos组合以捕获相位信息
        fourier_features = torch.zeros(batch_size, self.modes * 2, device=x.device, dtype=torch.float32)
        for i in range(self.modes):
            k = i + 1
            fourier_features[:, i * 2] = torch.sin(k * x_norm.squeeze())
            fourier_features[:, i * 2 + 1] = torch.cos(k * x_norm.squeeze())
        
        # 通过可学习的Fourier权重进行变换
        # 扩展权重以匹配sin+cos特征
        expanded_weights = self.fourier_weights.repeat_interleave(2, dim=0)  # [modes*2, hidden_size]
        weighted = torch.matmul(fourier_features, expanded_weights)
        
        # 通过MLP映射到输出空间
        nn_out = self.net(weighted)
        
        # Ansatz硬约束
        linear_bias = (CFG.Y_END / CFG.X_END) * x_col
        boundary_factor = x_col * (x_col - CFG.X_END)
        
        return linear_bias + boundary_factor * nn_out

# --- 工具函数 ---
def vector_to_model(vec, model):
    idx = 0
    for param in model.parameters():
        numel = param.numel()
        new_param_tensor = torch.as_tensor(
            vec[idx:idx+numel],
            dtype=torch.float32,
            device=param.device  # 确保与参数同设备
        ).view_as(param)
        
        # 使用 param.copy_() 直接更新 torch.nn.Parameter 对象
        # 并在 torch.no_grad() 上下文中进行，以确保此操作本身不被追踪
        # 但模型参数在后续计算中仍能被追踪梯度
        with torch.no_grad():
            param.copy_(new_param_tensor)
        idx += numel

def get_model_size(model):
    return sum(p.numel() for p in model.parameters())