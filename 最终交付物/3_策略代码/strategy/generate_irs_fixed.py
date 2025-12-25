"""
修复版 - 生成IRS格式的因子文件
关键修复：第二列应该是因子分数，而不是权重！
"""

from datetime import datetime
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import sys

sys.path.insert(0, os.path.dirname(__file__))
from data_loader import JYDBDataLoader


class IRSFactorGenerator:
    """IRS格式因子生成器（修复版）"""
    
    def __init__(self, data_loader):
        self.loader = data_loader
    
    def calculate_all_factors_vectorized(self, start_date, end_date):
        """向量化批量计算所有因子"""
        print("\n" + "=" * 80)
        print("📊 批量计算优化因子组合")
        print("=" * 80)
        
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
        
        df = df.sort_values(['SecuCode', 'TradingDay'])
        
        print("\n计算5个核心因子...")
        
        print("  [1/5] 动量因子 (20日) - 权重30%")
        df['momentum_20d'] = df.groupby('SecuCode')['ClosePrice'].pct_change(periods=20) * 100
        
        print("  [2/5] 反转因子 (5日) - 权重15%")
        df['reversal_5d'] = -df.groupby('SecuCode')['ClosePrice'].pct_change(periods=5) * 100
        
        print("  [3/5] EP估值因子 - 权重25%")
        df['ep_ratio'] = 1 / (df['ClosePrice'] + 1e-10) * 1000
        
        print("  [4/5] BP市净率代理 - 权重15%")
        df['price_ma_250'] = df.groupby('SecuCode')['ClosePrice'].transform(
            lambda x: x.rolling(250, min_periods=125).mean()
        )
        df['bp_ratio'] = df['price_ma_250'] / (df['ClosePrice'] + 1e-10)
        
        print("  [5/5] 成交量异常因子 - 权重15%")
        df['vol_ma_20'] = df.groupby('SecuCode')['TurnoverVolume'].transform(
            lambda x: x.rolling(20, min_periods=10).mean()
        )
        df['volume_anomaly'] = df['TurnoverVolume'] / (df['vol_ma_20'] + 1e-10)
        
        factor_cols = ['SecuCode', 'TradingDay', 'momentum_20d', 'reversal_5d', 
                      'ep_ratio', 'bp_ratio', 'volume_anomaly']
        
        df = df[factor_cols]
        df = df[df['TradingDay'] >= start_date].copy()
        
        print(f"\n✅ 因子计算完成: {len(df):,} 条记录")
        
        return df
    
    def process_and_combine_factors(self, factor_df):
        """批量处理和合成因子"""
        print("\n" + "=" * 80)
        print("⚙️  批量处理和合成因子")
        print("=" * 80)
        
        weights = {
            'momentum_20d': 0.30,
            'reversal_5d': 0.15,
            'ep_ratio': 0.25,
            'bp_ratio': 0.15,
            'volume_anomaly': 0.15
        }
        
        factor_cols = list(weights.keys())
        
        print(f"  因子权重配置:")
        for factor, weight in weights.items():
            print(f"    - {factor}: {weight:.0%}")
        
        print("\n  处理进度:")
        
        def process_group(group):
            for col in factor_cols:
                median = group[col].median()
                mad = (group[col] - median).abs().median()
                if mad > 0:
                    upper = median + 3 * mad
                    lower = median - 3 * mad
                    group[col] = group[col].clip(lower, upper)
                
                mean = group[col].mean()
                std = group[col].std()
                if std > 0:
                    group[col] = (group[col] - mean) / std
            
            return group
        
        tqdm.pandas(desc="  去极值+标准化")
        processed_df = factor_df.groupby('TradingDay', group_keys=False).progress_apply(process_group)
        
        print("\n  合成因子...")
        processed_df['combined_factor'] = 0
        for col in factor_cols:
            processed_df['combined_factor'] += processed_df[col].fillna(0) * weights[col]
        
        print(f"✅ 因子处理完成")
        
        return processed_df[['SecuCode', 'TradingDay', 'combined_factor']].dropna()
    
    def generate_irs_files_fixed(self, combined_factors, output_dir=None):
        """生成IRS格式因子文件（修复版 - 输出因子分数而非权重）"""
        if output_dir is None:
            output_dir = r'd:\谷歌反重力\股票量化\irs_factors_fixed'
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n" + "=" * 80)
        print("📁 批量生成IRS因子文件（修复版）")
        print("=" * 80)
        print(f"  输出目录: {output_dir}")
        print("  ⚠️  关键修复：输出因子分数，而非权重！")
        
        grouped = combined_factors.groupby('TradingDay')
        total_dates = len(grouped)
        
        print(f"  总天数: {total_dates}")
        print("\n  生成进度:")
        
        generated_files = []
        
        for date, group in tqdm(grouped, desc="  生成文件"):
            if len(group) == 0:
                continue
            
            # 提取股票代码（补齐6位）
            group = group.copy()
            group['stock_code'] = group['SecuCode'].astype(str).str.extract(r'(\d+)')[0]
            group['stock_code'] = group['stock_code'].str.zfill(6)  # 补齐6位
            
            # 生成文件名
            date_str = date.strftime('%Y%m%d')
            output_file = os.path.join(output_dir, f'{date_str}.csv')
            
            # ⚠️ 关键修复：保存因子分数，不是权重！
            # IRS会根据因子分数自动计算持仓权重
            group[['stock_code', 'combined_factor']].to_csv(
                output_file,
                index=False,
                header=False
            )
            
            generated_files.append(output_file)
        
        print(f"\n✅ 文件生成完成: {len(generated_files)} 个")
        print(f"  ✨ 格式：股票代码,因子分数（IRS会自动处理）")
        
        return generated_files, output_dir


def main():
    START_DATE = datetime(2021, 2, 1)
    END_DATE = datetime(2024, 12, 31)
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 20 + "修复版 IRS因子文件生成系统（正确格式）" + " " * 21 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    try:
        print("\n【第1步】加载JYDB数据")
        loader = JYDBDataLoader()
        
        print("\n【第2步】初始化因子生成器")
        generator = IRSFactorGenerator(loader)
        
        print("\n【第3步】批量计算因子")
        factor_df = generator.calculate_all_factors_vectorized(START_DATE, END_DATE)
        
        print("\n【第4步】处理和合成因子")
        combined_factors = generator.process_and_combine_factors(factor_df)
        
        print("\n【第5步】生成IRS格式文件（修复版）")
        files, output_dir = generator.generate_irs_files_fixed(combined_factors)
        
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + " " * 30 + "✅ 全部完成！" + " " * 34 + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        
        print(f"\n📊 关键修复说明:")
        print(f"   ❌ 之前：输出等权重（0.02），IRS无法识别")
        print(f"   ✅ 现在：输出因子分数，IRS自动计算权重")
        print(f"\n📁 生成文件: {len(files)} 个")
        print(f"   保存位置: {output_dir}")
        print(f"\n🎯 下一步: 在IRS平台回测")
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
