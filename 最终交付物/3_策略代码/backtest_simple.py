"""
简单回测脚本 - 直接计算策略收益
绕过IRS平台，使用本地JYDB数据
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob

def simple_backtest():
    """简单回测函数"""
    
    print("\n" + "="*80)
    print("📊 多因子策略简单回测")
    print("="*80)
    
    # 1. 读取因子文件
    factor_dir = r"D:\irs_final"
    print(f"\n1. 读取因子文件: {factor_dir}")
    
    factor_files = sorted(glob.glob(os.path.join(factor_dir, "*.csv")))
    print(f"   找到 {len(factor_files)} 个因子文件")
    
    # 2. 读取行情数据
    print("\n2. 读取行情数据...")
    quotes = pd.read_csv(r"d:\谷歌反重力\股票量化\data\daily_quotes.csv")
    quotes['TradingDay'] = pd.to_datetime(quotes['TradingDay'])
    quotes['SecuCode_6'] = quotes['SecuCode'].astype(str).str.zfill(6)
    print(f"   行情数据: {len(quotes):,} 条")
    
    # 3. 回测
    print("\n3. 开始回测...")
    initial_capital = 80000000  # 8000万
    capital = initial_capital
    holdings = {}  # 持仓
    daily_values = []
    
    for factor_file in factor_files:
        # 读取因子
        date_str = os.path.basename(factor_file).replace('.csv', '')
        trade_date = datetime.strptime(date_str, '%Y%m%d')
        
        factor_df = pd.read_csv(factor_file, header=None, names=['stock_code', 'factor_score'])
        factor_df['stock_code'] = factor_df['stock_code'].astype(str).str.zfill(6)
        
        # 获取当日行情
        daily_quotes = quotes[quotes['TradingDay'] == trade_date].copy()
        
        if len(daily_quotes) == 0:
            continue
        
        # 合并因子和行情
        merged = factor_df.merge(
            daily_quotes[['SecuCode_6', 'ClosePrice']], 
            left_on='stock_code', 
            right_on='SecuCode_6',
            how='inner'
        )
        
        if len(merged) == 0:
            continue
        
        # 计算持仓市值（如果有持仓的话）
        if holdings:
            portfolio_value = 0
            for stock, shares in holdings.items():
                stock_quotes = daily_quotes[daily_quotes['SecuCode_6'] == stock]
                if len(stock_quotes) > 0:
                    price = stock_quotes.iloc[0]['ClosePrice']
                    portfolio_value += shares * price
            
            capital = portfolio_value
            
        # 月初调仓（简化：每20个交易日）
        if len(daily_values) % 20 == 0:
            # 清仓
            holdings = {}
            
            # 选Top 50
            top_stocks = merged.nlargest(50, 'factor_score')
            
            # 等权买入
            per_stock_value = capital / 50
            
            for _, row in top_stocks.iterrows():
                stock_code = row['stock_code']
                price = row['ClosePrice']
                shares = int(per_stock_value / price)
                if shares > 0:
                    holdings[stock_code] = shares
        
        # 记录净值
        daily_values.append({
            'date': trade_date,
            'value': capital
        })
        
        if len(daily_values) % 100 == 0:
            print(f"   进度: {len(daily_values)}/{len(factor_files)}")
    
    # 4. 计算结果
    print("\n4. 计算回测指标...")
    
    df_values = pd.DataFrame(daily_values)
    df_values['return'] = df_values['value'].pct_change()
    
    # 总收益
    total_return = (df_values['value'].iloc[-1] / initial_capital - 1) * 100
    
    # 年化收益
    days = (df_values['date'].iloc[-1] - df_values['date'].iloc[0]).days
    years = days / 365
    annual_return = (np.power(df_values['value'].iloc[-1] / initial_capital, 1/years) - 1) * 100
    
    # 最大回撤
    df_values['cummax'] = df_values['value'].cummax()
    df_values['drawdown'] = (df_values['value'] / df_values['cummax'] - 1) * 100
    max_drawdown = df_values['drawdown'].min()
    
    # 夏普比率
    sharpe = df_values['return'].mean() / df_values['return'].std() * np.sqrt(252)
    
    # 5. 输出结果
    print("\n" + "="*80)
    print("📈 回测结果")
    print("="*80)
    print(f"回测期间: {df_values['date'].iloc[0].date()} 至 {df_values['date'].iloc[-1].date()}")
    print(f"初始资金: {initial_capital:,.0f} 元")
    print(f"最终资金: {df_values['value'].iloc[-1]:,.0f} 元")
    print(f"\n总收益率: {total_return:.2f}%")
    print(f"年化收益率: {annual_return:.2f}%")
    print(f"最大回撤: {max_drawdown:.2f}%")
    print(f"夏普比率: {sharpe:.3f}")
    print("="*80)
    
    # 保存结果
    output_file = r"d:\谷歌反重力\股票量化\backtest_result.csv"
    df_values.to_csv(output_file, index=False)
    print(f"\n✅ 结果已保存至: {output_file}")
    
    return df_values

if __name__ == '__main__':
    result = simple_backtest()
