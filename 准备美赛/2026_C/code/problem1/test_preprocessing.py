"""
测试数据预处理模块
验证预处理的正确性
"""

import pandas as pd
import numpy as np
from data_preprocessing import DWTSDataPreprocessor, quick_preprocess, get_week_data


def test_basic_loading():
    """测试1: 基础数据加载"""
    print("\n" + "="*70)
    print("测试1: 基础数据加载")
    print("="*70)
    
    try:
        preprocessor = DWTSDataPreprocessor('2026_MCM_Problem_C_Data.csv')
        df = preprocessor.load_raw_data()
        
        print(f"✓ 成功加载数据")
        print(f"  数据形状: {df.shape}")
        print(f"  列名数量: {len(df.columns)}")
        
        return True
    except Exception as e:
        print(f"✗ 加载失败: {e}")
        return False


def test_data_structure():
    """测试2: 数据结构检查"""
    print("\n" + "="*70)
    print("测试2: 数据结构检查")
    print("="*70)
    
    try:
        preprocessor = DWTSDataPreprocessor('2026_MCM_Problem_C_Data.csv')
        preprocessor.load_raw_data()
        info = preprocessor.inspect_data_structure()
        
        print(f"✓ 数据结构检查完成")
        print(f"  最大周数: {info['max_week']}")
        print(f"  评委列数: {len(info['judge_cols'])}")
        
        return True
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False


