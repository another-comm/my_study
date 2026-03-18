import numpy as np

# 基类：包含通用属性和结果记录逻辑
class BaseOptimizer:
    def __init__(self, dim, pop_size, max_iter):
        self.dim = dim
        self.pop_size = pop_size
        self.max_iter = max_iter
        
        # 初始化位置 (-0.5, 0.5) 范围
        self.particles = np.random.uniform(-0.5, 0.5, (pop_size, dim))
        
        self.pbest_pos = self.particles.copy()
        self.pbest_score = np.full(pop_size, float('inf'))
        
        self.gbest_pos = np.zeros(dim)
        self.gbest_score = float('inf')
        
        self.history = []
        
    def update_pbest(self, scores):
        """通用更新逻辑: 更新个体最优(pbest)和全局最优(gbest)"""
        # 更新 PBest
        improved = scores < self.pbest_score
        self.pbest_score[improved] = scores[improved]
        self.pbest_pos[improved] = self.particles[improved]
        
        # 更新 GBest
        min_score_idx = np.argmin(self.pbest_score)
        if self.pbest_score[min_score_idx] < self.gbest_score:
            self.gbest_score = self.pbest_score[min_score_idx]
            self.gbest_pos = self.pbest_pos[min_score_idx].copy()
            
        self.history.append(self.gbest_score)

# 1. 标准 PSO
class StandardPSO(BaseOptimizer):
    def __init__(self, dim, pop_size, max_iter):
        super().__init__(dim, pop_size, max_iter)
        self.velocities = np.random.uniform(-0.1, 0.1, (pop_size, dim))
        
    def step(self, it):
        w = 0.9 - 0.5 * (it / self.max_iter) # 线性递减权重
        c1, c2 = 1.5, 1.5
        
        r1 = np.random.rand(self.pop_size, self.dim)
        r2 = np.random.rand(self.pop_size, self.dim)
        
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
        min_val = np.min(self.particles, axis=0)
        max_val = np.max(self.particles, axis=0)
        norm_p = (self.particles - min_val) / (max_val - min_val + 1e-8)
        
        # 计算每一维的标准差作为简单熵替代
        # std 越大 -> 熵越大 -> 多样性越好
        avg_std = np.mean(np.std(self.particles, axis=0))
        return avg_std

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
            
        r1 = np.random.rand(self.pop_size, self.dim)
        r2 = np.random.rand(self.pop_size, self.dim)
        
        self.velocities = (w * self.velocities + 
                           c1 * r1 * (self.pbest_pos - self.particles) + 
                           c2 * r2 * (self.gbest_pos - self.particles))
        self.particles += self.velocities

# 3. 量子 PSO (QPSO) - 无速度向量，基于波函数坍缩
class QPSO(BaseOptimizer):
    def step(self, it):
        # 收缩-扩张系数 alpha (线性递减)
        alpha = 1.0 - 0.5 * (it / self.max_iter)
        
        # 计算 mbest (Mean Best Position) - 种群所有 PBest 的平均中心
        mbest = np.mean(self.pbest_pos, axis=0)
        
        # 逐个粒子更新
        # x(t+1) = p +/- alpha * |mbest - x(t)| * ln(1/u)
        # p = (c1*pbest + c2*gbest) / (c1+c2)
        
        phi = np.random.rand(self.pop_size, self.dim)
        p = phi * self.pbest_pos + (1 - phi) * self.gbest_pos
        
        u = np.random.rand(self.pop_size, self.dim)
        
        # 这一步决定是向左还是向右坍缩
        sign = np.where(np.random.rand(self.pop_size, self.dim) > 0.5, 1, -1)
        
        # QPSO 核心公式
        self.particles = p + sign * alpha * np.abs(mbest - self.particles) * np.log(1 / (u + 1e-8))
