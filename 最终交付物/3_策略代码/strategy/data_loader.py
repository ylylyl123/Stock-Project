"""
JYDB数据加载器 - 从本地CSV文件加载数据
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class JYDBDataLoader:
    """JYDB数据加载器 - 从本地CSV文件加载"""
    
    def __init__(self, data_dir=r'd:\谷歌反重力\股票量化\data'):
        self.data_dir = data_dir
        self.daily_quotes = None
        self.trading_calendar = None
        self.stock_list = None
        self.industry = None
        self.trading_days = None
        self._load_all_data()
    
    def _load_all_data(self):
        """一次性加载所有数据到内存"""
        print("=" * 80)
        print("📥 正在加载数据...")
        print("=" * 80)
        
        # 1. 加载日线数据
        print("  [1/4] 加载日线行情数据...") 
        daily_quotes_file = os.path.join(self.data_dir, 'daily_quotes.csv')
        self.daily_quotes = pd.read_csv(daily_quotes_file)
        self.daily_quotes['TradingDay'] = pd.to_datetime(self.daily_quotes['TradingDay'])
        print(f"        ✅ 日线数据: {len(self.daily_quotes):,} 条")
        
        # 2. 加载交易日历
        print("  [2/4] 加载交易日历...")
        calendar_file = os.path.join(self.data_dir, 'trading_calendar.csv')
        self.trading_calendar = pd.read_csv(calendar_file)
        self.trading_calendar['TradingDate'] = pd.to_datetime(self.trading_calendar['TradingDate'])
        self.trading_days = self.trading_calendar[
            self.trading_calendar['IfTradingDay'] == 1
        ]['TradingDate'].sort_values().tolist()
        print(f"        ✅ 交易日: {len(self.trading_days):,} 天")
        
        # 3. 加载股票列表
        print("  [3/4] 加载股票列表...")
        stock_list_file = os.path.join(self.data_dir, 'stock_list.csv')
        self.stock_list = pd.read_csv(stock_list_file)
        print(f"        ✅ 股票数量: {len(self.stock_list):,} 只")
        
        # 4. 加载行业分类
        print("  [4/4] 加载行业分类...")
        industry_file = os.path.join(self.data_dir, 'industry_classification.csv')
        self.industry = pd.read_csv(industry_file)
        print(f"        ✅ 行业记录: {len(self.industry):,} 条")
        
        print("\n" + "=" * 80)
        print("✅ 数据加载完成！")
        print("=" * 80)
        print(f"数据时间范围: {self.daily_quotes['TradingDay'].min().date()} 至 {self.daily_quotes['TradingDay'].max().date()}")
        print(f"交易日范围: {self.trading_days[0].date()} 至 {self.trading_days[-1].date()}")
        print("=" * 80)
        print()
    
    def get_price_data(self, start_date, end_date):
        """获取指定时间段的价格数据"""
        mask = (
            (self.daily_quotes['TradingDay'] >= start_date) &
            (self.daily_quotes['TradingDay'] <= end_date)
        )
        return self.daily_quotes[mask].copy()
    
    def get_trading_days(self, start_date, end_date):
        """获取指定时间段的交易日"""
        return [d for d in self.trading_days 
                if start_date <= d <= end_date]
    
    def get_latest_data_before_date(self, date):
        """获取某日期之前最新的数据"""
        mask = self.daily_quotes['TradingDay'] <= date
        return self.daily_quotes[mask].copy()


if __name__ == '__main__':
    # 测试数据加载
    loader = JYDBDataLoader()
    
    # 测试获取数据
    print("\n测试获取2021年1月数据...")
    jan_data = loader.get_price_data(
        datetime(2021, 1, 1),
        datetime(2021, 1, 31)
    )
    print(f"  2021年1月数据量: {len(jan_data)} 条")
    print(f"  股票数量: {jan_data['SecuCode'].nunique()} 只")
    
    # 测试获取交易日
    print("\n测试获取2021年交易日...")
    trading_days_2021 = loader.get_trading_days(
        datetime(2021, 1, 1),
        datetime(2021, 12, 31)
    )
    print(f"  2021年交易日: {len(trading_days_2021)} 天")
    
    print("\n✅ 数据加载器测试通过！")
