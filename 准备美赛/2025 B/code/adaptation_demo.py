import numpy as np
import matplotlib.pyplot as plt
import random
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

class VeniceProblem:
    def __init__(self):
        self.bounds = [(2.0, 5.2), (5.0, 50.0), (0.1, 0.9)]
        self.n_vars = 3
        self.n_obj = 3

    def evaluate(self, x):
        V_daily, fee, alpha_maint = x
        
        V_annual = V_daily * 365.0 
        
        avg_spend = 70.0 + fee
        total_revenue = V_annual * avg_spend / 1e4
        
        f1 = -total_revenue
        
        maint_budget = total_revenue * alpha_maint
        mitigation = 0.5 * np.log1p(maint_budget / 100.0)
        
        vlm_human = 0.5 * ((V_daily / 5.2)**2) * (1 - min(0.8, mitigation))
        rslr = 4.2 + 1.2 + vlm_human
        
        f2 = rslr
        
        density = 2.0 * (V_daily / 5.2)
        f3 = density
        
        g1 = max(0, V_daily - 5.2)
        
        g2 = max(0, 10.0 - maint_budget)
        
        penalty_coeff = 100.0
        penalty = penalty_coeff * (g1 + g2)
        
        is_feasible = (g1 < 0.1) and (g2 < 0.1)
        
        return [f1 + penalty, f2 + penalty, f3 + penalty]

class Individual:
    def __init__(self, problem):
        self.x = [random.uniform(b[0], b[1]) for b in problem.bounds]
        self.obj = []
        self.rank = 0
        self.distance = 0

def fast_non_dominated_sort(population):
    fronts = [[]]
    for p in population:
        p.S = []
        p.n = 0
        for q in population:
            if all(p.obj[i] <= q.obj[i] for i in range(len(p.obj))) and any(p.obj[i] < q.obj[i] for i in range(len(p.obj))):
                p.S.append(q)
            elif all(q.obj[i] <= p.obj[i] for i in range(len(q.obj))) and any(q.obj[i] < p.obj[i] for i in range(len(q.obj))):
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

def calc_crowding_distance(front):
    l = len(front)
    if l == 0: return
    for p in front: p.distance = 0
    for m in range(len(front[0].obj)):
        front.sort(key=lambda x: x.obj[m])
        front[0].distance = float('inf')
        front[-1].distance = float('inf')
        rng = front[-1].obj[m] - front[0].obj[m]
        if rng == 0: continue
        for i in range(1, l-1):
            front[i].distance += (front[i+1].obj[m] - front[i-1].obj[m]) / rng

