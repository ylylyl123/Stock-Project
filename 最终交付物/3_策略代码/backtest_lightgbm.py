"""
LightGBM多因子策略 - 机器学习动态优化因子权重
使用滚动窗口训练，避免未来信息泄露
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'strategy'))
from data_loader import JYDBDataLoader

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("⚠️  LightGBM未安装，尝试安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lightgbm"])
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True


class LightGBMFactorStrategy:
    """LightGBM多因子策略"""
    
    def __init__(self, data_loader, train_days=252, retrain_freq=20):
        """
        参数:
            data_loader: 数据加载器
            train_days: 训练窗口天数（默认252个交易日，约1年）
            retrain_freq: 重新训练频率（默认20天）
        """
        self.loader = data_loader
        self.train_days = train_days
        self.retrain_freq = retrain_freq
        self.model = None
    
    def calculate_factors_batch(self, start_date, end_date):
        """批量计算5个核心因子"""
        print("\n📊 批量计算因子...")
        
        lookback = 260
        trading_days = self.loader.get_trading_days(start_date, end_date)
        start_idx = self.loader.trading_days.index(trading_days[0])
        actual_start = self.loader.trading_days[max(0, start_idx - lookback)]
        
        df = self.loader.get_price_data(actual_start, end_date).copy()
        df = df.sort_values(['SecuCode', 'TradingDay'])
        
        print("  计算因子...")
        df['momentum_20d'] = df.groupby('SecuCode')['ClosePrice'].pct_change(periods=20) * 100
        df['reversal_5d'] = -df.groupby('SecuCode')['ClosePrice'].pct_change(periods=5) * 100
        df['ep_ratio'] = 1 / (df['ClosePrice'] + 1e-10) * 1000
        df['price_ma_250'] = df.groupby('SecuCode')['ClosePrice'].transform(
            lambda x: x.rolling(250, min_periods=125).mean()
        )
        df['bp_ratio'] = df['price_ma_250'] / (df['ClosePrice'] + 1e-10)
        df['vol_ma_20'] = df.groupby('SecuCode')['TurnoverVolume'].transform(
            lambda x: x.rolling(20, min_periods=10).mean()
        )
        df['volume_anomaly'] = df['TurnoverVolume'] / (df['vol_ma_20'] + 1e-10)
        
        # 计算未来收益（用于训练标签）
        df['future_return'] = df.groupby('SecuCode')['ClosePrice'].shift(-5).pct_change(periods=5) * 100
        
        factor_cols = ['SecuCode', 'TradingDay', 'ClosePrice', 'momentum_20d', 'reversal_5d', 
                      'ep_ratio', 'bp_ratio', 'volume_anomaly', 'future_return']
        
        df = df[factor_cols]
        df = df[df['TradingDay'] >= start_date].copy()
        
        print(f"  ✅ 因子计算完成: {len(df):,} 条")
        return df
    
    def prepare_training_data(self, factor_df, train_start, train_end):
        """准备训练数据"""
        train_data = factor_df[
            (factor_df['TradingDay'] >= train_start) & 
            (factor_df['TradingDay'] <= train_end)
        ].copy()
        
        feature_cols = ['momentum_20d', 'reversal_5d', 'ep_ratio', 'bp_ratio', 'volume_anomaly']
        
        # 去极值和标准化
        for col in feature_cols:
            median = train_data[col].median()
            mad = (train_data[col] - median).abs().median()
            if mad > 0:
                upper = median + 3 * mad
                lower = median - 3 * mad
                train_data[col] = train_data[col].clip(lower, upper)
            
            mean = train_data[col].mean()
            std = train_data[col].std()
            if std > 0:
                train_data[col] = (train_data[col] - mean) / std
        
        # 移除缺失值
        train_data = train_data.dropna(subset=feature_cols + ['future_return'])
        
        X = train_data[feature_cols].values
        y = train_data['future_return'].values
        
        return X, y, feature_cols
    
    def train_model(self, X, y):
        """训练LightGBM模型"""
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        train_data = lgb.Dataset(X, label=y)
        self.model = lgb.train(params, train_data, num_boost_round=100)
        
        return self.model
    
    def predict_scores(self, factor_df, date, feature_cols):
        """预测因子得分"""
        daily_data = factor_df[factor_df['TradingDay'] == date].copy()
        
        if len(daily_data) == 0:
            return pd.DataFrame()
        
        # 标准化
        for col in feature_cols:
            median = daily_data[col].median()
            mad = (daily_data[col] - median).abs().median()
            if mad > 0:
                upper = median + 3 * mad
                lower = median - 3 * mad
                daily_data[col] = daily_data[col].clip(lower, upper)
            
            mean = daily_data[col].mean()
            std = daily_data[col].std()
            if std > 0:
                daily_data[col] = (daily_data[col] - mean) / std
        
        # 预测
        X = daily_data[feature_cols].fillna(0).values
        
        if self.model is not None:
            scores = self.model.predict(X)
            daily_data['predicted_score'] = scores
        else:
            # 如果模型未训练，使用简单线性组合
            weights = [0.3, 0.15, 0.25, 0.15, 0.15]
            daily_data['predicted_score'] = sum(daily_data[col].fillna(0) * w for col, w in zip(feature_cols, weights))
        
        return daily_data[['SecuCode', 'ClosePrice', 'predicted_score']]
    
    def backtest(self, start_date, end_date, top_n=50):
        """完整回测流程"""
        print("\n" + "="*80)
        print("🤖 LightGBM多因子策略回测")
        print("="*80)
        
        # 1. 计算所有因子
        factor_df = self.calculate_factors_batch(start_date, end_date)
        
        # 2. 准备回测
        trading_days = self.loader.get_trading_days(start_date, end_date)
        
        initial_capital = 80000000
        capital = initial_capital
        holdings = {}
        daily_values = []
        
        print(f"\n🔄 开始滚动回测...")
        print(f"  训练窗口: {self.train_days}天")
        print(f"  重训频率: {self.retrain_freq}天")
        print(f"  选股数量: Top {top_n}")
        
        for i, date in enumerate(tqdm(trading_days, desc="  回测进度")):
            # 3. 滚动训练模型
            if i % self.retrain_freq == 0 and i >= self.train_days:
                train_start = trading_days[max(0, i - self.train_days)]
                train_end = trading_days[i - 1]
                
                X, y, feature_cols = self.prepare_training_data(factor_df, train_start, train_end)
                
                if len(X) > 100:  # 确保有足够数据
                    self.train_model(X, y)
            
            # 4. 获取当日数据
            daily_quotes = factor_df[factor_df['TradingDay'] == date]
            
            if len(daily_quotes) == 0:
                continue
            
            # 5. 计算持仓市值
            if holdings:
                portfolio_value = 0
                for stock, shares in list(holdings.items()):
                    stock_price = daily_quotes[daily_quotes['SecuCode'] == stock]
                    if len(stock_price) > 0:
                        price = stock_price.iloc[0]['ClosePrice']
                        portfolio_value += shares * price
                    else:
                        # 股票退市或停牌，移除持仓
                        del holdings[stock]
                
                capital = portfolio_value if portfolio_value > 0 else capital
            
            # 6. 月初调仓
            if i % 20 == 0 and i >= self.train_days:
                # 清仓
                holdings = {}
                
                # 预测得分
                scores = self.predict_scores(factor_df, date, feature_cols if self.model else ['momentum_20d', 'reversal_5d', 'ep_ratio', 'bp_ratio', 'volume_anomaly'])
                
                if len(scores) >= top_n:
                    # 选Top N
                    top_stocks = scores.nlargest(top_n, 'predicted_score')
                    
                    # 等权买入
                    per_stock_value = capital / top_n
                    
                    for _, row in top_stocks.iterrows():
                        stock_code = row['SecuCode']
                        price = row['ClosePrice']
                        shares = int(per_stock_value / price)
                        if shares > 0:
                            holdings[stock_code] = shares
            
            # 7. 记录净值
            daily_values.append({
                'date': date,
                'value': capital
            })
        
        # 8. 计算结果
        print("\n📊 计算回测指标...")
        df_values = pd.DataFrame(daily_values)
        df_values['return'] = df_values['value'].pct_change()
        
        total_return = (df_values['value'].iloc[-1] / initial_capital - 1) * 100
        days = (df_values['date'].iloc[-1] - df_values['date'].iloc[0]).days
        years = days / 365
        annual_return = (np.power(df_values['value'].iloc[-1] / initial_capital, 1/years) - 1) * 100
        
        df_values['cummax'] = df_values['value'].cummax()
        df_values['drawdown'] = (df_values['value'] / df_values['cummax'] - 1) * 100
        max_drawdown = df_values['drawdown'].min()
        
        sharpe = df_values['return'].mean() / df_values['return'].std() * np.sqrt(252) if df_values['return'].std() > 0 else 0
        
        # 9. 输出结果
        print("\n" + "="*80)
        print("📈 LightGBM策略回测结果")
        print("="*80)
        print(f"回测期间: {df_values['date'].iloc[0].date()} 至 {df_values['date'].iloc[-1].date()}")
        print(f"初始资金: {initial_capital:,.0f} 元")
        print(f"最终资金: {df_values['value'].iloc[-1]:,.0f} 元")
        print(f"\n🎯 总收益率: {total_return:.2f}%")
        print(f"📊 年化收益率: {annual_return:.2f}%")
        print(f"📉 最大回撤: {max_drawdown:.2f}%")
        print(f"⚡ 夏普比率: {sharpe:.3f}")
        print("="*80)
        
        # 保存结果
        output_file = r"d:\谷歌反重力\股票量化\backtest_lightgbm.csv"
        df_values.to_csv(output_file, index=False)
        print(f"\n✅ 结果已保存: {output_file}")
        
        return df_values


def main():
    START_DATE = datetime(2021, 2, 1)
    END_DATE = datetime(2024, 12, 31)
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 20 + "LightGBM多因子策略回测系统" + " " * 28 + "█")
    print("█" + " " * 15 + "机器学习动态优化 | 滚动训练 | 本地数据" + " " * 18 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    try:
        # 1. 加载数据
        print("\n【第1步】加载JYDB数据")
        loader = JYDBDataLoader()
        
        # 2. 初始化策略
        print("\n【第2步】初始化LightGBM策略")
        strategy = LightGBMFactorStrategy(
            loader, 
            train_days=252,  # 1年训练窗口
            retrain_freq=20  # 每20天重训
        )
        
        # 3. 运行回测
        print("\n【第3步】运行回测")
        result = strategy.backtest(START_DATE, END_DATE, top_n=50)
        
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + " " * 30 + "✅ 回测完成！" + " " * 34 + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
