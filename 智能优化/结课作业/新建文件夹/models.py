import torch
import torch.nn as nn
from config import CFG

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
        1. x=0 时, y=0 (起点)
        2. x=x_end 时, y=y_end (终点)
        """
        x_col = x.view(-1, 1)
        nn_out = self.net(x_col)
        
        # 线性基底 (连接起点和终点的直线)
        linear_bias = (CFG.Y_END / CFG.X_END) * x_col
        
        # 边界修正因子 (在两端为0，中间非0)
        boundary_factor = x_col * (x_col - CFG.X_END)
        
        return linear_bias + boundary_factor * nn_out

# 工具函数：将扁平的numpy基因向量加载到模型中
def vector_to_model(vec, model):
    idx = 0
    for param in model.parameters():
        numel = param.numel()
        param.data.copy_(torch.tensor(vec[idx:idx+numel], dtype=torch.float32).view_as(param))
        idx += numel

# 工具函数：获取模型总参数量
def get_model_size(model):
    return sum(p.numel() for p in model.parameters())