def test_full_preprocessing():
    """测试3: 完整预处理流程"""
    print("\n" + "="*70)
    print("测试3: 完整预处理流程")
    print("="*70)
    
    try:
        df, stats, _ = quick_preprocess('2026_MCM_Problem_C_Data.csv')
        
        print(f"✓ 预处理完成")
        print(f"  总记录数: {stats['n_total_records']}")
        print(f"  赛季数: {stats['n_seasons']}")
        print(f"  选手数: {stats['n_celebrities']}")
        
        # 检查是否生成了必要的列
        required_cols = ['elimination_week', 'week1_total_score', 'week1_active']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"✗ 缺少列: {missing_cols}")
            return False
        else:
            print(f"✓ 所有必要列已生成")
        
        return True
    except Exception as e:
        print(f"✗ 预处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_week_data_extraction():
    """测试4: 周数据提取"""
    print("\n" + "="*70)
    print("测试4: 周数据提取")
    print("="*70)
    
    try:
        df, _, _ = quick_preprocess('2026_MCM_Problem_C_Data.csv')
        
        # 测试几个赛季的周数据
        test_cases = [
            (1, 1),  # Season 1, Week 1
            (2, 4),  # Season 2, Week 4
            (3, 5),  # Season 3, Week 5
        ]
        
        for season, week in test_cases:
            week_df = get_week_data(df, season, week)
            if len(week_df) > 0:
                print(f"✓ Season {season}, Week {week}: {len(week_df)} 位活跃选手")
            else:
                print(f"⚠ Season {season}, Week {week}: 无数据")
        
        return True
    except Exception as e:
        print(f"✗ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_cases():
    """测试5: 特定案例验证"""
    print("\n" + "="*70)
    print("测试5: 特定案例验证（题目示例）")
    print("="*70)
    
    try:
        df, _, _ = quick_preprocess('2026_MCM_Problem_C_Data.csv')
        
        # 测试题目中提到的案例
        # 案例1: Season 2, Week 4 (Rachel Hunter被淘汰)
        print("\n案例1: Season 2, Week 4")
        week_df = get_week_data(df, 2, 4)
        
        if len(week_df) > 0:
            print(f"  选手数: {len(week_df)}")
            print(f"  选手名单:")
            for idx, row in week_df.iterrows():
                name = row['celebrity_name']
                score = row.get('week4_total_score', 'N/A')
                elim = row.get('elimination_week', 'N/A')
                print(f"    - {name}: 分数={score}, 淘汰周={elim}")
            
            # 检查Rachel Hunter是否在该周被淘汰
            rachel = week_df[week_df['celebrity_name'].str.contains('Rachel', case=False, na=False)]
            if len(rachel) > 0:
                rachel_elim = rachel.iloc[0]['elimination_week']
                if rachel_elim == 4:
                    print(f"  ✓ 确认Rachel Hunter在Week 4被淘汰")
                else:
                    print(f"  ⚠ Rachel Hunter淘汰周为{rachel_elim}，不是4")
        
        # 案例2: 争议选手 Jerry Rice (Season 2)
        print("\n案例2: Jerry Rice (Season 2)")
        jerry = df[(df['season'] == 2) & 
                   (df['celebrity_name'].str.contains('Jerry', case=False, na=False))]
        
        if len(jerry) > 0:
            jerry_row = jerry.iloc[0]
            print(f"  最终名次: {jerry_row['placement']}")
            print(f"  淘汰周: {jerry_row['elimination_week']}")
            print(f"  行业: {jerry_row['celebrity_industry']}")
            
            # 检查几周的分数
            for week in [1, 2, 3, 4, 5]:
                score_col = f'week{week}_total_score'
                if score_col in jerry_row.index:
                    score = jerry_row[score_col]
                    if pd.notna(score):
                        print(f"  Week {week} 分数: {score}")
        
        return True
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_consistency():
    """测试6: 数据一致性检查"""
    print("\n" + "="*70)
    print("测试6: 数据一致性检查")
    print("="*70)
    
    try:
        df, _, _ = quick_preprocess('2026_MCM_Problem_C_Data.csv')
        
        issues = []
        
        # 检查1: 每个赛季的选手数量
        for season in df['season'].unique()[:5]:  # 检查前5个赛季
            season_df = df[df['season'] == season]
            n_contestants = len(season_df)
            
            if n_contestants < 5:
                issues.append(f"Season {season}: 选手数过少 ({n_contestants})")
            elif n_contestants > 30:
                issues.append(f"Season {season}: 选手数过多 ({n_contestants})")
            else:
                print(f"✓ Season {season}: {n_contestants} 位选手")
        
        # 检查2: placement字段有效性
        invalid_placement = df[df['placement'] < 1]
        if len(invalid_placement) > 0:
            issues.append(f"发现{len(invalid_placement)}个无效placement")
        else:
            print(f"✓ Placement字段有效")
        
        # 检查3: 评委分数范围
        score_cols = [col for col in df.columns if 'total_score' in col]
        for col in score_cols[:5]:
            valid_scores = df[(df[col].notna()) & (df[col] > 0)][col]
            if len(valid_scores) > 0:
                min_s = valid_scores.min()
                max_s = valid_scores.max()
                
                # 假设最多4位评委，每位最高10分
                if max_s > 50:  # 留一些余量
                    issues.append(f"{col}: 最大分数{max_s}异常")
                elif max_s < 5:
                    issues.append(f"{col}: 最大分数{max_s}过低")
        
        print(f"✓ 分数范围检查完成")
        
        if issues:
            print(f"\n⚠ 发现 {len(issues)} 个潜在问题:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\n✓ 数据一致性检查通过!")
        
        return len(issues) == 0
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("DWTS 数据预处理测试套件")
    print("="*70)
    
    tests = [
        ("基础数据加载", test_basic_loading),
        ("数据结构检查", test_data_structure),
        ("完整预处理流程", test_full_preprocessing),
        ("周数据提取", test_week_data_extraction),
        ("特定案例验证", test_specific_cases),
        ("数据一致性检查", test_data_consistency),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 发生异常: {e}")
            results.append((test_name, False))
    
    # 汇总
    print("\n" + "="*70)
    print("测试汇总")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！数据预处理可以正常使用。")
    else:
        print(f"\n⚠ 有 {total - passed} 个测试失败，请检查。")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n" + "="*70)
        print("后续步骤:")
        print("="*70)
        print("1. 数据预处理已验证，可以进行问题一的分析")
        print("2. 运行主分析脚本:")
        print("   python run_analysis.py --data 2026_MCM_Problem_C_Data.csv")
        print("3. 或使用交互式Python:")
        print("   from data_preprocessing import quick_preprocess, load_processed_excel")
        print("   df, stats, excel_path = quick_preprocess('2026_MCM_Problem_C_Data.csv')")
        print("   # 后续分析使用: df = load_processed_excel('2026_MCM_Problem_C_Data_processed.xlsx')")
