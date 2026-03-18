import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def calc_revenue(V):
    return V * (375.0 / 167.0)

def calc_satisfaction(V, HPI=438):
    score_crowd = 100 / (1 + np.exp(0.1 * (V - 140)))
    return score_crowd

def check_constraints(V, alpha_env, W_cap_base=16.0):
    water_demand = 3.5 + V * 0.03
    alpha_inf = 1.0 - alpha_env
    revenue = calc_revenue(V) * 0.06
    w_cap_new = W_cap_base + 0.3 * np.log1p(revenue * alpha_inf)
    
    constraint_water = w_cap_new - water_demand
    
    glacier_retreat = 10 + 0.1 * V * (1 - alpha_env * 0.5)
    constraint_glacier = 25.0 - glacier_retreat
    
    return constraint_water, constraint_glacier

print("正在执行多目标优化搜索 (Monte Carlo)...")

n_samples = 5000
V_samples = np.random.uniform(50, 300, n_samples)
Alpha_samples = np.random.uniform(0.1, 0.9, n_samples)

results = []

for v, alpha in zip(V_samples, Alpha_samples):
    obj_econ = calc_revenue(v)
    obj_social = calc_satisfaction(v)
    
    c_water, c_glacier = check_constraints(v, alpha)
    
    is_feasible = (c_water >= 0) and (c_glacier >= 0)
    
    results.append({
        'Visitors': v,
        'Alpha_Env': alpha,
        'Economic': obj_econ,
        'Satisfaction': obj_social,
        'Feasible': is_feasible,
        'Water_Margin': c_water,
        'Glacier_Margin': c_glacier
    })

df_res = pd.DataFrame(results)
df_feasible = df_res[df_res['Feasible']].copy()

print(f"采样 {n_samples} 次，可行解 {len(df_feasible)} 个")

def is_pareto_efficient(costs):
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, c in enumerate(costs):
        if is_efficient[i]:
            is_efficient[is_efficient] = np.any(costs[is_efficient] > c, axis=1)
            is_efficient[i] = True
    return is_efficient

df_feasible = df_feasible.sort_values('Economic', ascending=False)
pareto_front = []
max_sat = -1

for _, row in df_feasible.iterrows():
    if row['Satisfaction'] > max_sat:
        pareto_front.append(row)
        max_sat = row['Satisfaction']

df_pareto = pd.DataFrame(pareto_front)
print(f"Pareto 最优解数量: {len(df_pareto)}")

econ_norm = (df_pareto['Economic'] - df_pareto['Economic'].min()) / (df_pareto['Economic'].max() - df_pareto['Economic'].min())
sat_norm = (df_pareto['Satisfaction'] - df_pareto['Satisfaction'].min()) / (df_pareto['Satisfaction'].max() - df_pareto['Satisfaction'].min())

dist = np.sqrt((1 - econ_norm)**2 + (1 - sat_norm)**2)
best_idx = dist.idxmin()
best_solution = df_pareto.loc[best_idx]

print("\n--- 最优折衷解 (Best Compromise Solution) ---")
print(f"游客上限: {best_solution['Visitors']:.1f} 万人/年")
print(f"环保投资: {best_solution['Alpha_Env']*100:.1f}%")
print(f"经济收益: ${best_solution['Economic']:.1f} M")
print(f"居民满意度: {best_solution['Satisfaction']:.1f} 分")

plt.figure(figsize=(10, 6))

plt.scatter(df_feasible['Economic'], df_feasible['Satisfaction'], c='gray', alpha=0.1, label='Feasible Solution Space')
plt.plot(df_pareto['Economic'], df_pareto['Satisfaction'], 'r-o', linewidth=2, label='Pareto Front')
plt.scatter(best_solution['Economic'], best_solution['Satisfaction'], s=200, c='gold', edgecolors='k', zorder=10, label='Optimal Compromise Solution (TOPSIS)')

plt.xlabel('Economic Benefit (Million USD)')
plt.ylabel('Resident Satisfaction (0-100)')
plt.title('Multi-Objective Optimization Pareto Front Analysis')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.3)
plt.savefig('optimization_pareto.png')
print("\n优化结果图已保存为 optimization_pareto.png")
