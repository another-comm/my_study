import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def evaluate_sustainability(V_cap, alpha_env, alpha_inf, diversion_strength):
    v_core = V_cap * (1 - 0.1 * diversion_strength)
    
    revenue = V_cap * 225 * (1 + 0.05 * diversion_strength)
    score_econ = min(100, revenue / 375.0 * 100)
    
    b_eff = 6.73 * (1 - 0.6 * alpha_env)
    dG = b_eff * (v_core / 100.0) + 4.66
    score_env = max(0, 100 - dG * 5)
    
    w_cap = 16.0 + 5.0 * alpha_inf
    demand = 3.5 + V_cap * 0.03
    risk_water = max(0, (demand - w_cap) / w_cap)
    
    crowd_penalty = max(0, (v_core - 80) / 80 * 50)
    score_social = max(0, 100 - risk_water * 200 - crowd_penalty)
    
    total_score = 0.3 * score_econ + 0.4 * score_env + 0.3 * score_social
    return total_score

def run_sobol_analysis():
    print("正在执行 Sobol 全局灵敏度分析...")
    
    bounds = [
        ('Visitor Cap', 50, 200),
        ('Environmental Investment', 0.1, 0.9),
        ('Infrastructure Investment', 0.1, 0.9),
        ('Diversion Strength', 0.0, 5.0)
    ]
    
    n_samples = 10000
    param_names = [b[0] for b in bounds]
    n_params = len(bounds)
    
    A = np.zeros((n_samples, n_params))
    B = np.zeros((n_samples, n_params))
    
    for i, (name, low, high) in enumerate(bounds):
        A[:, i] = np.random.uniform(low, high, n_samples)
        B[:, i] = np.random.uniform(low, high, n_samples)
    
    Y_A = np.array([evaluate_sustainability(*row) for row in A])
    var_Y = np.var(Y_A)
    print(f"模型输出总方差: {var_Y:.2f}")
    
    sobol_indices = []
    
    for i in range(n_params):
        AB_i = A.copy()
        AB_i[:, i] = B[:, i]
        
        Y_AB_i = np.array([evaluate_sustainability(*row) for row in AB_i])
        
        C = A.copy()
        C[:, i] = B[:, i]
        Y_C = np.array([evaluate_sustainability(*row) for row in C])
        
        Y_B = np.array([evaluate_sustainability(*row) for row in B])
        
        diff_sq = (Y_A - Y_C)**2
        ST = 0.5 * np.mean(diff_sq) / var_Y
        
        C_S1 = B.copy()
        C_S1[:, i] = A[:, i]
        Y_C_S1 = np.array([evaluate_sustainability(*row) for row in C_S1])
        
        S1 = np.mean(Y_A * (Y_C_S1 - Y_B)) / var_Y
        
        sobol_indices.append({
            'Parameter': param_names[i],
            'S1 (主效应)': max(0, S1),
            'ST (总效应)': ST
        })

    df_sobol = pd.DataFrame(sobol_indices)
    
    df_sobol['S1_Norm'] = df_sobol['S1 (主效应)'] / df_sobol['S1 (主效应)'].sum()
    
    print("\n--- Sobol 灵敏度分析结果 ---")
    print(df_sobol.round(3))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(n_params)
    width = 0.35
    
    ax.bar(x - width/2, df_sobol['S1 (主效应)'], width, label='S1 (Independent Contribution)', color='steelblue')
    ax.bar(x + width/2, df_sobol['ST (总效应)'], width, label='ST (Total=Independent+Interaction)', color='lightcoral')
    
    ax.set_ylabel('Sensitivity Index')
    ax.set_title('Contribution Rate of Policy Factors to System Sustainability (Sobol)')
    ax.set_xticks(x)
    ax.set_xticklabels(param_names, rotation=15, ha='right')
    ax.legend()
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('sobol_sensitivity.png')
    print("\n图表已保存为 sobol_sensitivity.png")
    
    top_factor = df_sobol.loc[df_sobol['ST (总效应)'].idxmax(), 'Parameter']
    print(f"\n[结论] 对系统可持续性影响最大的因子是：**{top_factor}**。")
    print("这意味着政策制定应优先关注此变量的调控。")
    print("注：ST > S1 的部分代表该变量与其他变量存在'交互效应' (Interaction Effect)。")

if __name__ == "__main__":
    run_sobol_analysis()
