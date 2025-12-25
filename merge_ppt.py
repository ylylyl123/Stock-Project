
import json
import re

html_path = "/Volumes/T7/谷歌反重力/股票量化最终版本/Stock_Quant_PPT.html"
data_path = "ppt_data.json"

# New Slides HTML (Slides 6-18)
# Key Changes:
# 1. p-8 instead of p-12 (more space)
# 2. overflow-hidden everywhere
# 3. Chinese labels
# 4. Split Layout for Charts (Height 65% Chart / 35% Analysis)
slides_html = """
    <!-- ==========================================
         Slide 6: 因子体系
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-6 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">策略核心：5大类因子体系</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Five-Factor System</p>
            </div>
            <div class="text-4xl font-bold text-gray-100 absolute top-8 right-10">06</div>
        </div>
        <div class="flex flex-1 gap-8 items-center overflow-hidden">
            <div class="w-full">
                <table class="w-full text-left border-collapse shadow-sm rounded-lg overflow-hidden text-sm">
                    <thead>
                        <tr class="bg-gradient-to-r from-szu-dark to-szu-red text-white">
                            <th class="p-3 w-1/4">因子类别 (Category)</th>
                            <th class="p-3 w-1/4">代表因子 (Factors)</th>
                            <th class="p-3 w-1/2">选股逻辑 (Selection Logic)</th>
                        </tr>
                    </thead>
                    <tbody class="text-gray-700 bg-white">
                        <tr class="border-b border-gray-100 hover:bg-red-50/50 transition-colors group">
                            <td class="p-3 font-bold text-szu-dark group-hover:text-szu-red"><i class="fas fa-chart-line mr-2 w-5 text-center"></i>量价因子</td>
                            <td class="p-3 font-mono text-xs bg-gray-50/50">RSI, MACD, KDJ</td>
                            <td class="p-3 text-gray-600">捕捉短期市场情绪，用于判断<span class="font-bold text-szu-red">短期择时</span>。</td>
                        </tr>
                        <tr class="border-b border-gray-100 hover:bg-red-50/50 transition-colors group">
                            <td class="p-3 font-bold text-szu-dark group-hover:text-szu-red"><i class="fas fa-history mr-2 w-5 text-center"></i>动量/反转</td>
                            <td class="p-3 font-mono text-xs bg-gray-50/50">Momentum_5D, Reversal_20D</td>
                            <td class="p-3 text-gray-600">利用A股独特的<span class="font-bold text-szu-red">"短期反转，长期动量"</span>效应。</td>
                        </tr>
                        <tr class="border-b border-gray-100 hover:bg-red-50/50 transition-colors group">
                            <td class="p-3 font-bold text-szu-dark group-hover:text-szu-red"><i class="fas fa-compress-arrows-alt mr-2 w-5 text-center"></i>波动率因子</td>
                            <td class="p-3 font-mono text-xs bg-gray-50/50">ATR, StdDev_20</td>
                            <td class="p-3 text-gray-600">衡量风险水平，倾向于<span class="font-bold text-szu-red">稳健上涨</span>标的。</td>
                        </tr>
                        <tr class="border-b border-gray-100 hover:bg-red-50/50 transition-colors group">
                            <td class="p-3 font-bold text-szu-dark group-hover:text-szu-red"><i class="fas fa-stream mr-2 w-5 text-center"></i>成交量因子</td>
                            <td class="p-3 font-mono text-xs bg-gray-50/50">Volume_Ratio, OBV</td>
                            <td class="p-3 text-gray-600">"量在价先"，资金流向是主力行为的最直接体现。</td>
                        </tr>
                        <tr class="hover:bg-red-50/50 transition-colors group">
                            <td class="p-3 font-bold text-szu-dark group-hover:text-szu-red"><i class="fas fa-brain mr-2 w-5 text-center"></i>技术衍生</td>
                            <td class="p-3 font-mono text-xs bg-gray-50/50">Bollinger_Band_Width</td>
                            <td class="p-3 text-gray-600">基于统计学的非线性特征提取，捕捉<span class="font-bold text-szu-red">趋势突破</span>。</td>
                        </tr>
                    </tbody>
                </table>
                <div class="mt-6 bg-szu-light p-4 rounded-lg border-l-4 border-szu-gold text-xs text-gray-600 flex items-start gap-3 shadow-inner">
                    <i class="fas fa-lightbulb text-szu-gold text-lg mt-0.5"></i>
                    <div>
                        <p class="font-bold mb-1 text-szu-dark">数据预处理标准 (SOP):</p>
                        <p>1. <span class="font-bold">MAD去极值</span>：防止离群点干扰机器学习模型训练。</p>
                        <p>2. <span class="font-bold">Z-Score标准化</span>：消除不同因子量纲差异，确保模型权重公平分配。</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="page-number">06</div>
    </div>

    <!-- ==========================================
         Slide 7: LightGBM 模型创新
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-4 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">模型创新：LightGBM 滚动训练</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Machine Learning</p>
            </div>
            <div class="text-4xl font-bold text-gray-100 absolute top-8 right-10">07</div>
        </div>
        <div class="flex flex-1 gap-6 items-center justify-center overflow-hidden">
            <div class="w-full relative flex flex-col items-center">
                <!-- Timeline Visualization of Rolling Window -->
                <div class="relative w-full bg-white rounded-xl border border-gray-200 p-6 shadow-sm overflow-hidden">
                    <div class="absolute top-0 right-0 p-2 bg-gray-100 rounded-bl-lg text-[10px] font-mono text-gray-500">SCHEME</div>
                    
                    <div class="flex flex-col gap-4 w-full px-4">
                        <!-- Window 1 -->
                        <div class="flex items-center gap-2 animate-pulse">
                            <div class="w-16 text-[10px] font-bold text-gray-500 text-right">Window 1</div>
                            <div class="flex-1 h-6 bg-gray-100 rounded relative flex items-center overflow-hidden border border-gray-200">
                                <div class="h-full bg-szu-dark w-1/3 flex items-center justify-center text-[10px] text-white/90">Train (252 Days)</div>
                                <div class="h-full bg-szu-gold w-[10%] flex items-center justify-center text-[10px] text-white/90 border-l border-white/20">Test</div>
                                <div class="h-full bg-gray-100 w-1/2"></div>
                            </div>
                        </div>
                        <!-- Window 2 -->
                        <div class="flex items-center gap-2 opacity-80">
                            <div class="w-16 text-[10px] font-bold text-gray-500 text-right">Window 2</div>
                            <div class="flex-1 h-6 bg-gray-100 rounded relative flex items-center overflow-hidden border border-gray-200">
                                <div class="w-[5%]"></div>
                                <div class="h-full bg-szu-dark w-1/3 flex items-center justify-center text-[10px] text-white/90">Train</div>
                                <div class="h-full bg-szu-gold w-[10%] flex items-center justify-center text-[10px] text-white/90 border-l border-white/20">Test</div>
                            </div>
                        </div>
                        <!-- Window 3 -->
                        <div class="flex items-center gap-2 opacity-60">
                            <div class="w-16 text-[10px] font-bold text-gray-500 text-right">Window 3</div>
                            <div class="flex-1 h-6 bg-gray-100 rounded relative flex items-center overflow-hidden border border-gray-200">
                                <div class="w-[10%]"></div>
                                <div class="h-full bg-szu-dark w-1/3 flex items-center justify-center text-[10px] text-white/90">Train</div>
                                <div class="h-full bg-szu-gold w-[10%] flex items-center justify-center text-[10px] text-white/90 border-l border-white/20">Test</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-6 mt-6 w-full">
                    <!-- Left: Parameters -->
                    <div class="p-4 bg-gray-50 rounded-lg border border-gray-200 relative group hover:border-szu-red transition-colors">
                        <div class="absolute -top-3 left-4 bg-white px-2 text-xs font-bold text-szu-red">Key Parameters</div>
                        <ul class="text-xs text-gray-600 space-y-2 mt-1">
                            <li class="flex justify-between border-b border-gray-200 pb-1">
                                <span>训练窗口</span>
                                <span class="font-mono font-bold text-szu-dark">252 天</span>
                            </li>
                            <li class="flex justify-between border-b border-gray-200 pb-1">
                                <span>调仓频率</span>
                                <span class="font-mono font-bold text-szu-dark">20 天 (月频)</span>
                            </li>
                            <li class="flex justify-between">
                                <span>持仓数量</span>
                                <span class="font-mono font-bold text-szu-dark">Top 50</span>
                            </li>
                        </ul>
                    </div>
                    
                    <!-- Right: Why Rolling? -->
                    <div class="p-4 bg-blue-50/50 rounded-lg border border-blue-100 relative">
                        <div class="absolute -top-3 left-4 bg-white px-2 text-xs font-bold text-blue-600">Why Rolling Window?</div>
                        <div class="flex items-start gap-3 mt-1">
                            <i class="fas fa-sync-alt text-blue-400 mt-1"></i>
                            <div>
                                <h4 class="text-xs font-bold text-gray-800">对抗"概念漂移"</h4>
                                <p class="text-[10px] text-gray-500 mt-1 leading-tight">
                                    A股市场风格切换极快。滚动训练确保模型始终学习<span class="font-bold text-blue-600">最近的市场规律</span>，而非被3年前的无效规律误导。
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="page-number">07</div>
    </div>

    <!-- ==========================================
         Slide 8: 回测框架
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-4 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">量化回测框架</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Backtesting Framework</p>
            </div>
            <div class="text-4xl font-bold text-gray-100 absolute top-8 right-10">08</div>
        </div>
        <div class="flex flex-1 items-center justify-center overflow-hidden relative">
            <div class="mermaid w-full flex justify-center transform scale-[0.65] z-10 origin-center px-4">
                %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#FFF0F3', 'primaryTextColor': '#2b2d42', 'primaryBorderColor': '#9F1F35', 'lineColor': '#C49453', 'secondaryColor': '#F3F4F6', 'tertiaryColor': '#fff', 'fontSize': '12px'}}}%%
                flowchart TB
                    Start((开始 Start)) --> Init[初始化资金 1000万]
                    Init --> Loop{交易日循环 Loop}
                    
                    subgraph Strategy[月度调仓机制 Rebalance]
                        direction TB
                        Loop -- 每20日 --> Train[LightGBM 训练]
                        Train --> Predict[预测全市场收益率]
                        Predict --> Rank[Top 50 股票池]
                        Rank --> Weight[等权重分配]
                    end
                    
                    subgraph Execute[交易执行 Execution]
                        direction TB
                        Weight --> Sell[卖出不在池持仓]
                        Sell --> Buy[买入新入池股票]
                        Buy --> Cost["扣除手续费 (Fees: 万分之五)"]
                    end
                    
                    Cost --> Update[更新账户净值]
                    Update --> Loop
                    Loop -- 结束 --> Analyze[绩效归因分析]
                    Analyze --> End((结束 End))
            </div>
        </div>
        <div class="page-number">08</div>
    </div>

    <!-- ==========================================
         Slide 9: 核心结果 - 净值曲线 (Split Layout)
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-center justify-between mb-2 shrink-0">
            <h2 class="text-2xl font-extrabold text-szu-red flex items-center gap-3">
                <i class="fas fa-chart-line"></i> 策略净值曲线 (Net Value)
            </h2>
            <div class="text-xs text-gray-400 font-mono bg-gray-100 px-2 py-1 rounded">2021.02 - 2024.12</div>
        </div>
        
        <!-- Top: Chart Area (60%) -->
        <div class="h-[60%] w-full relative border border-gray-200 rounded-lg p-2 bg-gray-50 mb-4 overflow-hidden">
            <div id="chart-nav" class="w-full h-full"></div>
        </div>
        
        <!-- Bottom: Analysis Box (35%) -->
        <div class="flex-1 bg-gradient-to-r from-red-50 to-white border-l-4 border-szu-red p-4 rounded-r-lg shadow-sm flex flex-col justify-center overflow-hidden">
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 rounded-full bg-szu-red text-white flex items-center justify-center text-lg shrink-0 mt-1 shadow-md">
                    <i class="fas fa-search-dollar"></i>
                </div>
                <div>
                    <h3 class="font-bold text-szu-dark text-sm mb-2">收益表现分析</h3>
                    <ul class="text-xs text-gray-700 space-y-2">
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-green-500 mt-0.5"></i>
                            <span><strong>穿越牛熊</strong>：在2022-2023年市场大幅下跌中，策略净值保持稳健上升，体现极强Alpha能力。</span>
                        </li>
                         <li class="flex items-start gap-2">
                            <i class="fas fa-check text-green-500 mt-0.5"></i>
                            <span><strong>持续跑赢</strong>：红线（策略）始终位于灰线（基准）之上，超额收益随着时间推移不断扩大。</span>
                        </li>
                    </ul>
                </div>
                <div class="ml-auto text-right shrink-0">
                    <p class="text-[10px] text-gray-400 uppercase">Annualized Return</p>
                    <p class="text-2xl font-bold text-szu-gold font-mono">+12.32%</p>
                </div>
            </div>
        </div>
        <div class="page-number">09</div>
    </div>


    <!-- ==========================================
         Slide 10: 核心结果 - 回撤分析 (Split Layout)
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-center justify-between mb-2 shrink-0">
            <h2 class="text-2xl font-extrabold text-szu-red flex items-center gap-3">
                <i class="fas fa-water"></i> 动态回撤分析 (Drawdown)
            </h2>
        </div>
        
        <!-- Top: Chart Area (60%) -->
        <div class="h-[60%] w-full relative border border-gray-200 rounded-lg p-2 bg-gray-50 mb-4 overflow-hidden">
            <div id="chart-drawdown" class="w-full h-full"></div>
        </div>
        
        <!-- Bottom: Analysis Box -->
        <div class="flex-1 bg-gradient-to-r from-blue-50 to-white border-l-4 border-blue-500 p-4 rounded-r-lg shadow-sm flex flex-col justify-center overflow-hidden">
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center text-lg shrink-0 mt-1 shadow-md">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <div>
                    <h3 class="font-bold text-blue-900 text-sm mb-2">风险控制分析</h3>
                    <ul class="text-xs text-gray-700 space-y-2">
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-blue-500 mt-0.5"></i>
                            <span><strong>优于基准</strong>：最大回撤 <span class="font-bold font-mono">-40.95%</span>，优于沪深300的 <span class="font-mono">-45.79%</span>。</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-blue-500 mt-0.5"></i>
                            <span><strong>快速修复</strong>：从回撤坑中爬升的速度明显快于市场，说明策略具备较强的**弹性恢复能力**。</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        <div class="page-number">10</div>
    </div>

    <!-- ==========================================
         Slide 11: 核心结果 - 月度收益热力图 (Split Layout)
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-center justify-between mb-2 shrink-0">
            <h2 class="text-2xl font-extrabold text-szu-red flex items-center gap-3">
                <i class="fas fa-th"></i> 月度收益热力图 (Monthly Returns)
            </h2>
        </div>
        
        <!-- Top: Chart Area -->
        <div class="h-[60%] w-full relative border border-gray-200 rounded-lg p-2 bg-gray-50 mb-4 overflow-hidden">
            <div id="chart-heatmap" class="w-full h-full"></div>
        </div>
        
        <!-- Bottom: Analysis Box -->
        <div class="flex-1 bg-gradient-to-r from-orange-50 to-white border-l-4 border-orange-500 p-4 rounded-r-lg shadow-sm flex flex-col justify-center overflow-hidden">
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 rounded-full bg-orange-500 text-white flex items-center justify-center text-lg shrink-0 mt-1 shadow-md">
                    <i class="fas fa-calendar-alt"></i>
                </div>
                <div>
                    <h3 class="font-bold text-orange-900 text-sm mb-2">季节性表现</h3>
                     <ul class="text-xs text-gray-700 space-y-2">
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-orange-500 mt-0.5"></i>
                            <span><strong>胜率统计</strong>：正收益月份占比超过 <span class="font-bold text-szu-red">55%</span>，深红色月份显著多于冷色月份。</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-orange-500 mt-0.5"></i>
                            <span><strong>日历效应</strong>：策略在每年的Q1和Q4表现相对较强，符合A股"春季躁动"特征。</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        <div class="page-number">11</div>
    </div>

    <!-- ==========================================
         Slide 12: 核心结果 - 收益分布 (Split Layout)
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-center justify-between mb-2 shrink-0">
            <h2 class="text-2xl font-extrabold text-szu-red flex items-center gap-3">
                <i class="fas fa-chart-bar"></i> 收益率分布 (Distribution)
            </h2>
        </div>
        
        <!-- Top: Chart Area -->
        <div class="h-[60%] w-full relative border border-gray-200 rounded-lg p-2 bg-gray-50 mb-4 overflow-hidden">
            <div id="chart-dist" class="w-full h-full"></div>
        </div>

         <!-- Bottom: Analysis Box -->
        <div class="flex-1 bg-gradient-to-r from-gray-50 to-white border-l-4 border-gray-500 p-4 rounded-r-lg shadow-sm flex flex-col justify-center overflow-hidden">
            <div class="flex items-start gap-4">
                <div class="w-10 h-10 rounded-full bg-gray-600 text-white flex items-center justify-center text-lg shrink-0 mt-1 shadow-md">
                    <i class="fas fa-balance-scale"></i>
                </div>
                <div>
                    <h3 class="font-bold text-gray-800 text-sm mb-2">正态性与风险</h3>
                    <ul class="text-xs text-gray-700 space-y-2">
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-gray-600 mt-0.5"></i>
                            <span><strong>右偏分布</strong>：整体分布略向右偏（Long Tail），意味着策略捕捉到了更多的<span class="font-bold text-szu-red">正向极端收益</span>。</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <i class="fas fa-check text-gray-600 mt-0.5"></i>
                            <span><strong>肥尾控制</strong>：左侧极端亏损（肥尾）较少，说明从机制上有效规避了极端的流动性风险。</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        <div class="page-number">12</div>
    </div>

    <!-- ==========================================
         Slide 13: 核心指标统计 (Refined Grid)
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-6 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">核心绩效指标一览</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Performance Metrics</p>
            </div>
            <div class="text-4xl font-bold text-gray-100">13</div>
        </div>

        <div class="grid grid-cols-2 gap-8 flex-1 items-center overflow-hidden">
            <!-- Left: Strategy Highlights -->
            <div class="bg-gradient-to-br from-szu-dark to-szu-red text-white p-6 rounded-2xl shadow-xl flex flex-col justify-center h-full">
                <div class="flex items-center justify-between border-b border-white/20 pb-4 mb-4">
                    <h3 class="text-xl font-bold opacity-90">策略表现 (Strategy)</h3>
                    <i class="fas fa-trophy text-szu-gold text-2xl"></i>
                </div>
                <div class="grid grid-cols-2 gap-y-6 gap-x-4">
                    <div>
                        <p class="text-[10px] opacity-60 uppercase mb-1">Total Return</p>
                        <p class="text-3xl font-mono font-bold text-szu-gold">+57.60%</p>
                    </div>
                    <div>
                        <p class="text-[10px] opacity-60 uppercase mb-1">Annualized</p>
                        <p class="text-2xl font-mono font-bold text-white">+12.32%</p>
                    </div>
                    <div>
                        <p class="text-[10px] opacity-60 uppercase mb-1">Sharpe Ratio</p>
                        <p class="text-2xl font-mono font-bold text-white">0.65</p>
                    </div>
                    <div>
                        <p class="text-[10px] opacity-60 uppercase mb-1">Info Ratio</p>
                        <p class="text-2xl font-mono font-bold text-white/90">0.96</p>
                    </div>
                </div>
            </div>

            <!-- Right: Benchmark Comparison -->
            <div class="bg-gray-50 p-6 rounded-2xl border border-gray-200 flex flex-col justify-center h-full relative overflow-hidden">
                <div class="absolute -right-6 top-10 text-9xl text-gray-200 opacity-20 rotate-12"><i class="fas fa-balance-scale-right"></i></div>
                <div class="flex items-center justify-between border-b border-gray-200 pb-4 mb-4 z-10">
                    <h3 class="text-xl font-bold text-gray-700">基准对比 (vs CSI 300)</h3>
                </div>
                <div class="grid grid-cols-2 gap-y-6 z-10 text-gray-800">
                    <div>
                        <p class="text-[10px] text-gray-400 uppercase mb-1">Benchmark Return</p>
                        <p class="text-3xl font-mono font-bold text-gray-500">-19.60%</p>
                    </div>
                    <div>
                        <p class="text-[10px] text-gray-400 uppercase mb-1">Alpha (Excess)</p>
                        <p class="text-3xl font-mono font-bold text-green-600">+77.2%</p>
                    </div>
                    <div class="col-span-2 bg-white/80 p-3 rounded border border-gray-100 mt-2">
                        <p class="text-xs text-gray-500 leading-relaxed">
                            <span class="font-bold text-szu-red">结论</span>: 在基准大幅下跌近20%的情况下，策略逆势获得正收益，超额收益显著。
                        </p>
                    </div>
                </div>
            </div>
        </div>
        <div class="page-number">13</div>
    </div>

    <!-- ==========================================
         Slide 14: 超额收益分析
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-4 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">超额收益归因</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Attribution Analysis</p>
            </div>
            <div class="text-4xl font-bold text-gray-100 absolute top-8 right-10">14</div>
        </div>
        
        <div class="flex flex-1 gap-8 items-center overflow-hidden">
            <div class="w-1/2 flex flex-col justify-center gap-6">
                <!-- Attribution Item 1 -->
                <div class="flex gap-4 group">
                    <div class="w-12 h-12 rounded-full bg-szu-red text-white flex items-center justify-center shrink-0 text-xl font-bold shadow-lg group-hover:scale-110 transition-transform">1</div>
                    <div class="bg-red-50 p-4 rounded-lg w-full border border-red-100 group-hover:bg-red-100 transition-colors">
                        <h4 class="font-bold text-base text-gray-800 mb-1">熊市防御属性 (Defensive)</h4>
                        <p class="text-xs text-gray-600 leading-relaxed">LightGBM准确识别下跌趋势中的高估值股票，通过定期调仓及时剔除弱势股，实现<span class="font-bold text-szu-red">少亏即是赚</span>。</p>
                    </div>
                </div>
                <!-- Attribution Item 2 -->
                <div class="flex gap-4 group">
                    <div class="w-12 h-12 rounded-full bg-szu-gold text-white flex items-center justify-center shrink-0 text-xl font-bold shadow-lg group-hover:scale-110 transition-transform">2</div>
                    <div class="bg-yellow-50 p-4 rounded-lg w-full border border-yellow-100 group-hover:bg-yellow-100 transition-colors">
                        <h4 class="font-bold text-base text-gray-800 mb-1">非线性挖掘 (Non-Linear)</h4>
                        <p class="text-xs text-gray-600 leading-relaxed">传统线性模型无法捕捉的<span class="font-bold text-szu-gold">因子交互作用</span>（如：高波动下的低反转效应），被树模型有效利用。</p>
                    </div>
                </div>
                <!-- Attribution Item 3 -->
                <div class="flex gap-4 group">
                    <div class="w-12 h-12 rounded-full bg-szu-dark text-white flex items-center justify-center shrink-0 text-xl font-bold shadow-lg group-hover:scale-110 transition-transform">3</div>
                    <div class="bg-gray-100 p-4 rounded-lg w-full border border-gray-200 group-hover:bg-gray-200 transition-colors">
                        <h4 class="font-bold text-base text-gray-800 mb-1">风格自适应 (Adaptive)</h4>
                        <p class="text-xs text-gray-600 leading-relaxed">滚动训练机制让模型在不同市场阶段（牛/熊/震荡）自动侧重不同的有效因子。</p>
                    </div>
                </div>
            </div>
            
            <div class="w-1/2 bg-white rounded-xl p-6 border border-gray-200 shadow-md flex flex-col items-center justify-center h-[90%]">
                <h3 class="font-bold text-gray-700 mb-6 w-full border-b border-gray-100 pb-2">累计超额收益示意</h3>
                <!-- Simple CSS Bar Chart for Illustration -->
                <div class="flex items-end gap-10 h-56 w-full px-12 pb-4">
                    <div class="w-24 bg-gray-300 h-[20%] rounded-t-lg relative group flex flex-col justify-end">
                        <div class="w-full text-center text-lg font-bold text-gray-500 mb-2">-20%</div>
                        <div class="w-full text-center text-[10px] text-white bg-gray-400 py-1 rounded-b-none rounded-t">Benchmark</div>
                    </div>
                    <div class="w-24 bg-gradient-to-t from-szu-red to-orange-500 h-[80%] rounded-t-lg relative group shadow-2xl flex flex-col justify-end overflow-hidden">
                        <div class="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div class="w-full text-center text-3xl font-bold text-szu-red mb-2 drop-shadow-sm">+57%</div>
                        <div class="w-full text-center text-[10px] text-white bg-szu-dark py-1 rounded-b-none rounded-t">Strategy</div>
                    </div>
                </div>
                <div class="bg-green-50 text-green-700 px-4 py-2 rounded-full text-xs font-bold mt-4">
                    <i class="fas fa-arrow-up mr-1"></i> Outperformance: 77%
                </div>
            </div>
        </div>
        <div class="page-number">14</div>
    </div>

    <!-- ==========================================
         Slide 15: 挑战与解决方案 (3-Card Layout)
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-6 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">项目挑战与解决方案</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Challenges & Solutions</p>
            </div>
            <div class="text-4xl font-bold text-gray-100 absolute top-8 right-10">15</div>
        </div>

        <div class="grid grid-cols-3 gap-5 flex-1 items-stretch overflow-hidden">
            <!-- Card 1 -->
            <div class="bg-white border rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-all group flex flex-col hover:-translate-y-1">
                <div class="bg-red-50 p-4 border-b border-red-100 flex items-center gap-3">
                    <div class="w-8 h-8 rounded bg-red-100 flex items-center justify-center text-szu-red"><i class="fas fa-bug"></i></div>
                    <h3 class="font-bold text-szu-dark text-sm">平台受限</h3>
                </div>
                <div class="p-5 flex-1 flex flex-col text-sm">
                    <div class="mb-4">
                         <span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-bold uppercase">Problem</span>
                         <p class="text-gray-600 mt-2 text-xs leading-relaxed">IRS平台无法安装库，NumPy版本冲突，网络受限。</p>
                    </div>
                    <div class="mt-auto border-t border-dashed border-gray-200 pt-4">
                         <span class="text-[10px] bg-green-100 text-green-600 px-2 py-0.5 rounded font-bold uppercase">Solved</span>
                         <p class="text-gray-800 mt-2 text-xs font-semibold">迁移至本地 mac/linux 环境，构建 Conda 虚拟环境。</p>
                    </div>
                </div>
            </div>

            <!-- Card 2 -->
            <div class="bg-white border rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-all group flex flex-col hover:-translate-y-1">
                <div class="bg-yellow-50 p-4 border-b border-yellow-100 flex items-center gap-3">
                    <div class="w-8 h-8 rounded bg-yellow-100 flex items-center justify-center text-yellow-700"><i class="fas fa-hourglass-half"></i></div>
                    <h3 class="font-bold text-yellow-800 text-sm">计算瓶颈</h3>
                </div>
                 <div class="p-5 flex-1 flex flex-col text-sm">
                    <div class="mb-4">
                         <span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-bold uppercase">Problem</span>
                         <p class="text-gray-600 mt-2 text-xs leading-relaxed">400万条大数据逐行计算极其缓慢，耗时 > 3小时。</p>
                    </div>
                    <div class="mt-auto border-t border-dashed border-gray-200 pt-4">
                         <span class="text-[10px] bg-green-100 text-green-600 px-2 py-0.5 rounded font-bold uppercase">Solved</span>
                         <p class="text-gray-800 mt-2 text-xs font-semibold">Vectorization (向量化) 重构，利用 Broadcasting 机制加速至 3分钟。</p>
                    </div>
                </div>
            </div>

            <!-- Card 3 -->
            <div class="bg-white border rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-all group flex flex-col hover:-translate-y-1">
                <div class="bg-blue-50 p-4 border-b border-blue-100 flex items-center gap-3">
                    <div class="w-8 h-8 rounded bg-blue-100 flex items-center justify-center text-blue-700"><i class="fas fa-chart-pie"></i></div>
                    <h3 class="font-bold text-blue-800 text-sm">可视化弱</h3>
                </div>
                 <div class="p-5 flex-1 flex flex-col text-sm">
                    <div class="mb-4">
                         <span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-bold uppercase">Problem</span>
                         <p class="text-gray-600 mt-2 text-xs leading-relaxed">Matplotlib 静态图表丑陋且无法交互分析细节。</p>
                    </div>
                    <div class="mt-auto border-t border-dashed border-gray-200 pt-4">
                         <span class="text-[10px] bg-green-100 text-green-600 px-2 py-0.5 rounded font-bold uppercase">Solved</span>
                         <p class="text-gray-800 mt-2 text-xs font-semibold">引入 Plotly.js，开发 HTML 报告模块，支持 hover/zoom。</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="page-number">15</div>
    </div>

    <!-- ==========================================
         Slide 16: 总结与展望
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-6 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">总结与展望</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Summary & Future Work</p>
            </div>
            <div class="text-4xl font-bold text-gray-100 absolute top-8 right-10">16</div>
        </div>

        <div class="flex flex-1 gap-10 items-start mt-4 overflow-hidden">
            <!-- Left: Summary -->
            <div class="w-1/2 space-y-4">
                <div class="p-4 bg-red-50 rounded-lg border-l-4 border-szu-red">
                    <h3 class="text-lg font-bold text-szu-dark mb-3">项目成果总结</h3>
                    <ul class="space-y-4 text-gray-700 text-sm">
                        <li class="flex items-start gap-3">
                            <i class="fas fa-check-circle text-szu-red mt-1"></i>
                            <span><strong>体系完备</strong>：成功构建了从数据ETL、因子挖掘、模型训练到回测分析的全流程量化系统。</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <i class="fas fa-check-circle text-szu-red mt-1"></i>
                            <span><strong>实战有效</strong>：在A股最困难的时期验证了非线性机器学习模型的有效性 (+57.6%)。</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <i class="fas fa-check-circle text-szu-red mt-1"></i>
                            <span><strong>技能提升</strong>：掌握了金融大数据处理、工程化代码构建及高性能计算的核心技能。</span>
                        </li>
                    </ul>
                </div>
            </div>

            <!-- Right: Future -->
            <div class="w-1/2 space-y-4">
                 <div class="p-4 bg-yellow-50 rounded-lg border-l-4 border-szu-gold">
                    <h3 class="text-lg font-bold text-szu-gold mb-3">未来改进方向</h3>
                    <ul class="space-y-4 text-gray-700 text-sm">
                        <li class="flex items-start gap-3">
                            <i class="fas fa-arrow-circle-right text-szu-gold mt-1"></i>
                            <div>
                                <span class="font-bold block">多源因子融合</span>
                                <span class="text-xs text-gray-500">引入分析师预期、新闻舆情文本等另类数据，提升信息广度。</span>
                            </div>
                        </li>
                        <li class="flex items-start gap-3">
                            <i class="fas fa-arrow-circle-right text-szu-gold mt-1"></i>
                             <div>
                                <span class="font-bold block">模型集成 (Ensemble)</span>
                                <span class="text-xs text-gray-500">结合 XGBoost, CatBoost 与神经网络，降低单一模型过拟合风险。</span>
                            </div>
                        </li>
                        <li class="flex items-start gap-3">
                            <i class="fas fa-arrow-circle-right text-szu-gold mt-1"></i>
                             <div>
                                <span class="font-bold block">精细化风控</span>
                                <span class="text-xs text-gray-500">引入 BARRA 风险因子模型与组合优化器，更好控制回撤。</span>
                            </div>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        <div class="page-number">16</div>
    </div>

    <!-- ==========================================
         Slide 17: 项目开发时间线
         ========================================== -->
    <div class="slide p-8 bg-white flex flex-col justify-center overflow-hidden">
        <div class="flex items-end justify-between border-b-2 border-gray-100 pb-3 mb-4 shrink-0">
            <div>
                <h2 class="text-3xl font-extrabold text-szu-red">项目开发时间线</h2>
                <p class="text-xs text-szu-gold font-bold tracking-widest mt-1 uppercase">Project Timeline</p>
            </div>
            <div class="text-4xl font-bold text-gray-100 absolute top-8 right-10">17</div>
        </div>
        
        <div class="flex flex-1 items-center justify-center px-20 relative overflow-hidden">
             <div class="w-full relative h-[2px] bg-gray-200 mt-0">
                <!-- Point 1: Phase 1 (Top) -->
                <div class="absolute -top-3 left-0 flex flex-col items-center group">
                    <div class="w-6 h-6 bg-szu-red rounded-full border-4 border-white shadow-md z-10 transition-transform group-hover:scale-125"></div>
                    <!-- Label Box (Top) -->
                    <div class="absolute bottom-6 w-40 text-center pb-4 border-l border-dashed border-gray-300 h-16 flex flex-col justify-end">
                        <p class="font-bold text-szu-dark text-xs bg-red-50 px-2 py-1 rounded inline-block mb-1">Phase 1</p>
                        <p class="font-bold text-gray-800 text-sm">环境配置</p>
                        <p class="text-[10px] text-gray-400 mt-1">IRS平台调研<br>本地环境搭建</p>
                    </div>
                </div>

                <!-- Point 2: Phase 2 (Bottom) -->
                <div class="absolute -top-3 left-[25%] flex flex-col items-center group">
                    <div class="w-6 h-6 bg-szu-gold rounded-full border-4 border-white shadow-md z-10 transition-transform group-hover:scale-125"></div>
                    <!-- Label Box (Bottom) -->
                    <div class="absolute top-6 w-40 text-center pt-4 border-l border-dashed border-gray-300 h-16 flex flex-col justify-start">
                        <p class="font-bold text-gray-800 text-sm mb-1">数据工程</p>
                        <p class="text-[10px] text-gray-400 mb-1">SQL数据提取<br>清洗与预处理</p>
                        <p class="font-bold text-szu-gold text-xs bg-yellow-50 px-2 py-1 rounded inline-block">Phase 2</p>
                    </div>
                </div>

                <!-- Point 3: Phase 3 (Top) -->
                <div class="absolute -top-3 left-[50%] flex flex-col items-center group">
                    <div class="w-6 h-6 bg-szu-dark rounded-full border-4 border-white shadow-md z-10 transition-transform group-hover:scale-125"></div>
                    <!-- Label Box (Top) -->
                    <div class="absolute bottom-6 w-40 text-center pb-4 border-l border-dashed border-gray-300 h-16 flex flex-col justify-end">
                        <p class="font-bold text-szu-dark text-xs bg-gray-100 px-2 py-1 rounded inline-block mb-1">Phase 3</p>
                        <p class="font-bold text-gray-800 text-sm">策略开发</p>
                        <p class="text-[10px] text-gray-400 mt-1">因子向量化计算<br>LightGBM 建模</p>
                    </div>
                </div>

                <!-- Point 4: Phase 4 (Bottom) -->
                <div class="absolute -top-3 left-[75%] flex flex-col items-center group">
                    <div class="w-6 h-6 bg-blue-500 rounded-full border-4 border-white shadow-md z-10 transition-transform group-hover:scale-125"></div>
                     <!-- Label Box (Bottom) -->
                     <div class="absolute top-6 w-40 text-center pt-4 border-l border-dashed border-gray-300 h-16 flex flex-col justify-start">
                        <p class="font-bold text-gray-800 text-sm mb-1">回测优化</p>
                        <p class="text-[10px] text-gray-400 mb-1">策略回测运行<br>超参数调优</p>
                        <p class="font-bold text-blue-600 text-xs bg-blue-50 px-2 py-1 rounded inline-block">Phase 4</p>
                    </div>
                </div>

                <!-- Point 5: Phase 5 (Top) -->
                <div class="absolute -top-3 right-0 flex flex-col items-center group">
                    <div class="w-6 h-6 bg-green-500 rounded-full border-4 border-white shadow-md z-10 transition-transform group-hover:scale-125"></div>
                    <!-- Label Box (Top) -->
                    <div class="absolute bottom-6 w-40 text-right pb-4 border-r border-dashed border-gray-300 h-16 flex flex-col justify-end items-end pr-2">
                         <p class="font-bold text-green-600 text-xs bg-green-50 px-2 py-1 rounded inline-block mb-1">Phase 5</p>
                        <p class="font-bold text-gray-800 text-sm">交付汇报</p>
                        <p class="text-[10px] text-gray-400 mt-1">可视化报告生成<br>最终PPT制作</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="page-number">17</div>
    </div>

    <!-- ==========================================
         Slide 18: 结束页
         ========================================== -->
    <div class="slide flex flex-col items-center justify-center bg-gradient-to-br from-[#1e1e2e] to-[#2d2d44] text-white overflow-hidden relative">
        <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5"></div>
        <div class="text-center z-10 animate-fade-in-up">
            <h2 class="text-5xl font-extrabold mb-8 tracking-wide">感谢聆听</h2>
            <p class="text-xl font-light text-szu-gold tracking-[0.2em] mb-12 border-b border-szu-gold/30 inline-block pb-2">Q & A</p>
            <p class="text-xs text-white/40 mt-8 tracking-widest">SHENZHEN UNIVERSITY</p>
        </div>
        <div class="page-number text-white/20">18</div>
    </div>
"""

