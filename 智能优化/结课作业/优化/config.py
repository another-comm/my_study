import torch

class Config:
    # --- 环境物理参数 ---
    X_END = 1.0
    Y_END = 1.0
    GRAVITY = 9.8
    MU = 0       # 动摩擦系数 (库伦摩擦+粘滞阻力)
    DRAG_COEFF = 0  # 空气阻力系数
    
    # 是否启用曲率离心力对摩擦的贡献（向心力引起的法向力变化）
    ENABLE_CENTRIFUGAL = False  
    # --- 数值积分参数 ---
    RK_STEPS = 1000      # 物理评估时的积分步数 
    
    # --- 神经网络参数 ---
    HIDDEN_SIZE = 16    # 隐藏层大小
    # 目前仅使用 MLP 模型
    MODEL_TYPE = 'MLP'
    
    # --- 优化算法参数 ---
    NUM_PARTICLES = 80    # 种群大小 (混合策略下可适当减少)
    MAX_ITER = 200        # PSO 迭代次数 (混合策略下主要用于粗定位)
    BATCH_PARTICLES = 32  # Phase1 评估批大小，减少 Python 循环
    PSO_POS_INIT_RANGE = 0.5  # PSO 粒子初始位置范围 [-range, range]
    ENTROPY_BINS = 20     # 熵权PSO中直方图分箱数，用于估计真实香农熵
    
    # 算法选择: 'PSO', 'EntropyPSO'
    ALGO_TYPE = 'PSO'
    
    # ---  混合优化策略 (Hybrid Neuroevolution) ---
    ENABLE_HYBRID = False      # 是否启用 PSO + Gradient (关闭以纯PSO对比)
    GRAD_STEPS = 200         # 梯度下降精调步数
    LEARNING_RATE = 0.002      # 梯度下降学习率
    ENABLE_AMP = True         # Phase2 是否启用混合精度 (CUDA 下有效)
    
    # ---  问题类型 ---
    # 'Brachistochrone': 最速降线问题 (1D -> 1D)
    PROBLEM_TYPE = 'Brachistochrone'

    # --- 设备 ---
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CFG = Config()

#ssh -i id_rsa -p 42016 root@xj-member.bitahub.com 