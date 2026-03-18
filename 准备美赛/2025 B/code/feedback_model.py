import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

class FeedbackSystem:
    def __init__(self, initial_cap=16.0, initial_beta=6.73):
        self.w_cap = initial_cap
        self.beta = initial_beta
        self.history = {'year': [], 'w_cap': [], 'beta': [], 'revenue': []}
        
    def step(self, year, visitors, revenue_base_2023=22.28, policy_split=(0.4, 0.3)):
        current_revenue = revenue_base_2023 * (visitors / 167.0)
        
        alpha_inf, alpha_env = policy_split
        invest_inf = current_revenue * alpha_inf
        invest_env = current_revenue * alpha_env
        
        k_inf = 0.3 
        w_gain = k_inf * np.log1p(invest_inf)
        self.w_cap += w_gain
        
        eta = 0.01 
        decay_factor = np.exp(-eta * invest_env) 
        self.beta *= decay_factor
        
        self.history['year'].append(year)
        self.history['w_cap'].append(self.w_cap)
        self.history['beta'].append(self.beta)
        self.history['revenue'].append(current_revenue)
        
        return self.w_cap, self.beta

print("--- 反馈机制模拟 (2025-2035) ---")
print("场景：游客量每年增长 5%，策略分配 [40% 基建, 30% 环保, 30% 其他]")

sim = FeedbackSystem()
years = range(2025, 2036)
v_current = 167.0

print(f"{'年份':<6} | {'游客(万)':<8} | {'收入($M)':<8} | {'水承载力':<8} | {'破坏系数':<8}")
print("-" * 60)

for y in years:
    v_current *= 1.05
    w, b = sim.step(y, v_current, policy_split=(0.4, 0.3))
    r = sim.history['revenue'][-1]
    print(f"{y:<6} | {v_current:<8.1f} | {r:<8.2f} | {w:<8.2f} | {b:<8.3f}")

hist = sim.history
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(hist['year'], hist['w_cap'], 'b-o', label='Water Capacity ($W_{cap}$)')
ax1.set_title('Infrastructure Investment Feedback: Capacity Enhancement')
ax1.set_xlabel('Year')
ax1.set_ylabel('MGD (Million Gallons/Day)')
ax1.grid(True)
ax1.legend()

ax2.plot(hist['year'], hist['beta'], 'g-s', label='Destruction Coefficient ($\\beta$)')
ax2.set_title('Environmental Investment Feedback: Impact Mitigation')
ax2.set_xlabel('Year')
ax2.set_ylabel('Coefficient Value (Initial=6.73)')
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.savefig('feedback_simulation.png')
print("\n[结论] 反馈模拟图已保存为 feedback_simulation.png")
print("观察：随着资金持续注入，系统承载力在10年内显著提升，同时单位游客的破坏性在下降。")
print("这证明了'以游养游' (Sustainable Reinvestment) 的可行性。")
