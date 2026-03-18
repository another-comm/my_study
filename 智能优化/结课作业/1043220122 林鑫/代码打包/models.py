import torch
import torch.nn as nn
from config import CFG

# === MLP 参数化模型 (1D -> 1D) ===
class NeuralPath(nn.Module):
    """
    标准多层感知机参数化控制器
    保证轨迹的无限阶可微性（光滑性）
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