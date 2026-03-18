import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def run_simulation(V_target, alpha_env, delta_T=0, n_sims=10000):
    T_sim = np.random.normal(5.0 + delta_T, 1.2, n_sims)
    
    W_base_sim = np.random.normal(16.0, 2.5, n_sims)
    
    revenue = (V_target * 375.0 / 167.0) * 0.06
    invest_inf = revenue * (1 - alpha_env)
    W_gain = 0.3 * np.log1p(invest_inf)
    W_cap_total = W_base_sim + W_gain
    
    per_capita_water = np.random.normal(0.03, 0.005, n_sims)
    W_demand = 3.5 + V_target * per_capita_water
    
    T_mean = 4.5
    T_std = 1.5
    V_mean = 100.0
    V_std = 30.0
    
    T_Z = (T_sim - T_mean) / T_std
    V_Z = (V_target - V_mean) / V_std
    
    b_effective = 6.73 * (1 - alpha_env * 0.5)
    dG_dt = 0.31 * T_Z + b_effective * V_Z + 4.66
    
    risk_water = (W_demand > W_cap_total)
    
    risk_glacier = (dG_dt > 10.0)
    
    return risk_water, risk_glacier

print("--- 4.1 灵敏度与鲁棒性分析 ---")

V_opt = 125.6
Alpha_opt = 0.44

scenarios = [
    ("Baseline Scenario", 0),
    ("Warming +1°C", 1.0),
    ("Warming +2°C", 2.0)
]

results = []

print(f"测试策略: V={V_opt}万, Alpha_Env={Alpha_opt*100:.1f}%")
print(f"{'Scenario':<15} | {'Water Risk':<12} | {'Glacier Risk':<15} | {'Reliability':<12}")
print("-" * 65)

risk_data = []

for name, dt in scenarios:
    r_w, r_g = run_simulation(V_opt, Alpha_opt, delta_T=dt)
    
    prob_water = np.mean(r_w) * 100
    prob_glacier = np.mean(r_g) * 100
    reliability = 100 - (np.mean(r_w | r_g) * 100)
    
    print(f"{name:<10} | {prob_water:<9.1f}% | {prob_glacier:<11.1f}% | {reliability:<9.1f}%")
    
    risk_data.append([r_w, r_g])

labels = [s[0] for s in scenarios]
water_risks = [np.mean(d[0])*100 for d in risk_data]
glacier_risks = [np.mean(d[1])*100 for d in risk_data]

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 6))
rects1 = ax.bar(x - width/2, water_risks, width, label='Water Shortage Risk', color='skyblue')
rects2 = ax.bar(x + width/2, glacier_risks, width, label='Glacier Exceedance Risk', color='salmon')

ax.set_ylabel('Failure Probability (%)')
ax.set_title(f'Strategy Robustness Test (V={V_opt:.1f}万)\nSensitivity to Climate Warming')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()
ax.grid(True, axis='y', linestyle='--', alpha=0.3)

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

autolabel(rects1)
autolabel(rects2)

plt.tight_layout()
plt.savefig('sensitivity_robustness.png')
print("\n鲁棒性分析图已保存为 sensitivity_robustness.png")

print("\n[分析结论]")
if glacier_risks[-1] > 20:
    print("警报：在升温 2°C 的极端场景下，冰川保护目标的失效概率显著上升！")
    print(f"建议：即便执行了 V={V_opt} 的限流，若全球变暖失控，本地政策将失效。")
    print("这强调了模型的一个关键边界条件：本地可持续依赖于全球气候稳定。")
else:
    print("系统展现出较好的韧性，即便升温也能维持较低风险。")
