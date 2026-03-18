import torch
from config import CFG

# 基类：包含通用属性和结果记录逻辑
class BaseOptimizer:
    def __init__(self, dim, pop_size, max_iter):
        self.dim = dim
        self.pop_size = pop_size
        self.max_iter = max_iter
        
        # 初始化位置 (-0.5, 0.5) 范围，全部放在目标设备
        self.particles = torch.empty((pop_size, dim), device=CFG.DEVICE).uniform_(-0.5, 0.5)
        
        self.pbest_pos = self.particles.clone()
        self.pbest_score = torch.full((pop_size,), float('inf'), device=CFG.DEVICE)
        
        self.gbest_pos = torch.zeros(dim, device=CFG.DEVICE)
        self.gbest_score = float('inf')
        
        self.history = []
        
    def update_pbest(self, scores):
        """通用更新逻辑: 更新个体最优(pbest)和全局最优(gbest)"""
        scores_t = torch.as_tensor(scores, device=CFG.DEVICE, dtype=torch.float32)
        # 确保是一维向量 [pop_size]，避免广播成 [pop_size, pop_size]
        scores_t = scores_t.view(-1)
        # 更新 PBest
        improved = scores_t < self.pbest_score
        self.pbest_score = torch.where(improved, scores_t, self.pbest_score)
        # [pop_size, 1] -> [pop_size, dim]
        mask = improved.unsqueeze(1).expand_as(self.particles)
        self.pbest_pos = torch.where(mask, self.particles, self.pbest_pos)
        
        # 更新 GBest
        min_score_idx = torch.argmin(self.pbest_score)
        min_score_val = self.pbest_score[min_score_idx].item()
        if min_score_val < self.gbest_score:
            self.gbest_score = min_score_val
            self.gbest_pos = self.pbest_pos[min_score_idx].clone()
            
        self.history.append(self.gbest_score)

# 1. 标准 PSO
class StandardPSO(BaseOptimizer):
    def __init__(self, dim, pop_size, max_iter):
        super().__init__(dim, pop_size, max_iter)
        self.velocities = torch.empty((pop_size, dim), device=CFG.DEVICE).uniform_(-0.1, 0.1)
        
    def step(self, it):
        w = 0.9 - 0.5 * (it / self.max_iter) # 线性递减权重
        c1, c2 = 1.5, 1.5
        
        r1 = torch.rand(self.pop_size, self.dim, device=CFG.DEVICE)
        r2 = torch.rand(self.pop_size, self.dim, device=CFG.DEVICE)
        
        # 速度更新
        self.velocities = (w * self.velocities + 
                           c1 * r1 * (self.pbest_pos - self.particles) + 
                           c2 * r2 * (self.gbest_pos - self.particles))
        # 位置更新
        self.particles += self.velocities

# 2. 熵权 PSO (EntropyPSO) - 自适应调节参数
class EntropyPSO(StandardPSO):
    def _calculate_entropy(self):
        """计算种群分布的香农熵，衡量多样性"""
        # 简单网格法：将每个维度归一化后离散化
        min_val = torch.min(self.particles, dim=0).values
        max_val = torch.max(self.particles, dim=0).values
        norm_p = (self.particles - min_val) / (max_val - min_val + 1e-8)
        
        # 计算每一维的标准差作为简单熵替代
        # std 越大 -> 熵越大 -> 多样性越好
        avg_std = torch.mean(torch.std(norm_p, dim=0))
        return avg_std.item()

    def step(self, it):
        diversity = self._calculate_entropy()
        
        # 自适应逻辑:
        # 如果多样性低(diversity < 0.1), 增大 w (斥力), 减小 c2 (引力)
        # 如果多样性高(diversity > 0.5), 减小 w (收敛), 增大 c2
        if diversity < 0.1:
            w = 0.9
            c1, c2 = 2.0, 1.0
        elif diversity > 0.5:
            w = 0.4
            c1, c2 = 1.0, 2.0
        else:
            w = 0.7
            c1, c2 = 1.5, 1.5
            
        r1 = torch.rand(self.pop_size, self.dim, device=CFG.DEVICE)
        r2 = torch.rand(self.pop_size, self.dim, device=CFG.DEVICE)
        
        self.velocities = (w * self.velocities + 
                           c1 * r1 * (self.pbest_pos - self.particles) + 
                           c2 * r2 * (self.gbest_pos - self.particles))
        self.particles += self.velocities
