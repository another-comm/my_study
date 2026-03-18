class Config:
    # --- 环境物理参数 ---
    X_END = 1.0
    Y_END = 1.0
    GRAVITY = 9.8
    MU = 0            # 动摩擦系数
    DRAG_COEFF = 0.47   # 空气阻力系数
    
    # [新增] 是否启用曲率离心力对摩擦的贡献
    # True: N = mg*cos + mv^2/rho (更真实的物理，路径倾向平缓)
    # False: N = mg*cos (简化物理，路径倾向陡峭)
    ENABLE_CENTRIFUGAL = False 
    
    # --- 数值积分参数 ---
    RK_STEPS = 100      # 物理评估时的积分步数
    
    # --- 神经网络参数 ---
    HIDDEN_SIZE = 16    # 隐藏层大小
    
    # --- 优化算法参数 ---
    NUM_PARTICLES = 128 # 种群大小
    MAX_ITER = 200      # 最大迭代次数
    
    # 算法选择: 'PSO', 'EntropyPSO', 'QPSO'
    ALGO_TYPE = 'EntropyPSO'  

CFG = Config()