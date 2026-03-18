import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

class JuneauProblem:
    def __init__(self):
        self.bounds = [(50, 300), (0.1, 0.9), (0.1, 0.9)]
        self.n_vars = 3
        self.n_obj = 4

    def evaluate(self, x):
        V, alpha_env, alpha_inf = x
        
        if alpha_env + alpha_inf > 1.0:
            alpha_env = alpha_env / (alpha_env + alpha_inf) * 0.9
            alpha_inf = alpha_inf / (alpha_env + alpha_inf) * 0.9
        
        e = 224.55 / 1000
        direct_spending = V * e
        
        total_revenue = V * (375.0 / 167.0)
        taxes = total_revenue * 0.06
        
        f1 = -(direct_spending + taxes)
        
        T_Z = 0
        V_Z = (V - 100.0) / 30.0
        b_eff = 6.73 * (1 - 0.5 * alpha_env)
        dG_dt = 0.31 * T_Z + b_eff * V_Z + 4.66
        
        glacier_cost = dG_dt * 0.05
        
        carbon_per_visitor = 0.82
        total_carbon = V * 10000 * carbon_per_visitor
        shadow_price = 100
        carbon_cost = (total_carbon * shadow_price) / 1e6
        
        f2 = glacier_cost + carbon_cost
        
        water_demand_summer = 3.5 + V * 0.03
        
        muni_revenue = total_revenue * 0.06
        w_cap_base = 16.0
        w_cap_gain = 0.3 * np.log1p(muni_revenue * alpha_inf)
        w_cap_total = w_cap_base + w_cap_gain
        
        f3 = water_demand_summer / max(w_cap_total, 0.1)
        
        HPI_base = 150
        HPI_current = HPI_base + 1.5 * V
        HPI_increase = (HPI_current - HPI_base) / HPI_base
        
        area_core = 5.0
        density = V * 10000 / area_core
        crowding = np.log1p(density / 10000.0)
        
        f4 = 0.5 * HPI_increase + 0.5 * crowding
        
        g1 = max(0, water_demand_summer - w_cap_total)
        g2 = max(0, dG_dt - 15.0)
        
        penalty = 1e5 * (g1 + g2)
        
        return [f1 + penalty, f2 + penalty, f3 + penalty, f4 + penalty]

class Individual:
    def __init__(self, problem):
        self.x = [random.uniform(b[0], b[1]) for b in problem.bounds]
        self.obj = []
        self.rank = 0
        self.distance = 0

def non_dominated_sort(population):
    fronts = [[]]
    for p in population:
        p.S = []
        p.n = 0
        for q in population:
            p_dominates_q = all(p.obj[i] <= q.obj[i] for i in range(len(p.obj))) and \
                            any(p.obj[i] < q.obj[i] for i in range(len(p.obj)))
            if p_dominates_q:
                p.S.append(q)
            elif all(q.obj[i] <= p.obj[i] for i in range(len(q.obj))) and \
                 any(q.obj[i] < p.obj[i] for i in range(len(q.obj))):
                p.n += 1
        
        if p.n == 0:
            p.rank = 0
            fronts[0].append(p)
            
    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in p.S:
                q.n -= 1
                if q.n == 0:
                    q.rank = i + 1
                    next_front.append(q)
        i += 1
        fronts.append(next_front)
    
    return fronts[:-1]

def crowding_distance(front):
    l = len(front)
    if l == 0: return
    
    for p in front: p.distance = 0
    
    for m in range(len(front[0].obj)):
        front.sort(key=lambda x: x.obj[m])
        front[0].distance = float('inf')
        front[-1].distance = float('inf')
        
        obj_range = front[-1].obj[m] - front[0].obj[m]
        if obj_range == 0: continue
        
        for i in range(1, l-1):
            front[i].distance += (front[i+1].obj[m] - front[i-1].obj[m]) / obj_range

def tournament_selection(pop):
    a, b = random.sample(pop, 2)
    if a.rank < b.rank: return a
    elif b.rank < a.rank: return b
    elif a.distance > b.distance: return a
    else: return b

def crossover(p1, p2, problem):
    c1, c2 = Individual(problem), Individual(problem)
    alpha = random.random()
    for i in range(problem.n_vars):
        c1.x[i] = alpha * p1.x[i] + (1-alpha) * p2.x[i]
        c2.x[i] = (1-alpha) * p1.x[i] + alpha * p2.x[i]
    return c1, c2