# JS Logic with Chinese & Fixes
js_content = """
        // ==========================================
        //  Data & Rendering Logic
        // ==========================================
    
        // Parse the embedded data
        const data = pptData; // Injected variable

        // --- Chart 1: Net Value ---
        if (document.getElementById('chart-nav')) {
            const traceLGBM = {
                x: data.dates,
                y: data.nav_lgbm,
                type: 'scatter',
                mode: 'lines',
                name: 'LightGBM 策略',
                line: { color: '#9F1F35', width: 2 } // SZU Red
            };
            
            const traceBench = {
                x: data.dates,
                y: data.nav_bench,
                type: 'scatter',
                mode: 'lines',
                name: '沪深300 基准',
                line: { color: '#9ca3af', width: 1.5, dash: 'dot' } // Gray
            };

            const layout = {
                margin: { t: 10, r: 10, l: 30, b: 20 },
                showlegend: true,
                legend: { x: 0, y: 1 },
                xaxis: { showgrid: false },
                yaxis: { title: '', gridcolor: '#F3F4F6', showticklabels: true },
                hovermode: 'x unified',
                autosize: true
            };

            Plotly.newPlot('chart-nav', [traceBench, traceLGBM], layout, {responsive: true, displayModeBar: false});
        }

        // --- Chart 2: Drawdown ---
        if (document.getElementById('chart-drawdown')) {
            const traceDD = {
                x: data.dates,
                y: data.drawdown_lgbm,
                type: 'scatter',
                fill: 'tozeroy', // Fill to zero
                mode: 'lines',
                name: '最大回撤',
                line: { color: '#ef4444', width: 1 },
                fillcolor: 'rgba(239, 68, 68, 0.1)'
            };

            const layoutDD = {
                margin: { t: 10, r: 10, l: 30, b: 20 },
                xaxis: { showgrid: false },
                yaxis: { title: '', gridcolor: '#F3F4F6', tickformat: '.0%' },
                hovermode: 'x unified',
                autosize: true
            };

            Plotly.newPlot('chart-drawdown', [traceDD], layoutDD, {responsive: true, displayModeBar: false});
        }

        // --- Chart 3: Heatmap ---
        if (document.getElementById('chart-heatmap')) {
            const traceHeat = {
                z: data.heatmap.z,
                x: data.heatmap.months,
                y: data.heatmap.years,
                type: 'heatmap',
                colorscale: [
                    [0, 'rgba(239, 68, 68, 0.1)'], 
                    [0.5, 'rgba(239, 68, 68, 0.5)'], 
                    [1, '#9F1F35']
                ],
                text: data.heatmap.text,
                hovertransport: 'z',
                showscale: true
            };
            
            const layoutHeat = {
                margin: { t: 10, r: 0, l: 30, b: 0 },
                xaxis: { side: 'top' },
                yaxis: { title: '' },
                autosize: true
            };
            
            Plotly.newPlot('chart-heatmap', [traceHeat], layoutHeat, {responsive: true, displayModeBar: false});
        }

        // --- Chart 4: Distribution ---
        if (document.getElementById('chart-dist')) {
            const traceDist = {
                x: data.distribution,
                type: 'histogram',
                marker: { color: '#C49453', opacity: 0.8 },
                name: '收益分布'
            };
            
            const layoutDist = {
                margin: { t: 10, r: 10, l: 30, b: 30 },
                xaxis: { title: '日收益率', tickformat: '.1%' },
                yaxis: { title: '频次' },
                autosize: true,
                shapes: [{
                    type: 'line',
                    x0: 0, x1: 0,
                    y0: 0, y1: 1,
                    yref: 'paper',
                    line: { color: '#979797', width: 1.5, dash: 'dash'}
                }]
            };
            
            Plotly.newPlot('chart-dist', [traceDist], layoutDist, {responsive: true, displayModeBar: false});
        }
"""