def run_venice_optimization():
    print("正在启动威尼斯模型迁移测试 (Venice Adaptation)...")
    problem = VeniceProblem()
    pop_size = 100
    n_gen = 50
    
    pop = [Individual(problem) for _ in range(pop_size)]
    for p in pop: p.obj = problem.evaluate(p.x)
    
    for gen in range(n_gen):
        offspring = []
        for _ in range(pop_size):
            p1, p2 = random.sample(pop, 2)
            parent = p1 if p1.rank < p2.rank else p2
            child = Individual(problem)
            child.x = [(x1+x2)/2 for x1, x2 in zip(p1.x, p2.x)]
            if random.random() < 0.2:
                idx = random.randint(0, 2)
                child.x[idx] += random.gauss(0, (problem.bounds[idx][1]-problem.bounds[idx][0])*0.1)
                child.x[idx] = max(problem.bounds[idx][0], min(problem.bounds[idx][1], child.x[idx]))
            
            child.obj = problem.evaluate(child.x)
            offspring.append(child)
            
        combined = pop + offspring
        fronts = fast_non_dominated_sort(combined)
        new_pop = []
        for front in fronts:
            calc_crowding_distance(front)
            front.sort(key=lambda x: x.distance, reverse=True)
            if len(new_pop) + len(front) <= pop_size:
                new_pop.extend(front)
            else:
                new_pop.extend(front[:pop_size - len(new_pop)])
                break
        pop = new_pop
        
    best_front = fast_non_dominated_sort(pop)[0]
    results = []
    for p in best_front:
        V_daily, fee, alpha_maint = p.x
        V_annual = V_daily * 365.0
        avg_spend = 70.0 + fee
        total_revenue = V_annual * avg_spend / 1e4
        
        maint_budget = total_revenue * alpha_maint
        mitigation = 0.5 * np.log1p(maint_budget / 100.0)
        vlm_human = 0.5 * ((V_daily / 5.2)**2) * (1 - min(0.8, mitigation))
        rslr = 4.2 + 1.2 + vlm_human
        density = 2.0 * (V_daily / 5.2)
        
        g1 = max(0, V_daily - 5.2)
        g2 = max(0, 10.0 - maint_budget)
        is_feasible = (g1 < 0.1) and (g2 < 0.1)
        
        results.append({
            'Visitors_Daily': V_daily,
            'Entry_Fee': fee,
            'Maint_Invest': alpha_maint,
            'Revenue_M': total_revenue,
            'RSLR_mm': rslr,
            'Density': density,
            'Feasible': is_feasible,
            'Constraint_Violation': g1 + g2
        })
    
    df = pd.DataFrame(results)
    
    df_feasible = df[df['Feasible'] == True].copy()
    if len(df_feasible) == 0:
        print("警告：未找到完全可行的解，使用约束违反最小的解")
        df_feasible = df.nsmallest(min(10, len(df)), 'Constraint_Violation')
    
    def safe_norm(series):
        if series.max() == series.min():
            return np.zeros_like(series)
        return (series - series.min()) / (series.max() - series.min())
    
    df_feasible['Rev_Norm'] = safe_norm(df_feasible['Revenue_M'])
    
    df_feasible['Env_Norm'] = 1 - safe_norm(df_feasible['RSLR_mm'])
    df_feasible['Soc_Norm'] = 1 - safe_norm(df_feasible['Density'])
    
    df_feasible['Score'] = np.sqrt((1-df_feasible['Rev_Norm'])**2 + 
                                    (1-df_feasible['Env_Norm'])**2 + 
                                    (1-df_feasible['Soc_Norm'])**2)
    
    if df_feasible['Score'].isna().all() or len(df_feasible) == 0:
        if len(df_feasible) > 0:
            best = df_feasible.iloc[0]
        else:
            print("错误：未找到可行解")
            return
    else:
        best = df_feasible.loc[df_feasible['Score'].idxmin()]
    
    print("\n=== 威尼斯模型迁移结果 ===")
    print(f"最优策略建议:")
    print(f"  日游客上限: {best['Visitors_Daily']:.2f} 万人 (阈值 5.2)")
    print(f"  入城费定价: €{best['Entry_Fee']:.2f} (现状 €5)")
    print(f"  维护投资比: {best['Maint_Invest']*100:.1f}%")
    print(f"预期结果:")
    print(f"  年总收入: €{best['Revenue_M']:.0f} M")
    print(f"  相对海平面上升: {best['RSLR_mm']:.2f} mm/yr")
    print(f"  圣马可广场密度: {best['Density']:.2f} 人/m2 (阈值 2.0)")
    
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Revenue_M'], df['Density'], c=df['RSLR_mm'], cmap='viridis', s=100)
    plt.colorbar(label='RSLR (mm/yr)')
    plt.scatter(best['Revenue_M'], best['Density'], c='red', marker='*', s=300, label='Optimal Solution')
    plt.xlabel('Annual Total Revenue (M€)')
    plt.ylabel('Crowd Density (people/m²)')
    plt.title('Venice Model Adaptation: Economic vs Crowding Trade-off\n(Color Represents Sea Level Rise Rate)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('venice_adaptation.png')
    print("图表已保存为 venice_adaptation.png")

if __name__ == "__main__":
    run_venice_optimization()