def mutation(ind, problem):
    for i in range(problem.n_vars):
        if random.random() < 0.1:
            ind.x[i] += random.gauss(0, (problem.bounds[i][1]-problem.bounds[i][0])*0.1)
            ind.x[i] = max(problem.bounds[i][0], min(problem.bounds[i][1], ind.x[i]))

def run_nsga2(n_gen=50, pop_size=100):
    print(f"开始 NSGA-II 优化 (代数={n_gen}, 种群={pop_size})...")
    problem = JuneauProblem()
    
    pop = [Individual(problem) for _ in range(pop_size)]
    for p in pop: p.obj = problem.evaluate(p.x)
    
    for gen in range(n_gen):
        offspring = []
        while len(offspring) < pop_size:
            p1 = tournament_selection(pop)
            p2 = tournament_selection(pop)
            c1, c2 = crossover(p1, p2, problem)
            mutation(c1, problem)
            mutation(c2, problem)
            c1.obj = problem.evaluate(c1.x)
            c2.obj = problem.evaluate(c2.x)
            offspring.extend([c1, c2])
            
        combined_pop = pop + offspring
        
        fronts = non_dominated_sort(combined_pop)
        
        new_pop = []
        for front in fronts:
            crowding_distance(front)
            if len(new_pop) + len(front) <= pop_size:
                new_pop.extend(front)
            else:
                front.sort(key=lambda x: x.distance, reverse=True)
                new_pop.extend(front[:pop_size - len(new_pop)])
                break
        
        pop = new_pop
        if gen % 10 == 0: print(f"  Generation {gen} completed")

    return pop

