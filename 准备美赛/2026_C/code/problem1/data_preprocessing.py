"""
DWTS 数据预处理模块
处理题目中提到的所有数据特殊情况：
1. 评委分数平均（多个舞蹈）
2. 额外积分分配
3. 团队舞蹈平均分
4. N/A值处理
5. 被淘汰选手0分处理
6. 评委数量变化
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


class DWTSDataPreprocessor:
    """
    DWTS数据预处理器
    """
    
    def __init__(self, filepath):
        """
        Parameters:
        -----------
        filepath : str
            CSV数据文件路径
        """
        self.filepath = filepath
        self.raw_df = None
        self.processed_df = None
        
    def load_raw_data(self):
        """加载原始数据（支持 CSV 或 Excel）"""
        print("加载原始数据...")
        filepath_lower = self.filepath.lower()
        if filepath_lower.endswith('.xlsx') or filepath_lower.endswith('.xls'):
            self.raw_df = pd.read_excel(self.filepath, sheet_name=0, engine='openpyxl')
            print(f"  从 Excel 加载")
        else:
            self.raw_df = pd.read_csv(self.filepath, encoding='utf-8-sig')
            print(f"  从 CSV 加载")
        print(f"  原始数据: {len(self.raw_df)} 行, {len(self.raw_df.columns)} 列")
        print(f"  赛季范围: {self.raw_df['season'].min()} - {self.raw_df['season'].max()}")
        print(f"  选手数量: {self.raw_df['celebrity_name'].nunique()}")
        return self.raw_df
    
    def inspect_data_structure(self):
        """检查数据结构"""
        if self.raw_df is None:
            self.load_raw_data()
        
        print("\n数据结构检查:")
        print("="*60)
        
        # 1. 列名检查
        print("\n[1] 列名列表:")
        for i, col in enumerate(self.raw_df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        # 2. 周数和评委数量
        judge_cols = [col for col in self.raw_df.columns 
                     if 'week' in col.lower() and 'judge' in col.lower() and 'score' in col.lower()]
        
        # 提取周数
        weeks = set()
        for col in judge_cols:
            try:
                # 从列名中提取周数，如 'week1_judge1_score' -> 1
                parts = col.split('_')
                for part in parts:
                    if part.startswith('week'):
                        week_num = int(part.replace('week', ''))
                        weeks.add(week_num)
                        break
            except:
                pass
        
        max_week = max(weeks) if weeks else 0
        print(f"\n[2] 周数范围: 1 - {max_week}")
        
        # 提取评委数量
        judges_per_week = {}
        for week in sorted(weeks):
            week_judges = [col for col in judge_cols if f'week{week}_' in col]
            judges_per_week[week] = len(week_judges)
        
        print(f"\n[3] 每周评委数量:")
        for week in sorted(list(judges_per_week.keys())[:10]):  # 显示前10周
            print(f"  Week {week}: {judges_per_week[week]} 位评委")
        
        # 3. N/A值统计
        print(f"\n[4] N/A值统计:")
        na_stats = {}
        for col in judge_cols[:20]:  # 检查前20个评委分数列
            na_count = self.raw_df[col].isna().sum()
            if na_count > 0:
                na_stats[col] = na_count
        
        if na_stats:
            print(f"  含N/A的列数: {len(na_stats)}")
            for col, count in list(na_stats.items())[:5]:
                print(f"    {col}: {count} 个N/A")
        else:
            print("  未发现N/A值（可能用其他方式表示）")
        
        # 4. 被淘汰选手0分检查
        print(f"\n[5] 0分记录统计:")
        zero_counts = 0
        for col in judge_cols[:20]:
            zero_counts += (self.raw_df[col] == 0).sum()
        print(f"  前20列中0分数量: {zero_counts}")
        
        # 5. Results字段分析
        print(f"\n[6] Results字段分析:")
        results_samples = self.raw_df['results'].value_counts().head(10)
        print("  前10种结果类型:")
        for result, count in results_samples.items():
            print(f"    '{result}': {count} 次")
        
        return {
            'n_rows': len(self.raw_df),
            'n_cols': len(self.raw_df.columns),
            'max_week': max_week,
            'judge_cols': judge_cols,
            'judges_per_week': judges_per_week
        }
    
    def parse_results_field(self, df):
        """
        解析results字段，提取淘汰周次和最终名次
        
        Parameters:
        -----------
        df : pd.DataFrame
            数据框
            
        Returns:
        --------
        df : pd.DataFrame
            添加了 elimination_week 和 verified_placement 列
        """
        print("\n解析results字段...")
        
        def extract_elimination_week(result_str):
            """从results提取淘汰周次"""
            if pd.isna(result_str):
                return None
            
            result_str = str(result_str).lower().strip()
            
            # 情况1: "Eliminated Week X"
            if 'eliminated week' in result_str:
                try:
                    # 提取数字
                    import re
                    match = re.search(r'week\s*(\d+)', result_str)
                    if match:
                        return int(match.group(1))
                except:
                    pass
            
            # 情况2: "1st Place", "2nd Place" 等（进入决赛，未在周赛被淘汰）
            if 'place' in result_str:
                return None
            
            return None
        
        df['elimination_week'] = df['results'].apply(extract_elimination_week)
        
        eliminated_count = df['elimination_week'].notna().sum()
        finalist_count = df['elimination_week'].isna().sum()
        
        print(f"  周赛淘汰: {eliminated_count} 人")
        print(f"  进入决赛: {finalist_count} 人")
        
        return df
    
    def extract_judge_scores(self, df):
        """
        提取并整理评委分数
        处理:
        - N/A值
        - 0分（被淘汰选手）
        - 小数分数（多舞蹈平均）
        
        Parameters:
        -----------
        df : pd.DataFrame
            数据框
            
        Returns:
        --------
        df : pd.DataFrame
            添加了每周总分和标准化列
        """
        print("\n提取评委分数...")
        
        # 找出所有评委分数列
        judge_cols = [col for col in df.columns 
                     if 'week' in col.lower() and 'judge' in col.lower() and 'score' in col.lower()]
        
        # 提取周数
        weeks = set()
        for col in judge_cols:
            try:
                parts = col.split('_')
                for part in parts:
                    if part.startswith('week'):
                        week_num = int(part.replace('week', ''))
                        weeks.add(week_num)
                        break
            except:
                pass
        
        max_week = max(weeks) if weeks else 11
        
        # 对每一周，计算总分和评委人数
        for week in range(1, max_week + 1):
            week_judge_cols = [col for col in judge_cols if f'week{week}_' in col]
            
            if not week_judge_cols:
                continue
            
            # 计算该周总分（处理N/A和0）
            def compute_week_total(row):
                scores = []
                for col in week_judge_cols:
                    val = row[col]
                    # 处理N/A
                    if pd.isna(val) or val == 'N/A' or val == '':
                        continue
                    # 转换为浮点数
                    try:
                        score = float(val)
                        # 0分表示已被淘汰，仍然记录
                        scores.append(score)
                    except:
                        continue
                
                return sum(scores) if scores else np.nan
            
            df[f'week{week}_total_score'] = df.apply(compute_week_total, axis=1)
            
            # 计算该周有效评委人数
            def count_judges(row):
                count = 0
                for col in week_judge_cols:
                    val = row[col]
                    if pd.notna(val) and val != 'N/A' and val != '':
                        try:
                            float(val)
                            count += 1
                        except:
                            pass
                return count if count > 0 else np.nan
            
            df[f'week{week}_judge_count'] = df.apply(count_judges, axis=1)
            
            # 计算平均分（用于标准化比较）
            df[f'week{week}_avg_score'] = df[f'week{week}_total_score'] / df[f'week{week}_judge_count']
        
        # 统计
        total_score_cols = [col for col in df.columns if 'total_score' in col]
        print(f"  生成了 {len(total_score_cols)} 周的总分列")
        
        return df
    
    def handle_zero_scores(self, df):
        """
        处理被淘汰选手的0分
        标记哪些0分是因为被淘汰，哪些是真实得分
        
        Parameters:
        -----------
        df : pd.DataFrame
            数据框
            
        Returns:
        --------
        df : pd.DataFrame
            添加了 is_eliminated 标记列
        """
        print("\n处理0分记录...")
        
        # 获取所有周的总分列
        score_cols = [col for col in df.columns if 'total_score' in col and 'week' in col]
        
        zero_count = 0
        
        for idx, row in df.iterrows():
            elim_week = row['elimination_week']
            
            if pd.notna(elim_week):
                # 从淘汰周的下一周开始，所有分数都应该是0或N/A
                elim_week = int(elim_week)
                
                for col in score_cols:
                    # 提取周数
                    try:
                        week_num = int(col.split('week')[1].split('_')[0])
                        
                        # 如果是淘汰后的周次
                        if week_num > elim_week:
                            # 标记为"淘汰后的0分"
                            if row[col] == 0:
                                zero_count += 1
                    except:
                        pass
        
        print(f"  识别出 {zero_count} 个淘汰后的0分")
        
        return df
    
    def identify_active_contestants(self, df):
        """
        为每一周标识哪些选手仍在比赛中
        
        Parameters:
        -----------
        df : pd.DataFrame
            数据框
            
        Returns:
        --------
        df : pd.DataFrame
            添加了每周的 weekX_active 列
        """
        print("\n标识每周活跃选手...")
        
        score_cols = [col for col in df.columns if 'total_score' in col and 'week' in col]
        weeks = []
        
        for col in score_cols:
            try:
                week_num = int(col.split('week')[1].split('_')[0])
                weeks.append(week_num)
            except:
                pass
        
        for week in sorted(set(weeks)):
            score_col = f'week{week}_total_score'
            
            # 选手在该周活跃的条件：
            # 1. 有评委分数
            # 2. 分数不为0（或者该周就是淘汰周）
            # 3. 还未被淘汰
            
            def is_active(row):
                # 检查是否已被淘汰
                elim_week = row['elimination_week']
                if pd.notna(elim_week) and week > elim_week:
                    return False
                
                # 检查是否有分数
                score = row[score_col]
                if pd.isna(score):
                    return False
                
                # 0分需要特殊处理：如果是该周被淘汰，仍算活跃
                if score == 0:
                    if pd.notna(elim_week) and week == elim_week:
                        return True  # 该周被淘汰但仍参赛
                    else:
                        return False  # 已被淘汰
                
                return True
            
            df[f'week{week}_active'] = df.apply(is_active, axis=1)
        
        return df
    
    def compute_statistics(self, df):
        """
        计算数据集统计信息
        
        Parameters:
        -----------
        df : pd.DataFrame
            数据框
            
        Returns:
        --------
        stats : dict
            统计信息
        """
        print("\n计算统计信息...")
        
        stats = {
            'n_total_records': len(df),
            'n_seasons': df['season'].nunique(),
            'n_celebrities': df['celebrity_name'].nunique(),
            'n_pro_dancers': df['ballroom_partner'].nunique(),
            'seasons': {}
        }
        
        # 每个赛季的统计
        for season in sorted(df['season'].unique()):
            season_df = df[df['season'] == season]
            
            # 找出该赛季的最大周数
            active_cols = [col for col in season_df.columns if 'active' in col]
            max_week = 0
            for col in active_cols:
                try:
                    week_num = int(col.split('week')[1].split('_')[0])
                    if season_df[col].any():
                        max_week = max(max_week, week_num)
                except:
                    pass
            
            stats['seasons'][season] = {
                'n_celebrities': len(season_df),
                'max_week': max_week,
                'industries': season_df['celebrity_industry'].value_counts().to_dict()
            }
        
        print(f"  总赛季数: {stats['n_seasons']}")
        print(f"  总选手数: {stats['n_celebrities']}")
        print(f"  总舞者数: {stats['n_pro_dancers']}")
        
        return stats
    
    def validate_data(self, df):
        """
        数据验证：检查预处理后的数据质量
        
        Parameters:
        -----------
        df : pd.DataFrame
            数据框
            
        Returns:
        --------
        validation_report : dict
            验证报告
        """
        print("\n数据验证...")
        
        issues = []
        
        # 1. 检查placement与results的一致性
        if 'placement' in df.columns:
            # placement应该是正整数
            invalid_placement = df[df['placement'] < 1]
            if len(invalid_placement) > 0:
                issues.append(f"发现 {len(invalid_placement)} 个无效placement值")
        
        # 2. 检查每周分数的合理性
        score_cols = [col for col in df.columns if 'total_score' in col]
        for col in score_cols[:5]:  # 检查前5周
            # 分数应该在合理范围内
            valid_scores = df[df[col].notna() & (df[col] > 0)][col]
            if len(valid_scores) > 0:
                min_score = valid_scores.min()
                max_score = valid_scores.max()
                
                # 假设最多4个评委，每个最高10分
                if max_score > 40:
                    issues.append(f"{col}: 最大分数 {max_score} 超过预期上限40")
                if min_score < 0:
                    issues.append(f"{col}: 发现负分 {min_score}")
        
        # 3. 检查每个赛季的选手数量
        for season in df['season'].unique():
            season_df = df[df['season'] == season]
            n_celebrities = len(season_df)
            
            if n_celebrities < 5:
                issues.append(f"Season {season}: 选手数量过少 ({n_celebrities})")
            elif n_celebrities > 30:
                issues.append(f"Season {season}: 选手数量过多 ({n_celebrities})")
        
        if issues:
            print("  发现以下问题:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✓ 数据验证通过!")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues
        }
    
    def run_full_preprocessing(self):
        """
        运行完整的预处理流程
        
        Returns:
        --------
        processed_df : pd.DataFrame
            预处理后的数据
        stats : dict
            统计信息
        """
        print("="*70)
        print("DWTS 数据预处理")
        print("="*70)
        
        # 1. 加载原始数据
        df = self.load_raw_data()
        
        # 2. 检查数据结构
        structure_info = self.inspect_data_structure()
        
        # 3. 解析results字段
        df = self.parse_results_field(df)
        
        # 4. 提取评委分数
        df = self.extract_judge_scores(df)
        
        # 5. 处理0分
        df = self.handle_zero_scores(df)
        
        # 6. 标识活跃选手
        df = self.identify_active_contestants(df)
        
        # 7. 计算统计信息
        stats = self.compute_statistics(df)
        
        # 8. 数据验证
        validation = self.validate_data(df)
        
        self.processed_df = df
        
        # 9. 自动保存为 Excel
        excel_path = self.save_processed_data()
        
        print("\n" + "="*70)
        print("预处理完成!")
        print("="*70)
        if excel_path:
            print(f"后续分析请使用处理后的 Excel 文件: {excel_path}")
        
        return df, stats, validation
    
    def save_processed_data(self, output_path=None, also_save_csv=False):
        """
        保存预处理后的数据为 Excel 文档（主输出），可选同时保存 CSV。
        
        Parameters:
        -----------
        output_path : str
            输出路径，默认与输入同目录，文件名为 xxx_processed.xlsx
        also_save_csv : bool
            是否同时保存一份 CSV 备份
        """
        if self.processed_df is None:
            print("错误: 请先运行预处理")
            return None
        
        import os
        if output_path is None:
            base = self.filepath
            for ext in ['.xlsx', '.xls', '.csv']:
                if base.lower().endswith(ext):
                    base = base[:-len(ext)]
                    break
            output_path = base + '_processed.xlsx'
        
        # 确保扩展名为 .xlsx
        if not output_path.lower().endswith('.xlsx'):
            output_path = output_path.rstrip('.xls') + '.xlsx'
        
        # 生成数据说明表（第二个 Sheet）
        n_records = len(self.processed_df)
        n_seasons = self.processed_df['season'].nunique()
        n_celebrities = self.processed_df['celebrity_name'].nunique()
        n_dancers = self.processed_df['ballroom_partner'].nunique()
        desc_data = [
            ['项目', '数值'],
            ['总记录数', n_records],
            ['赛季数', n_seasons],
            ['选手数', n_celebrities],
            ['职业舞者数', n_dancers],
            ['', ''],
            ['字段说明', ''],
            ['elimination_week', '该选手被淘汰的周次，空表示进入决赛'],
            ['weekX_total_score', '第X周评委总分'],
            ['weekX_judge_count', '第X周评委人数'],
            ['weekX_avg_score', '第X周平均分'],
            ['weekX_active', '第X周是否仍在比赛中'],
        ]
        desc_df = pd.DataFrame(desc_data[1:], columns=desc_data[0])
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            self.processed_df.to_excel(writer, sheet_name='数据', index=False)
            desc_df.to_excel(writer, sheet_name='数据说明', index=False)
        
        print(f"\n预处理后的数据已保存为 Excel: {output_path}")
        print(f"  - Sheet「数据」: 预处理后的完整数据")
        print(f"  - Sheet「数据说明」: 字段说明与统计信息")
        
        if also_save_csv:
            csv_path = output_path.replace('.xlsx', '.csv')
            self.processed_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  - CSV 备份: {csv_path}")
        
        return output_path


# =============================================================================
# 工具函数：快速访问预处理后的数据
# =============================================================================

# 默认预处理输出文件名（供后续代码使用）
DEFAULT_PROCESSED_EXCEL = '2026_MCM_Problem_C_Data_processed.xlsx'


def quick_preprocess(filepath='2026_MCM_Problem_C_Data.csv', save_excel=True):
    """
    快速预处理函数：从原始 CSV 运行完整预处理，并输出 Excel。
    
    Parameters:
    -----------
    filepath : str
        原始数据文件路径（CSV）
    save_excel : bool
        是否保存为 Excel（默认 True）
        
    Returns:
    --------
    df : pd.DataFrame
        预处理后的数据
    stats : dict
        统计信息
    excel_path : str or None
        保存的 Excel 路径（若 save_excel=True）
    """
    preprocessor = DWTSDataPreprocessor(filepath)
    df, stats, validation = preprocessor.run_full_preprocessing()
    excel_path = preprocessor.save_processed_data() if save_excel else None
    return df, stats, excel_path


def load_processed_excel(excel_path):
    """
    从预处理后的 Excel 文件加载数据（供后续分析使用）。
    
    Parameters:
    -----------
    excel_path : str
        预处理输出的 Excel 文件路径（.xlsx）
        
    Returns:
    --------
    df : pd.DataFrame
        预处理后的数据（与「数据」Sheet 一致）
    """
    df = pd.read_excel(excel_path, sheet_name='数据', engine='openpyxl')
    # 确保关键列为正确类型
    if 'season' in df.columns:
        df['season'] = pd.to_numeric(df['season'], errors='coerce').fillna(0).astype(int)
    if 'placement' in df.columns:
        df['placement'] = pd.to_numeric(df['placement'], errors='coerce').fillna(0).astype(int)
    if 'elimination_week' in df.columns:
        def to_elim_week(x):
            if pd.isna(x):
                return None
            try:
                v = float(x)
                return int(v) if v == int(v) else None
            except (ValueError, TypeError):
                return None
        df['elimination_week'] = df['elimination_week'].apply(to_elim_week)
    return df


def get_week_data(df, season, week):
    """
    获取特定赛季特定周的数据
    
    Parameters:
    -----------
    df : pd.DataFrame
        预处理后的数据
    season : int
        赛季
    week : int
        周次
        
    Returns:
    --------
    week_df : pd.DataFrame
        该周的选手数据
    """
    season_df = df[df['season'] == season].copy()
    
    # 过滤活跃选手
    active_col = f'week{week}_active'
    if active_col not in season_df.columns:
        print(f"警告: 第{week}周数据不存在")
        return pd.DataFrame()
    
    week_df = season_df[season_df[active_col] == True].copy()
    
    # 添加该周的分数信息
    score_col = f'week{week}_total_score'
    if score_col in week_df.columns:
        week_df['current_score'] = week_df[score_col]
    
    return week_df


# =============================================================================
# 使用示例
# =============================================================================

def main():
    """主函数：运行预处理示例"""
    import os
    
    # 数据文件路径
    data_path = '2026_MCM_Problem_C_Data.csv'
    
    if not os.path.exists(data_path):
        print(f"错误: 找不到数据文件 {data_path}")
        print("请确保数据文件在当前目录下")
        return None
    
    # 创建预处理器
    preprocessor = DWTSDataPreprocessor(data_path)
    
    # 运行完整预处理（内部会自动保存 Excel）
    df, stats, validation = preprocessor.run_full_preprocessing()
    
    # 若未自动保存，可手动保存
    if preprocessor.processed_df is not None and not os.path.exists(
        data_path.replace('.csv', '_processed.xlsx')
    ):
        preprocessor.save_processed_data()
    
    # 示例：查看某一周的数据
    print("\n" + "="*70)
    print("示例：Season 2, Week 4")
    print("="*70)
    
    week_data = get_week_data(df, season=2, week=4)
    if len(week_data) > 0:
        print(f"\n活跃选手数: {len(week_data)}")
        print("\n选手信息:")
        cols_to_show = ['celebrity_name', 'week4_total_score', 'week4_judge_count', 
                       'week4_avg_score', 'elimination_week']
        if all(col in week_data.columns for col in cols_to_show):
            print(week_data[cols_to_show].to_string(index=False))
    
    return df, stats


if __name__ == "__main__":
    df, stats = main()
