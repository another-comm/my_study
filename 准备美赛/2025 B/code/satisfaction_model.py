import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

try:
    df = pd.read_csv('juneau_data_processed.csv')
except FileNotFoundError:
    print("错误：请先运行 data_preprocessing.py")
    exit()

def calculate_satisfaction(V, HPI, params):
    V_threshold = params.get('V_threshold', 150)
    k_crowd = params.get('k_crowd', 0.05)
    
    score_crowd = 1.0 / (1.0 + np.exp(k_crowd * (V - V_threshold)))
    
    HPI_base = params.get('HPI_base', 150)
    HPI_limit = params.get('HPI_limit', 500)
    
    hpi_stress = (HPI - HPI_base) / (HPI_limit - HPI_base)
    hpi_stress = np.clip(hpi_stress, 0, 1)
    
    score_econ = 1.0 - hpi_stress
    
    w_crowd = 0.6
    w_econ = 0.4
    
    rsi = 100 * (w_crowd * score_crowd + w_econ * score_econ)
    
    return rsi, score_crowd, score_econ

params = {
    'V_threshold': 140,
    'k_crowd': 0.1,
    'HPI_base': 150,
    'HPI_limit': 550
}

rsi_list = []
crowd_list = []
econ_list = []

for idx, row in df.iterrows():
    rsi, s_c, s_e = calculate_satisfaction(row['Visitors_Smoothed'], row['HPI'], params)
    rsi_list.append(rsi)
    crowd_list.append(s_c)
    econ_list.append(s_e)

df['RSI'] = rsi_list
df['Score_Crowd'] = crowd_list
df['Score_Econ'] = econ_list

print("--- 居民满意度模型结果 (2019-2024) ---")
print(df[['Year', 'Visitors_Smoothed', 'HPI', 'RSI']].tail(6))

min_rsi = df['RSI'].min()
min_year = df.loc[df['RSI'].idxmin(), 'Year']
print(f"\n最低满意度出现在 {min_year} 年，RSI = {min_rsi:.1f}")
if min_rsi < 60:
    print("警报：满意度已跌破及格线 (60分)，说明过度旅游已引发社会危机！")

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(df['Year'], df['RSI'], 'g-o', linewidth=2, label='Comprehensive Satisfaction (RSI)')
ax1.set_xlabel('Year')
ax1.set_ylabel('Satisfaction Index (0-100)', color='g')
ax1.tick_params(axis='y', labelcolor='g')
ax1.set_ylim(0, 100)

ax1.axhline(y=60, color='r', linestyle='--', alpha=0.5, label='Alert Line (60)')
ax1.axhline(y=40, color='darkred', linestyle=':', alpha=0.5, label='Crisis Line (40)')

ax2 = ax1.twinx()
ax2.bar(df['Year'], df['Visitors_Smoothed'], alpha=0.15, color='blue', label='Visitors (Background)')
ax2.set_ylabel('Visitors (10k)', color='b')
ax2.tick_params(axis='y', labelcolor='b')

plt.title('Juneau Resident Satisfaction Evolution (2000-2024)\n$RSI = f_{crowd}(V) \cdot w_1 + f_{econ}(HPI) \cdot w_2$')
fig.tight_layout()
plt.savefig('resident_satisfaction_model.png')
print("\n图表已保存为 resident_satisfaction_model.png")
