"""
优化版多因子策略 - 5因子组合
基于量化经验设计的稳健策略

因子组合：
- Momentum (30%): 20日动量
- Reversal (15%): 5日反转
- EP (25%): 估值因子（价格倒数）
- BP (15%): 市净率代理
- Volume (15%): 成交量异常
"""

from datetime import datetime
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import sys

# 添加strategy目录到路径
sys.path.insert(0, os.path.dirname(__file__))
from data_loader import JYDBDataLoader


class OptimizedFactorCalculator:
    """优化的因子计算器"""
    
    def __init__(self, data_loader):
        self.loader = data_loader
    
    def calculate_all_factors_vectorized(self, start_date, end_date):
        """向量化批量计算所有因子"""
        print("\n" + "=" * 80)
        print("📊 批量计算优化因子组合")
        print("=" * 80)
        
        # 获取数据
        lookback_days = 250
        trading_days = self.loader.get_trading_days(start_date, end_date)
        
        if len(trading_days) < lookback_days:
            actual_start = self.loader.trading_days[0]
        else:
            start_idx = self.loader.trading_days.index(trading_days[0])
            actual_start = self.loader.trading_days[max(0, start_idx - lookback_days)]
        
        print(f"  获取数据: {actual_start.date()} 至 {end_date.date()}")
        df = self.loader.get_price_data(actual_start, end_date).copy()
        print(f"  原始数据: {len(df):,} 条记录")
        
        # 按股票和日期排序
        df = df.sort_values(['SecuCode', 'TradingDay'])
        
        print("\n计算5个核心因子...")
        
        # 1. 动量因子（20日） - 权重30%
        print("  [1/5] 动量因子 (20日) - 权重30%")
        df['momentum_20d'] = df.groupby('SecuCode')['ClosePrice'].pct_change(periods=20) * 100
        
        # 2. 短期反转（5日） - 权重15%
        print("  [2/5] 反转因子 (5日) - 权重15%")
        df['reversal_5d'] = -df.groupby('SecuCode')['ClosePrice'].pct_change(periods=5) * 100
        
        # 3. EP估值因子 - 权重25%
        print("  [3/5] EP估值因子 - 权重25%")
        df['ep_ratio'] = 1 / (df['ClosePrice'] + 1e-10) * 1000  # 放大便于观察
        
        # 4. BP市净率代理 - 权重15%
        print("  [4/5] BP市净率代理 - 权重15%")
        df['price_ma_250'] = df.groupby('SecuCode')['ClosePrice'].transform(
            lambda x: x.rolling(250, min_periods=125).mean()
        )
        df['bp_ratio'] = df['price_ma_250'] / (df['ClosePrice'] + 1e-10)
        
        # 5. 成交量异常 - 权重15%
        print("  [5/5] 成交量异常因子 - 权重15%")
        df['vol_ma_20'] = df.groupby('SecuCode')['TurnoverVolume'].transform(
            lambda x: x.rolling(20, min_periods=10).mean()
        )
        df['volume_anomaly'] = df['TurnoverVolume'] / (df['vol_ma_20'] + 1e-10)
        
        # 只保留需要的列和目标日期范围
        factor_cols = ['SecuCode', 'TradingDay', 'momentum_20d', 'reversal_5d', 
                      'ep_ratio', 'bp_ratio', 'volume_anomaly']
        
        df = df[factor_cols]
        df = df[df['TradingDay'] >= start_date].copy()
        
        print(f"\n✅ 因子计算完成: {len(df):,} 条记录")
        print(f"  日期范围: {df['TradingDay'].min().date()} 至 {df['TradingDay'].max().date()}")
        print(f"  股票数量: {df['SecuCode'].nunique()}")
        
        return df
    
    def process_and_combine_factors(self, factor_df):
        """批量处理和合成因子"""
        print("\n" + "=" * 80)
        print("⚙️  批量处理和合成因子")
        print("=" * 80)
        
        # 因子权重（最优配置）
        weights = {
            'momentum_20d': 0.30,    # 动量 - 最重要
            'reversal_5d': 0.15,     # 反转 - 互补
            'ep_ratio': 0.25,        # EP估值 - 价值核心
            'bp_ratio': 0.15,        # BP市净率 - 补充
            'volume_anomaly': 0.15   # 成交量 - 质量
        }
        
        factor_cols = list(weights.keys())
        
        print(f"  因子权重配置:")
        for factor, weight in weights.items():
            print(f"    - {factor}: {weight:.0%}")
        
        # 按日期分组处理
        print("\n  处理进度:")
        
        def process_group(group):
            """对单个日期的数据进行处理"""
            for col in factor_cols:
                # 去极值 (MAD)
                median = group[col].median()
                mad = (group[col] - median).abs().median()
                if mad > 0:
                    upper = median + 3 * mad
                    lower = median - 3 * mad
                    group[col] = group[col].clip(lower, upper)
                
                # 标准化
                mean = group[col].mean()
                std = group[col].std()
                if std > 0:
                    group[col] = (group[col] - mean) / std
            
            return group
        
        # 使用tqdm显示进度
        tqdm.pandas(desc="  去极值+标准化")
        processed_df = factor_df.groupby('TradingDay', group_keys=False).progress_apply(process_group)
        
        # 合成因子
        print("\n  合成因子...")
        processed_df['combined_factor'] = 0
        for col in factor_cols:
            processed_df['combined_factor'] += processed_df[col].fillna(0) * weights[col]
        
        print(f"✅ 因子处理完成")
        
        return processed_df[['SecuCode', 'TradingDay', 'combined_factor']].dropna()
    
    def generate_irs_files(self, combined_factors, top_n=50, output_dir=None):
        """生成IRS因子文件"""
        if output_dir is None:
            output_dir = r'd:\谷歌反重力\股票量化\irs_factors_optimized'
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "=" * 80)
        print("📁 批量生成IRS因子文件")
        print("=" * 80)
        print(f"  输出目录: {output_dir}")
        print(f"  每日选股: Top {top_n}")
        
        # 按日期分组
        grouped = combined_factors.groupby('TradingDay')
        total_dates = len(grouped)
        
        print(f"  总天数: {total_dates}")
        print("\n  生成进度:")
        
        generated_files = []
        
        for date, group in tqdm(grouped, desc="  生成文件"):
            if len(group) < top_n:
                continue
            
            # 选择top N
            top_stocks = group.nlargest(top_n, 'combined_factor')
            
            # 等权分配
            top_stocks['weight'] = 1.0 / top_n
            
            # 提取股票代码
            top_stocks['stock_code'] = top_stocks['SecuCode'].astype(str).str.extract(r'(\d+)')[0]
            
            # 生成文件名
            date_str = date.strftime('%Y%m%d')
            output_file = os.path.join(output_dir, f'{date_str}.csv')
            
            # 保存文件（无header）
            top_stocks[['stock_code', 'weight']].to_csv(
                output_file,
                index=False,
                header=False
            )
            
            generated_files.append(output_file)
        
        print(f"\n✅ 文件生成完成: {len(generated_files)} 个")
        
        return generated_files, output_dir


