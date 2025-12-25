"""
优化版因子生成器 - 批量向量化计算
一次性计算所有日期的因子，而不是逐日循环
"""

from datetime import datetime
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import sys

sys.path.insert(0, os.path.dirname(__file__))
from data_loader import JYDBDataLoader

class FastFactorGenerator:
    """快速批量因子生成器"""
    
    def __init__(self, data_loader):
        self.loader = data_loader
        print("✅ 快速因子生成器初始化完成")
    
    def calculate_all_factors_vectorized(self, start_date, end_date):
        """
        向量化批量计算所有因子
        一次性处理所有股票所有日期
        """
        print("\n" + "=" * 80)
        print("📊 批量计算因子（向量化）")
        print("=" * 80)
        
        # 获取数据（增加一些前置天数用于计算）
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
        
        print("\n计算因子...")
        
        # 1. 动量因子（20日收益率）
        print("  [1/6] 动量因子...")
        df['momentum'] = df.groupby('SecuCode')['ClosePrice'].pct_change(periods=20)
        
        # 2. 短期反转（5日反向收益）
        print("  [2/6] 反转因子...")
        df['reversal'] = -df.groupby('SecuCode')['ClosePrice'].pct_change(periods=5)
        
        # 3. 成交量异常
        print("  [3/6] 成交量因子...")
        df['vol_ma_20'] = df.groupby('SecuCode')['TurnoverVolume'].transform(
            lambda x: x.rolling(20, min_periods=10).mean()
        )
        df['volume_spike'] = df['TurnoverVolume'] / (df['vol_ma_20'] + 1e-10)
        
        # 4. RSI
        print("  [4/6] RSI因子...")
        def calc_rsi(prices, period=14):
            delta = prices.diff()
            gain = delta.where(delta > 0, 0).rolling(period, min_periods=period//2).mean()
            loss = -delta.where(delta < 0, 0).rolling(period, min_periods=period//2).mean()
            rs = gain / (loss + 1e-10)
            return 100 - (100 / (1 + rs))
        
        df['rsi'] = df.groupby('SecuCode')['ClosePrice'].transform(
            lambda x: calc_rsi(x, 14)
        )
        
        # 5. EP代理（价格倒数）
        print("  [5/6] EP因子...")
        df['ep_proxy'] = 1 / (df['ClosePrice'] + 1e-10)
        
        # 6. BP代理（250日均价/当前价）
        print("  [6/6] BP因子...")
        df['price_ma_250'] = df.groupby('SecuCode')['ClosePrice'].transform(
            lambda x: x.rolling(250, min_periods=125).mean()
        )
        df['bp_proxy'] = df['price_ma_250'] / (df['ClosePrice'] + 1e-10)
        
        # 只保留需要的列和目标日期范围
        factor_cols = ['SecuCode', 'TradingDay', 'momentum', 'reversal', 
                      'volume_spike', 'rsi', 'ep_proxy', 'bp_proxy']
        
        df = df[factor_cols]
        df = df[df['TradingDay'] >= start_date].copy()
        
        print(f"\n✅ 因子计算完成: {len(df):,} 条记录")
        print(f"  日期范围: {df['TradingDay'].min().date()} 至 {df['TradingDay'].max().date()}")
        print(f"  股票数量: {df['SecuCode'].nunique()}")
        
        return df
    
    def process_and_combine_factors(self, factor_df, weights=None):
        """
        批量处理和合成因子
        """
        print("\n" + "=" * 80)
        print("⚙️  批量处理因子")
        print("=" * 80)
        
        if weights is None:
            weights = {
                'momentum': 0.20,
                'reversal': 0.15,
                'volume_spike': 0.15,
                'rsi': 0.15,
                'ep_proxy': 0.20,
                'bp_proxy': 0.15
            }
        
        factor_cols = ['momentum', 'reversal', 'volume_spike', 'rsi', 'ep_proxy', 'bp_proxy']
        
        # 按日期分组处理（去极值+标准化）
        print("  处理进度:")
        
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
            processed_df['combined_factor'] += processed_df[col].fillna(0) * weights.get(col, 0)
        
        print(f"✅ 因子处理完成")
        
        return processed_df[['SecuCode', 'TradingDay', 'combined_factor']].dropna()
    
    def generate_daily_files(self, combined_factors, top_n=50, output_dir=None):
        """
        根据合成因子批量生成每日文件
        """
        if output_dir is None:
            output_dir = r'd:\谷歌反重力\股票量化\irs_factors'
        
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
            # 选择top N
            if len(group) < top_n:
                continue
            
            top_stocks = group.nlargest(top_n, 'combined_factor')
            
            # 等权分配
            top_stocks['weight'] = 1.0 / top_n
            
            # 提取股票代码（去掉交易所后缀）
            # SecuCode可能是数字或字符串，统一转为字符串处理
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
        
        return generated_files


def main():
    START_DATE = datetime(2021, 2, 1)
    END_DATE = datetime(2024, 12, 31)
    TOP_N = 50
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 20 + "优化版IRS因子文件生成系统（批量向量化）" + " " * 20 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    try:
        # 1. 加载数据
        print("\n【第1步】加载数据")
        loader = JYDBDataLoader()
        
        # 2. 初始化快速生成器
        print("\n【第2步】初始化快速因子生成器")
        generator = FastFactorGenerator(loader)
        
        # 3. 批量计算所有因子
        print("\n【第3步】批量计算因子（向量化）")
        factor_df = generator.calculate_all_factors_vectorized(START_DATE, END_DATE)
        
        # 4. 批量处理和合成
        print("\n【第4步】批量处理和合成因子")
        combined_factors = generator.process_and_combine_factors(factor_df)
        
        # 5. 批量生成文件
        print("\n【第5步】批量生成文件")
        files = generator.generate_daily_files(combined_factors, top_n=TOP_N)
        
        # 完成
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + " " * 30 + "✅ 全部完成！" + " " * 34 + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        
        print(f"\n📁 生成的因子文件: {len(files)} 个")
        print(f"   保存位置: d:/谷歌反重力/股票量化/irs_factors/")
        print(f"\n🎯 可以在IRS平台回测了: http://localhost:34326")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