if __name__ == "__main__":
    final_pop = run_nsga2()
    
    fronts = non_dominated_sort(final_pop)
    pareto_front = fronts[0]
    
    data = []
    for p in pareto_front:
        alpha_env = p.x[1]
        alpha_inf = p.x[2]
        if alpha_env + alpha_inf > 1.0:
            total = alpha_env + alpha_inf
            alpha_env = alpha_env / total * 0.9
            alpha_inf = alpha_inf / total * 0.9
        
        data.append({
            'Visitors': p.x[0],
            'Alpha_Env': alpha_env,
            'Alpha_Inf': alpha_inf,
            'Economic': -p.obj[0],
            'Env_Cost': p.obj[1],
            'Infra_Load': p.obj[2],
            'Social_Stress': p.obj[3]
        })
    
    df = pd.DataFrame(data).drop_duplicates()
    
    df['Econ_Norm'] = (df['Economic'] - df['Economic'].min()) / (df['Economic'].max() - df['Economic'].min())
    df['Env_Norm'] = 1 - (df['Env_Cost'] - df['Env_Cost'].min()) / (df['Env_Cost'].max() - df['Env_Cost'].min())
    df['Infra_Norm'] = 1 - (df['Infra_Load'] - df['Infra_Load'].min()) / (df['Infra_Load'].max() - df['Infra_Load'].min())
    df['Social_Norm'] = 1 - (df['Social_Stress'] - df['Social_Stress'].min()) / (df['Social_Stress'].max() - df['Social_Stress'].min())
    
    df['Dist'] = np.sqrt((1-df['Econ_Norm'])**2 + (1-df['Env_Norm'])**2 + 
                         (1-df['Infra_Norm'])**2 + (1-df['Social_Norm'])**2)
    
    best_sol = df.loc[df['Dist'].idxmin()]
    
    print("\n=== NSGA-II 四目标优化结果 ===")
    print(f"Pareto 解数量: {len(df)}")
    print(f"\n最优折衷解 (TOPSIS):")
    print(f"  游客上限: {best_sol['Visitors']:.1f} 万人/年")
    print(f"  环保投资: {best_sol['Alpha_Env']*100:.1f}%")
    print(f"  基建投资: {best_sol['Alpha_Inf']*100:.1f}%")
    print(f"  其他支出: {(1.0 - best_sol['Alpha_Env'] - best_sol['Alpha_Inf'])*100:.1f}%")
    print(f"\n目标值:")
    print(f"  f1 (经济收益): ${best_sol['Economic']:.2f} M")
    print(f"  f2 (环境损耗): ${best_sol['Env_Cost']:.2f} M")
    print(f"  f3 (基建负荷率): {best_sol['Infra_Load']:.3f} ({best_sol['Infra_Load']*100:.1f}%)")
    print(f"  f4 (社会压迫指数): {best_sol['Social_Stress']:.3f}")
    
    print(f"\n--- 结果解读 ---")
    print(f"✓ 游客量建议: {best_sol['Visitors']:.0f} 万人/年")
    print(f"  (对比 2023 年 167 万人，建议削减 {(1-best_sol['Visitors']/167)*100:.0f}%)")
    print(f"✓ 投资策略: 环保 {best_sol['Alpha_Env']*100:.0f}% + 基建 {best_sol['Alpha_Inf']*100:.0f}%")
    print(f"✓ 基建负荷率 {best_sol['Infra_Load']*100:.1f}% < 100%，供水系统安全")
    if best_sol['Social_Stress'] < 2.0:
        print(f"✓ 社会压迫指数 {best_sol['Social_Stress']:.2f} 处于可接受范围")
    else:
        print(f"⚠ 社会压迫指数 {best_sol['Social_Stress']:.2f} 较高，需关注居民满意度")
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('NSGA-II Four-Objective Optimization Pareto Front (2D Projections)', fontsize=14, weight='bold')
    
    ax = axes[0, 0]
    ax.scatter(df['Economic'], df['Env_Cost'], c='blue', alpha=0.6, label='Pareto Front')
    ax.scatter(best_sol['Economic'], best_sol['Env_Cost'], c='gold', s=200, edgecolors='k', zorder=10, label='Best Compromise')
    ax.set_xlabel('Economic Benefit ($M)')
    ax.set_ylabel('Environmental Cost ($M)')
    ax.set_title('f1 vs f2')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.3)
    
    ax = axes[0, 1]
    ax.scatter(df['Economic'], df['Infra_Load'], c='blue', alpha=0.6)
    ax.scatter(best_sol['Economic'], best_sol['Infra_Load'], c='gold', s=200, edgecolors='k', zorder=10)
    ax.set_xlabel('Economic Benefit ($M)')
    ax.set_ylabel('Infrastructure Load Rate')
    ax.set_title('f1 vs f3')
    ax.grid(True, linestyle='--', alpha=0.3)
    
    ax = axes[0, 2]
    ax.scatter(df['Economic'], df['Social_Stress'], c='blue', alpha=0.6)
    ax.scatter(best_sol['Economic'], best_sol['Social_Stress'], c='gold', s=200, edgecolors='k', zorder=10)
    ax.set_xlabel('Economic Benefit ($M)')
    ax.set_ylabel('Social Stress Index')
    ax.set_title('f1 vs f4')
    ax.grid(True, linestyle='--', alpha=0.3)
    
    ax = axes[1, 0]
    ax.scatter(df['Env_Cost'], df['Infra_Load'], c='blue', alpha=0.6)
    ax.scatter(best_sol['Env_Cost'], best_sol['Infra_Load'], c='gold', s=200, edgecolors='k', zorder=10)
    ax.set_xlabel('Environmental Cost ($M)')
    ax.set_ylabel('Infrastructure Load Rate')
    ax.set_title('f2 vs f3')
    ax.grid(True, linestyle='--', alpha=0.3)
    
    ax = axes[1, 1]
    ax.scatter(df['Env_Cost'], df['Social_Stress'], c='blue', alpha=0.6)
    ax.scatter(best_sol['Env_Cost'], best_sol['Social_Stress'], c='gold', s=200, edgecolors='k', zorder=10)
    ax.set_xlabel('Environmental Cost ($M)')
    ax.set_ylabel('Social Stress Index')
    ax.set_title('f2 vs f4')
    ax.grid(True, linestyle='--', alpha=0.3)
    
    ax = axes[1, 2]
    ax.scatter(df['Infra_Load'], df['Social_Stress'], c='blue', alpha=0.6)
    ax.scatter(best_sol['Infra_Load'], best_sol['Social_Stress'], c='gold', s=200, edgecolors='k', zorder=10)
    ax.set_xlabel('Infrastructure Load Rate')
    ax.set_ylabel('Social Stress Index')
    ax.set_title('f3 vs f4')
    ax.grid(True, linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('nsga2_pareto_4d.png', dpi=300, bbox_inches='tight')
    print("\n图表已保存为 nsga2_pareto_4d.png")