def main():
    START_DATE = datetime(2021, 2, 1)
    END_DATE = datetime(2024, 12, 31)
    TOP_N = 50
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 25 + "优化版多因子策略生成系统" + " " * 26 + "█")
    print("█" + " " * 20 + "5因子组合 | JYDB数据 | IRS回测" + " " * 21 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    try:
        # 1. 加载数据
        print("\n【第1步】加载JYDB数据")
        loader = JYDBDataLoader()
        
        # 2. 初始化因子计算器
        print("\n【第2步】初始化优化因子计算器")
        calculator = OptimizedFactorCalculator(loader)
        
        # 3. 批量计算因子
        print("\n【第3步】批量计算5个核心因子")
        factor_df = calculator.calculate_all_factors_vectorized(START_DATE, END_DATE)
        
        # 4. 处理和合成
        print("\n【第4步】处理和合成因子")
        combined_factors = calculator.process_and_combine_factors(factor_df)
        
        # 5. 生成IRS文件
        print("\n【第5步】生成IRS因子文件")
        files, output_dir = calculator.generate_irs_files(combined_factors, top_n=TOP_N)
        
        # 完成
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + " " * 30 + "✅ 全部完成！" + " " * 34 + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        
        print(f"\n📊 策略概要:")
        print(f"   - 因子数量: 5个（动量、反转、EP、BP、成交量）")
        print(f"   - 权重配置: 30% + 15% + 25% + 15% + 15%")
        print(f"   - 生成文件: {len(files)} 个")
        print(f"   - 保存位置: {output_dir}")
        print(f"\n🎯 下一步: 在IRS平台回测")
        print(f"   - 访问: http://localhost:34326")
        print(f"   - 因子路径: {output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
