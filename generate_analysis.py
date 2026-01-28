import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.font_manager import FontProperties

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取分析文件
analysis_file = "FastAPI_Server/experiments/results/congestion_analysis_20260120_134557.json"
with open(analysis_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取关键数据
scenarios = ['light', 'moderate', 'heavy', 'extreme']
sp_stats = []
dkspp_stats = []
time_improvements = []
efficiency_improvements = []

for scenario in scenarios:
    sp = data['by_congestion_algorithm'][scenario]['SP']
    dkspp = data['by_congestion_algorithm'][scenario]['D-KSPP']
    comparison = data['algorithm_comparison'][scenario]
    
    sp_stats.append({
        'scenario': scenario,
        'duration': sp['average_path_duration'],
        'efficiency': sp['traffic_efficiency']
    })
    
    dkspp_stats.append({
        'scenario': scenario,
        'duration': dkspp['average_path_duration'],
        'efficiency': dkspp['traffic_efficiency']
    })
    
    time_improvements.append({
        'scenario': scenario,
        'improvement': comparison['time_improvement']
    })
    
    efficiency_improvements.append({
        'scenario': scenario,
        'improvement': comparison['efficiency_improvement']
    })

# 创建数据框
sp_df = pd.DataFrame(sp_stats)
dkspp_df = pd.DataFrame(dkspp_stats)
time_imp_df = pd.DataFrame(time_improvements)
eff_imp_df = pd.DataFrame(efficiency_improvements)

# 合并数据框
comparison_df = pd.DataFrame({
    '拥堵场景': ['轻度', '中度', '重度', '极端'],
    'SP算法时间(s)': sp_df['duration'].round(2),
    'D-KSPP算法时间(s)': dkspp_df['duration'].round(2),
    '时间改进(%)': time_imp_df['improvement'].round(2),
    'SP算法效率': sp_df['efficiency'].round(6),
    'D-KSPP算法效率': dkspp_df['efficiency'].round(6),
    '效率改进(%)': eff_imp_df['improvement'].round(2)
})

# 生成清洗的表格
print("=" * 80)
print("D-KSPP算法性能优化分析表")
print("=" * 80)
print(comparison_df.to_string(index=False))
print("=" * 80)

# 保存表格到CSV
comparison_df.to_csv("performance_analysis.csv", index=False, encoding='utf-8-sig')
print("表格已保存到: performance_analysis.csv")

# 生成可视化图表
plt.figure(figsize=(12, 10))

# 1. 时间改进对比图
plt.subplot(2, 2, 1)
x = np.arange(len(comparison_df['拥堵场景']))
plt.bar(x - 0.2, comparison_df['SP算法时间(s)'], width=0.4, label='SP算法')
plt.bar(x + 0.2, comparison_df['D-KSPP算法时间(s)'], width=0.4, label='D-KSPP算法')
plt.xticks(x, comparison_df['拥堵场景'])
plt.xlabel('拥堵场景')
plt.ylabel('平均路径时间(s)')
plt.title('不同拥堵场景下的路径时间对比')
plt.legend()
plt.grid(axis='y', alpha=0.3)

# 2. 效率改进对比图
plt.subplot(2, 2, 2)
x = np.arange(len(comparison_df['拥堵场景']))
plt.bar(x - 0.2, comparison_df['SP算法效率'], width=0.4, label='SP算法')
plt.bar(x + 0.2, comparison_df['D-KSPP算法效率'], width=0.4, label='D-KSPP算法')
plt.xticks(x, comparison_df['拥堵场景'])
plt.xlabel('拥堵场景')
plt.ylabel('交通效率')
plt.title('不同拥堵场景下的交通效率对比')
plt.legend()
plt.grid(axis='y', alpha=0.3)

# 3. 时间改进百分比图
plt.subplot(2, 2, 3)
x = np.arange(len(comparison_df['拥堵场景']))
bars = plt.bar(x, comparison_df['时间改进(%)'], color='skyblue')
plt.xticks(x, comparison_df['拥堵场景'])
plt.xlabel('拥堵场景')
plt.ylabel('时间改进(%)')
plt.title('不同拥堵场景下的时间改进百分比')
plt.axhline(y=0, color='gray', linestyle='--')
plt.grid(axis='y', alpha=0.3)

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}%',
             ha='center', va='bottom')

# 4. 效率改进百分比图
plt.subplot(2, 2, 4)
x = np.arange(len(comparison_df['拥堵场景']))
bars = plt.bar(x, comparison_df['效率改进(%)'], color='lightgreen')
plt.xticks(x, comparison_df['拥堵场景'])
plt.xlabel('拥堵场景')
plt.ylabel('效率改进(%)')
plt.title('不同拥堵场景下的效率改进百分比')
plt.axhline(y=0, color='gray', linestyle='--')
plt.grid(axis='y', alpha=0.3)

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}%',
             ha='center', va='bottom')

plt.tight_layout()
plt.savefig('performance_analysis.png', dpi=300, bbox_inches='tight')
print("图表已保存到: performance_analysis.png")
plt.show()

print("\n分析完成！请查看生成的表格和图表文件。")
