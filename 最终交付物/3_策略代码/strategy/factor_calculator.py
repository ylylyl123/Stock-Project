"""
因子计算器 - 计算量价因子和基本面代理因子
"""

import pandas as pd
import numpy as np

class FactorCalculator:
    """多因子计算器"""
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
    
    # ========== 量价因子 ==========
    
    def calculate_momentum(self, df, period=20):
        """动量因子 - 过去N天收益率"""
        df = df.sort_values(['SecuCode', 'TradingDay'])
        df['momentum'] = df.groupby('SecuCode')['ClosePrice'].pct_change(periods=period)
        return df[['SecuCode', 'TradingDay', 'momentum']].dropna()
    
    def calculate_reversal(self, df, period=5):
        """短期反转因子 - 反向动量"""
        df = df.sort_values(['SecuCode', 'TradingDay'])
        df['reversal'] = -df.groupby('SecuCode')['ClosePrice'].pct_change(periods=period)
        return df[['SecuCode', 'TradingDay', 'reversal']].dropna()
    
    def calculate_volume_spike(self, df, period=20):
        """成交量异常因子 - 相对于均值的变化"""
        df = df.sort_values(['SecuCode', 'TradingDay'])
        df['vol_ma'] = df.groupby('SecuCode')['TurnoverVolume'].transform(
            lambda x: x.rolling(period, min_periods=period//2).mean()
        )
        df['volume_spike'] = df['TurnoverVolume'] / (df['vol_ma'] + 1e-10)
        return df[['SecuCode', 'TradingDay', 'volume_spike']].dropna()
    
    # ========== 技术指标因子 ==========
    
    def calculate_rsi(self, df, period=14):
        """RSI相对强弱指标"""
        df = df.sort_values(['SecuCode', 'TradingDay'])
        
        def rsi_calc(prices):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(period, min_periods=period//2).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period, min_periods=period//2).mean()
            rs = gain / (loss + 1e-10)
            return 100 - (100 / (1 + rs))
        
        df['rsi'] = df.groupby('SecuCode')['ClosePrice'].transform(rsi_calc)
        return df[['SecuCode', 'TradingDay', 'rsi']].dropna()
    
    # ========== 基本面因子代理（使用价格数据估算）==========
    
    def calculate_ep_proxy(self, df):
        """EP因子代理 - 使用价格倒数作为估值代理（价格越低估值越好）"""
        df = df.copy()
        df['ep_proxy'] = 1 / (df['ClosePrice'] + 1e-10)
        return df[['SecuCode', 'TradingDay', 'ep_proxy']]
    
    def calculate_bp_proxy(self, df, period=250):
        """BP因子代理 - 使用历史均价与当前价格的比率"""
        df = df.sort_values(['SecuCode', 'TradingDay'])
        df['price_ma_250'] = df.groupby('SecuCode')['ClosePrice'].transform(
            lambda x: x.rolling(period, min_periods=period//2).mean()
        )
        df['bp_proxy'] = df['price_ma_250'] / (df['ClosePrice'] + 1e-10)
        return df[['SecuCode', 'TradingDay', 'bp_proxy']].dropna()
    
    # ========== 组合因子计算 ==========
    
    def calculate_all_factors(self, date):
        """
        计算某一天所有股票的所有因子
        
        Args:
            date: 交易日期（datetime对象）
        
        Returns:
            DataFrame with all factors for the given date
        """
        # 获取过去一段时间的数据用于计算（需要足够的历史窗口）
        lookback_days = 250
        
        try:
            date_idx = self.data_loader.trading_days.index(date)
        except ValueError:
            print(f"⚠️  {date.date()} 不是交易日")
            return pd.DataFrame()
        
        start_idx = max(0, date_idx - lookback_days)
        start_date = self.data_loader.trading_days[start_idx]
        
        # 获取历史数据
        hist_data = self.data_loader.get_price_data(start_date, date)
        
        if len(hist_data) == 0:
            print(f"⚠️  {date.date()}: 无数据")
            return pd.DataFrame()
        
        # 计算各因子
        try:
            momentum_df = self.calculate_momentum(hist_data, period=20)
            reversal_df = self.calculate_reversal(hist_data, period=5)
            volume_spike_df = self.calculate_volume_spike(hist_data, period=20)
            rsi_df = self.calculate_rsi(hist_data, period=14)
            ep_proxy_df = self.calculate_ep_proxy(hist_data)
            bp_proxy_df = self.calculate_bp_proxy(hist_data, period=250)
            
            # 只取当日数据
            date_mask = lambda df: df[df['TradingDay'] == date]
            
            factors = date_mask(momentum_df)[['SecuCode', 'momentum']].copy()
            
            # 逐个合并因子
            for df, factor_name in [
                (reversal_df, 'reversal'),
                (volume_spike_df, 'volume_spike'),
                (rsi_df, 'rsi'),
                (ep_proxy_df, 'ep_proxy'),
                (bp_proxy_df, 'bp_proxy')
            ]:
                daily_df = date_mask(df)[['SecuCode', factor_name]]
                factors = factors.merge(daily_df, on='SecuCode', how='outer')
            
            # 添加日期列
            factors['TradingDay'] = date
            
            # 删除任何因子有缺失的股票
            factors = factors.dropna()
            
            return factors
            
        except Exception as e:
            print(f"❌ 计算因子时出错 ({date.date()}): {e}")
            return pd.DataFrame()


if __name__ == '__main__':
    # 测试因子计算
    from data_loader import JYDBDataLoader
    from datetime import datetime
    
    print("=" * 80)
    print("因子计算器测试")
    print("=" * 80)
    
    # 加载数据
    loader = JYDBDataLoader()
    
    # 初始化因子计算器
    calculator = FactorCalculator(loader)
    
    # 测试计算2021年1月4日的因子
    test_date = datetime(2021, 1, 4)
    print(f"\n测试计算 {test_date.date()} 的因子...")
    
    factors = calculator.calculate_all_factors(test_date)
    
    if len(factors) > 0:
        print(f"\n✅ 计算成功！")
        print(f"  股票数量: {len(factors)}")
        print(f"  因子列: {list(factors.columns)}")
        print(f"\n前5只股票的因子值:")
        print(factors.head())
        
        print(f"\n因子统计:")
        print(factors.describe())
    else:
        print(f"\n❌ 计算失败或无数据")
    
    print("\n" + "=" * 80)
