"""
生成IRS平台因子文件 - 主执行脚本

这个脚本会：
1. 加载JYDB数据
2. 计算多因子（动量、反转、成交量、RSI、估值代理、市净率代理）
3. 标准化和合成因子
4. 为每个交易日生成Top N股票的因子文件（IRS格式）
"""

from datetime import datetime
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from data_loader import JYDBDataLoader
from factor_calculator import FactorCalculator
from factor_processor import FactorProcessor
from irs_factor_generator import IRSFactorGenerator

def main():
    # ==================== 配置参数 ====================
    # 从2021-02-01开始，确保有足够的历史数据计算因子
    START_DATE = datetime(2021, 2, 1)
    END_DATE = datetime(2024, 12, 31)
    TOP_N = 50  # 每日选择Top 50只股票
    
    # 因子权重配置（可根据需要调整）
    FACTOR_WEIGHTS = {
        'momentum': 0.20,      # 动量因子
        'reversal': 0.15,      # 短期反转因子
        'volume_spike': 0.15,  # 成交量异常因子
        'rsi': 0.15,           # RSI技术指标
        'ep_proxy': 0.20,      # 估值代理（E/P）
        'bp_proxy': 0.15,      # 市净率代理（B/P）
    }
    # ==================================================
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + " " * 25 + "IRS平台因子文件生成系统" + " " * 26 + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    print()
    
    try:
        # 第1步：加载数据
        print("【第1步】加载JYDB数据")
        data_loader = JYDBDataLoader()
        
        # 第2步：初始化因子计算器
        print("\n【第2步】初始化因子计算器")
        factor_calculator = FactorCalculator(data_loader)
        print("  ✅ 因子计算器初始化完成")
        print(f"  包含因子: 动量, 反转, 成交量异常, RSI, EP代理, BP代理")
        
        # 第3步：初始化因子处理器
        print("\n【第3步】初始化因子处理器")
        factor_processor = FactorProcessor()
        print("  ✅ 因子处理器初始化完成")
        print(f"  处理方法: 去极值(MAD) + 标准化(Z-Score)")
        
        # 第4步：初始化文件生成器
        print("\n【第4步】初始化IRS文件生成器")
        irs_generator = IRSFactorGenerator()
        print("  ✅ 文件生成器初始化完成")
        
        # 第5步：批量生成因子文件
        print("\n【第5步】批量生成因子文件")
        print(f"  ⏰ 时间范围: {START_DATE.date()} 至 {END_DATE.date()}")
        print(f"  📊 选股数量: Top {TOP_N}")
        print(f"  ⚖️  因子权重: {FACTOR_WEIGHTS}")
        print()
        
        generated_files = irs_generator.generate_all_factors(
            START_DATE, END_DATE,
            data_loader, factor_calculator, factor_processor,
            top_n=TOP_N,
            factor_weights=FACTOR_WEIGHTS
        )
        
        # 输出使用说明
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + " " * 30 + "✅ 全部完成！" + " " * 34 + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        print()
        
        print("📁 生成的因子文件可用于IRS平台回测")
        print(f"   文件位置: d:/谷歌反重力/股票量化/irs_factors/")
        print(f"   文件数量: {len(generated_files)} 个")
        print(f"   文件格式: yyyyMMdd.csv（无header，两列：股票代码,权重）")
        print()
        
        print("🎯 在IRS平台中使用:")
        print("   1. 确保IRS平台正在运行: http://localhost:34326")
        print("   2. 点击'策略' -> 'StockAdjust'")
        print("   3. 填写配置:")
        print(f"      - 因子文件路径: d:/谷歌反重力/股票量化/irs_factors")
        print(f"      - 开始时间: {START_DATE.strftime('%Y-%m-%d')}")
        print(f"      - 结束时间: {END_DATE.strftime('%Y-%m-%d')}")
        print("      - TWAP执行秒数: 300（5分钟）")
        print("      - TWAP开始时间: 09:30")
        print("   4. 点击'开始'运行回测")
        print()
        
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        return 1
        
    except Exception as e:
        print(f"\n\n❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
