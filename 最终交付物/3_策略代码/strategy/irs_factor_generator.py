"""
IRS平台因子文件生成器 - 生成符合IRS格式的因子文件
"""

import pandas as pd
import os
from datetime import datetime
from tqdm import tqdm

class IRSFactorGenerator:
    """IRS平台因子文件生成器"""
    
    def __init__(self, output_dir=r'd:\谷歌反重力\股票量化\irs_factors'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 因子文件输出目录: {output_dir}")
    
    def generate_factor_file(self, date, factor_scores, top_n=50):
        """
        生成单日因子文件
        
        Args:
            date: 交易日期（datetime对象）
            factor_scores: DataFrame with columns ['SecuCode', 'combined_factor']
            top_n: 选择因子值最高的N只股票
        
        Returns:
            生成的文件路径
        """
        if len(factor_scores) < top_n:
            print(f"⚠️  {date.date()}: 股票数量不足（{len(factor_scores)} < {top_n}），跳过")
            return None
        
        # 按因子值降序排序，选择top_n
        top_stocks = factor_scores.nlargest(top_n, 'combined_factor').copy()
        
        # 等权分配
        top_stocks['weight'] = 1.0 / top_n
        
        # 去掉股票代码的交易所后缀（只保留数字部分）
        # SecuCode格式如：000001.SZ -> 000001
        top_stocks['stock_code'] = top_stocks['SecuCode'].str.extract(r'(\d+)')[0]
        
        # 生成文件名 (yyyyMMdd.csv格式)
        date_str = date.strftime('%Y%m%d')
        output_file = os.path.join(self.output_dir, f'{date_str}.csv')
        
        # 保存为CSV（无header，只有两列：股票代码,权重）
        top_stocks[['stock_code', 'weight']].to_csv(
            output_file, 
            index=False, 
            header=False
        )
        
        return output_file
    
    def generate_all_factors(self, start_date, end_date, 
                            data_loader, factor_calculator, 
                            factor_processor, 
                            top_n=50,
                            factor_weights=None):
        """
        批量生成所有交易日的因子文件
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            data_loader: 数据加载器实例
            factor_calculator: 因子计算器实例
            factor_processor: 因子处理器实例
            top_n: 每日选择的股票数量
            factor_weights: 因子权重字典
        
        Returns:
            生成的文件列表
        """
        trading_days = data_loader.get_trading_days(start_date, end_date)
        
        print("\n" + "=" * 80)
        print("🎯 开始批量生成IRS因子文件")
        print("=" * 80)
        print(f"  时间范围: {start_date.date()} 至 {end_date.date()}")
        print(f"  交易日数: {len(trading_days)} 天")
        print(f"  每日选股: Top {top_n} 只")
        print(f"  输出目录: {self.output_dir}")
        print("=" * 80)
        print()
        
        generated_files = []
        failed_dates = []
        
        for date in tqdm(trading_days, desc="生成因子文件"):
            try:
                # 1. 计算原始因子
                raw_factors = factor_calculator.calculate_all_factors(date)
                
                if len(raw_factors) == 0:
                    failed_dates.append((date, "无数据"))
                    continue
                
                # 2. 处理因子（标准化）
                processed_factors = factor_processor.process_factors(raw_factors)
                
                # 3. 合成因子
                combined = factor_processor.combine_factors(
                    processed_factors, 
                    weights=factor_weights
                )
                
                # 4. 生成文件
                output_file = self.generate_factor_file(date, combined, top_n)
                
                if output_file:
                    generated_files.append(output_file)
                    
            except Exception as e:
                failed_dates.append((date, str(e)))
        
        # 输出统计
        print("\n" + "=" * 80)
        print("✅ 批量生成完成！")
        print("=" * 80)
        print(f"  成功生成: {len(generated_files)} 个文件")
        print(f"  失败/跳过: {len(failed_dates)} 天")
        print(f"  保存位置: {self.output_dir}")
        
        if failed_dates and len(failed_dates) < 50:  # 只显示前50个失败日期
            print(f"\n失败日期明细:")
            for date, reason in failed_dates[:10]:
                print(f"  - {date.date()}: {reason}")
            if len(failed_dates) > 10:
                print(f"  ... 还有 {len(failed_dates) - 10} 个失败日期")
        
        print("=" * 80)
        print()
        
        return generated_files


if __name__ == '__main__':
    # 测试生成单个文件
    from data_loader import JYDBDataLoader
    from factor_calculator import FactorCalculator
    from factor_processor import FactorProcessor
    from datetime import datetime
    
    print("=" * 80)
    print("IRS因子文件生成器测试")
    print("=" * 80)
    
    # 初始化组件
    loader = JYDBDataLoader()
    calculator = FactorCalculator(loader)
    processor = FactorProcessor()
    generator = IRSFactorGenerator()
    
    # 测试生成单个文件
    test_date = datetime(2021, 1, 4)
    print(f"\n测试生成 {test_date.date()} 的因子文件...\n")
    
    # 计算并处理因子
    raw_factors = calculator.calculate_all_factors(test_date)
    if len(raw_factors) > 0:
        processed_factors = processor.process_factors(raw_factors)
        combined = processor.combine_factors(processed_factors)
        
        # 生成文件
        output_file = generator.generate_factor_file(test_date, combined, top_n=50)
        
        if output_file:
            print(f"\n✅ 文件生成成功: {output_file}")
            print(f"\n文件内容预览（前10行）:")
            with open(output_file, 'r') as f:
                for i, line in enumerate(f):
                    if i < 10:
                        print(f"  {line.strip()}")
        else:
            print(f"\n❌ 文件生成失败")
    else:
        print(f"\n❌ 无法计算因子")
    
    print("\n" + "=" * 80)
