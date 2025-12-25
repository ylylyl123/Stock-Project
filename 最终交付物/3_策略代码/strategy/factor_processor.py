"""
因子处理器 - 标准化、去极值、合成
"""

import pandas as pd
import numpy as np

class FactorProcessor:
    """因子处理器 - 标准化、去极值、合成"""
    
    @staticmethod
    def winsorize(series, n_sigma=3):
        """
        去极值 - MAD方法（中位数绝对偏差）
        
        Args:
            series: 因子序列
            n_sigma: 几倍MAD
        
        Returns:
            处理后的序列
        """
        if len(series) == 0 or series.isna().all():
            return series
        
        median = series.median()
        mad = (series - median).abs().median()
        
        if mad == 0:
            return series
        
        upper = median + n_sigma * mad
        lower = median - n_sigma * mad
        return series.clip(lower, upper)
    
    @staticmethod
    def standardize(series):
        """
        标准化 - Z-Score
        
        Args:
            series: 因子序列
        
        Returns:
            标准化后的序列
        """
        if len(series) == 0 or series.isna().all():
            return series
        
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return series - mean
        
        return (series - mean) / std
    
    def process_factors(self, factor_df):
        """
        处理因子：去极值 + 标准化
        
        Args:
            factor_df: 包含多个因子列的DataFrame
        
        Returns:
            处理后的DataFrame
        """
        processed = factor_df.copy()
        
        # 排除非因子列
        exclude_cols = ['SecuCode', 'TradingDay', 'InnerCode']
        factor_cols = [col for col in processed.columns if col not in exclude_cols]
        
        for col in factor_cols:
            # 去极值
            processed[col] = self.winsorize(processed[col])
            # 标准化
            processed[col] = self.standardize(processed[col])
        
        return processed
    
    def combine_factors(self, factor_df, weights=None):
        """
        合成因子 - 加权平均
        
        Args:
            factor_df: 包含多个因子列的DataFrame
            weights: 因子权重字典，如 {'momentum': 0.2, 'reversal': 0.15, ...}
                    如果为None，则等权
        
        Returns:
            包含'SecuCode'和'combined_factor'列的DataFrame
        """
        # 获取因子列
        exclude_cols = ['SecuCode', 'TradingDay', 'InnerCode']
        factor_cols = [col for col in factor_df.columns if col not in exclude_cols]
        
        if len(factor_cols) == 0:
            raise ValueError("没有找到因子列")
        
        # 设置权重
        if weights is None:
            # 等权
            weights = {col: 1.0 / len(factor_cols) for col in factor_cols}
        
        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight == 0:
            raise ValueError("权重总和为0")
        weights = {k: v/total_weight for k, v in weights.items()}
        
        # 计算加权得分
        result = factor_df[['SecuCode']].copy()
        result['combined_factor'] = 0
        
        for col in factor_cols:
            weight = weights.get(col, 0)
            result['combined_factor'] += factor_df[col].fillna(0) * weight
        
        return result


if __name__ == '__main__':
    # 测试因子处理
    from data_loader import JYDBDataLoader
    from factor_calculator import FactorCalculator
    from datetime import datetime
    
    print("=" * 80)
    print("因子处理器测试")
    print("=" * 80)
    
    # 加载数据
    loader = JYDBDataLoader()
    calculator = FactorCalculator(loader)
    processor = FactorProcessor()
    
    # 计算因子
    test_date = datetime(2021, 1, 4)
    print(f"\n1. 计算 {test_date.date()} 的原始因子...")
    raw_factors = calculator.calculate_all_factors(test_date)
    
    if len(raw_factors) > 0:
        print(f"   ✅ 原始因子: {len(raw_factors)} 只股票")
        print(f"\n   原始因子统计:")
        print(raw_factors.describe())
        
        # 处理因子
        print(f"\n2. 处理因子（去极值+标准化）...")
        processed_factors = processor.process_factors(raw_factors)
        print(f"   ✅ 处理后因子: {len(processed_factors)} 只股票")
        print(f"\n   处理后统计:")
        print(processed_factors.describe())
        
        # 合成因子
        print(f"\n3. 合成因子（等权）...")
        combined = processor.combine_factors(processed_factors)
        print(f"   ✅ 合成因子: {len(combined)} 只股票")
        print(f"\n   Top 10 股票:")
        print(combined.nlargest(10, 'combined_factor'))
        
        # 测试自定义权重
        print(f"\n4. 合成因子（自定义权重）...")
        custom_weights = {
            'momentum': 0.20,
            'reversal': 0.15,
            'volume_spike': 0.15,
            'rsi': 0.15,
            'ep_proxy': 0.20,
            'bp_proxy': 0.15
        }
        combined_custom = processor.combine_factors(processed_factors, custom_weights)
        print(f"   ✅ 合成因子: {len(combined_custom)} 只股票")
        print(f"\n   Top 10 股票:")
        print(combined_custom.nlargest(10, 'combined_factor'))
        
    else:
        print(f"\n❌ 无法计算因子")
    
    print("\n" + "=" * 80)
