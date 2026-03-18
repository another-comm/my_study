import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def simulate_diversion_policy():
    print("--- 4.2 空间分流策略模拟 (Spatial Diversion) ---")
    
    cap_core = 5.2
    attract_core_base = 10.0
    
    cap_sub = 8.0
    attract_sub_base = 5.0
    
    beta_price = 0.5
    beta_crowd = 2.0
    
    strategies = np.linspace(0, 5, 20)
    
    results = []
    
    V_potential_range = np.linspace(3, 15, 50)
    
    for strat in strategies:
        attract_sub_new = attract_sub_base + strat
        
        max_capacity = 0
        
        for V_total in V_potential_range:
            v_c = V_total * 0.5
            v_s = V_total * 0.5
            
            for _ in range(10):
                dens_c = min(1.5, v_c / cap_core)
                dens_s = min(1.5, v_s / cap_sub)
                
                u_c = attract_core_base - beta_crowd * dens_c
                u_s = attract_sub_new - beta_crowd * dens_s
                
                prob_c = np.exp(u_c) / (np.exp(u_c) + np.exp(u_s))
                
                v_c = V_total * prob_c
                v_s = V_total * (1 - prob_c)
            
            if v_c <= cap_core:
                max_capacity = V_total
            else:
                break
        
        v_c_final = max_capacity * prob_c
        v_s_final = max_capacity * (1 - prob_c)
        ratio_sub = v_s_final / max_capacity
        
        results.append({
            'Strategy_Strength': strat,
            'System_Capacity': max_capacity,
            'Core_Visitors': v_c_final,
            'Sub_Visitors': v_s_final,
            'Diversion_Ratio': ratio_sub
        })
    
    df = pd.DataFrame(results)
    
    base_cap = df.iloc[0]['System_Capacity']
    best_cap = df.iloc[-1]['System_Capacity']
    improvement = (best_cap - base_cap) / base_cap * 100
    
    print(f"基准承载力 (无干预): {base_cap:.2f} 万人/日")
    print(f"最大承载力 (强干预): {best_cap:.2f} 万人/日")
    print(f"提升幅度: +{improvement:.1f}%")
    print("\n[结论] 分流策略实现了'软扩容'：在不扩建核心区物理设施的情况下，")
    print(f"通过优化客流分布，使系统总接待能力增加了 {improvement:.0f}%。")
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Policy Intervention Strength ($\\lambda$)\n(e.g., Ticket Discounts, Marketing Investment, Transportation Convenience)')
    ax1.set_ylabel('Total System Capacity (10k people/day)', color=color)
    ax1.plot(df['Strategy_Strength'], df['System_Capacity'], 'b-o', linewidth=2, label='Total Capacity')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.3)
    
    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Secondary Attraction Visitor Share (%)', color=color)
    ax2.plot(df['Strategy_Strength'], df['Diversion_Ratio']*100, 'r--', linewidth=2, label='Diversion Ratio')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 100)
    
    plt.title('Impact of Diversion Strategy on System Capacity Enhancement')
    fig.tight_layout()
    plt.savefig('policy_diversion.png')
    print("图表已保存为 policy_diversion.png")

if __name__ == "__main__":
    simulate_diversion_policy()