def merge():
    print("Reading HTML file...")
    with open(html_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(data_path, 'r', encoding='utf-8') as f:
        json_data = f.read()

    # 1. Prepare JS Logic with Data
    js_final = f"const pptData = {json_data};\n" + js_content

    # 2. Find Slides 6-18 Range
    start_idx = -1
    end_idx = -1
    
    # Locate Start (Slide 6)
    for i, line in enumerate(lines):
        if "Slide 6: 因子体系" in line:
            # We assume the block starts 1 line before this (the <!-- line)
            # Verify if line i-1 has <!--
            if i > 0 and "<!--" in lines[i-1]:
                start_idx = i - 1
            else:
                # Fallback: Just start here
                start_idx = i
            print(f"Found Slide 6 at line {start_idx}")
            break
            
    # If Slide 6 not found, look for placeholder
    if start_idx == -1:
        for i, line in enumerate(lines):
            if "<!-- More slides will be added here -->" in line:
                start_idx = i
                # For placeholder, we replace just that line, so end_idx is i+1
                end_idx = i + 1
                print(f"Found placeholder at line {start_idx}")
                break
    
    # Locate End (Start of Script tag after Slide 6)
    if start_idx != -1 and end_idx == -1:
        for i in range(start_idx + 1, len(lines)):
            if "<script" in lines[i] or "// Data and Plot Logic" in lines[i]:
                # Found the script section after slides
                end_idx = i
                print(f"Found end of slides at line {end_idx}")
                break
    
    # Perform Slide Replacement
    if start_idx != -1 and end_idx != -1:
        print(f"Replacing lines {start_idx} to {end_idx} with new slides...")
        new_lines = lines[:start_idx] + [slides_html + "\n"] + lines[end_idx:]
        lines = new_lines
    else:
        print("ERROR: Could not find insertion point for Slides 6-18.")
        # Fallback to appending if totally lost? No, dangerous.
    
    # 3. Update JS Content
    # We now have the `lines` with new slides. Now update JS.
    # The JS is typically at the end. We need to find the block.
    # We can join to string to use regex for JS which is easier, or replace the whole script block.
    
    content = "".join(lines)
    
    # Regex to replace existing JS block (const pptData ... end of script)
    # The block ends usually with </script>. 
    # But wait, looking at file content in step 170:
    # Top of file has CDNs. We don't want to replace those.
    # The custom script is at the bottom.
    # It contains `const pptData = ...` OR `// Data and Plot Logic will go here`
    
    import re
    if 'const pptData =' in content:
        print("Updating existing JS data/logic...")
        # Pattern: const pptData = ... (until </script>)
        # Be careful not to eat </script> tag
        pattern = r'const pptData =[\s\S]*?(?=</script>)'
        content = re.sub(pattern, js_final, content, count=1)
    elif '// Data and Plot Logic will go here' in content:
        print("Injecting JS into placeholder...")
        content = content.replace('// Data and Plot Logic will go here', js_final)
    else:
        # If we just inserted slides, maybe the JS block is now inside `slides_html`? NO.
        # `slides_html` is just HTML divs.
        # We need to inject JS. 
        # If we can't find the markers, we might append it before </body>
        print("Warning: JS marker not found. Appending script to body.")
        content = content.replace('</body>', f'<script>\n{js_final}\n</script>\n</body>')
        
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Merge successfully completed.")


if __name__ == "__main__":
    merge()
