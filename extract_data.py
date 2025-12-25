import pandas as pd
import json
import numpy as np

# Paths
lightgbm_path = "/Volumes/T7/谷歌反重力/股票量化最终版本/最终交付物/2_回测数据/backtest_lightgbm.csv"
benchmark_path = "/Volumes/T7/谷歌反重力/股票量化最终版本/最终交付物/2_回测数据/backtest_result.csv"

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def process_data():
    # Load Data
    df_lgbm = pd.read_csv(lightgbm_path)
    df_bench = pd.read_csv(benchmark_path)

    # Ensure Date format
    df_lgbm['date'] = pd.to_datetime(df_lgbm['date'])
    df_bench['date'] = pd.to_datetime(df_bench['date'])

    # 1. Net Value Curve Data
    # Normalize to start at 1.0 for comparison
    initial_value_lgbm = df_lgbm['value'].iloc[0]
    initial_value_bench = df_bench['value'].iloc[0]
    
    # Merge
    merged = pd.merge(df_lgbm[['date', 'value', 'drawdown', 'return']], 
                      df_bench[['date', 'value', 'drawdown']], 
                      on='date', how='left', suffixes=('_lgbm', '_bench'))
    
    # Fill NaN benchmark
    merged['value_bench'] = merged['value_bench'].ffill()
    
    # Calculate Normalized Values
    merged['nav_lgbm'] = merged['value_lgbm'] / initial_value_lgbm
    merged['nav_bench'] = merged['value_bench'] / initial_value_bench
    
    # 2. Monthly Returns (Heatmap)
    # Resample to Monthly
    merged.set_index('date', inplace=True)
    monthly_returns = merged['value_lgbm'].resample('ME').last().pct_change()
    
    # Reset index to access dt accessor
    mr_df = monthly_returns.reset_index()
    mr_df.columns = ['date', 'return']
    mr_df['year'] = mr_df['date'].dt.year
    mr_df['month'] = mr_df['date'].dt.month
    
    years = sorted(mr_df['year'].unique())
    months = list(range(1, 13))
    
    z_values = []
    text_values = []
    
    # Matrix for current Heatmap (Years on Y, Months on X)
    for y in years:
        row_z = []
        row_text = []
        for m in months:
            val = mr_df[(mr_df['year'] == y) & (mr_df['month'] == m)]['return'].values
            if len(val) > 0:
                ret = val[0]
                row_z.append(ret)
                row_text.append(f"{ret:.2%}")
            else:
                row_z.append(None)
                row_text.append("")
        z_values.append(row_z)
        text_values.append(row_text)

    daily_rets = merged['return'].dropna().tolist()

    output = {
        "dates": merged.index.strftime('%Y-%m-%d').tolist(),
        "nav_lgbm": merged['nav_lgbm'].tolist(),
        "nav_bench": merged['nav_bench'].tolist(),
        "drawdown_lgbm": merged['drawdown_lgbm'].tolist(),
        "drawdown_bench": merged['drawdown_bench'].tolist(),
        "heatmap": {
            "years": years,
            "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "z": z_values,
            "text": text_values
        },
        "distribution": daily_rets
    }
    
    with open('ppt_data.json', 'w') as f:
        json.dump(output, f, cls=NpEncoder)

if __name__ == "__main__":
    process_data()
