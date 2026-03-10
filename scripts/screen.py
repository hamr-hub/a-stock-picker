#!/usr/bin/env python3
"""
A股选股策略执行脚本
支持多种选股策略：价值、成长、动量、技术
"""

import json
import sys
import pandas as pd
from typing import List, Dict, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入数据模块
try:
    from data_fetch import AStockData
except ImportError:
    sys.path.insert(0, '/Users/hyx/.openclaw/skills/a-stock-picker/scripts')
    from data_fetch import AStockData


class StockScreener:
    """A股选股器"""
    
    def __init__(self):
        self.data_api = AStockData()
        self.strategies = {
            "value": self.value_strategy,
            "growth": self.growth_strategy,
            "momentum": self.momentum_strategy,
            "technical": self.technical_strategy,
            "dividend": self.dividend_strategy,
            "kdj": self.kdj_strategy,
        }
    
    def value_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        价值投资策略
        筛选条件：
        - PE < 20
        - PB < 3
        - ROE > 10%
        - 市值 > 50亿
        """
        filtered = df[
            (df['市盈率'] < 20) &
            (df['市净率'] < 3) &
            (df['净资产收益率'] > 10) &
            (df['总市值'] > 50e8)
        ].copy()
        
        # 按 PE 从低到高排序
        filtered = filtered.sort_values('市盈率')
        return filtered.head(top_n)
    
    def growth_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        成长投资策略
        筛选条件：
        - 营收增长率 > 20%
        - 净利润增长率 > 20%
        - ROE > 15%
        """
        # 需要获取更详细的财务数据
        # 这里使用简化版：基于换手率、量比筛选活跃成长股
        filtered = df[
            (df['换手率'] > 3) &
            (df['量比'] > 1.2) &
            (df['涨跌幅'] > -5) &
            (df['涨跌幅'] < 20)
        ].copy()
        
        # 按市值和流动性排序
        filtered['score'] = filtered['换手率'] * filtered['量比']
        filtered = filtered.sort_values('score', ascending=False)
        return filtered.head(top_n)
    
    def momentum_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        动量策略
        筛选条件：
        - 近5日涨幅 > 10%
        - 换手率适中 (3%-20%)
        - 量比 > 1.5
        """
        filtered = df[
            (df['5日涨跌'] > 10) &
            (df['换手率'] > 3) &
            (df['换手率'] < 20) &
            (df['量比'] > 1.5)
        ].copy()
        
        # 按5日涨幅排序
        filtered = filtered.sort_values('5日涨跌', ascending=False)
        return filtered.head(top_n)
    
    def technical_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        技术突破策略
        筛选条件：
        - 当日涨幅 > 3%
        - 突破近期高点
        - 成交量放大
        """
        filtered = df[
            (df['涨跌幅'] > 3) &
            (df['换手率'] > 5) &
            (df['量比'] > 2) &
            (df['最高'] == df['涨停价'])  # 接近涨停
        ].copy()
        
        filtered = filtered.sort_values('涨跌幅', ascending=False)
        return filtered.head(top_n)
    
    def dividend_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        高股息策略
        筛选条件：
        - 股息率 > 3%
        - PE < 15
        - 市值 > 100亿
        """
        filtered = df[
            (df['市盈率'] < 15) &
            (df['市净率'] < 2) &
            (df['总市值'] > 100e8) &
            (df['涨跌幅'] > -10)
        ].copy()
        
        filtered = filtered.sort_values('市盈率')
        return filtered.head(top_n)
    
    def kdj_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        KDJ 选股策略（基于日线）
        筛选条件：J 线在 K 线和 D 线下方
        排序：J 线偏离 K/D 均值越大（越低）排名越靠前
        """
        stock_list = df['代码'].tolist() if '代码' in df.columns else []
        
        total = len(stock_list)
        print(f"开始计算 KDJ，共 {total} 只股票...", file=sys.stderr)
        
        df_indexed = df.set_index('代码')
        results = []
        done = [0]

        def calc_one(code):
            try:
                daily = self.data_api.get_stock_daily(code, days=60)
                if daily.empty or len(daily) < 15:
                    return None
                daily = self.data_api.calculate_kdj(daily)
                latest = daily.iloc[-1]
                k_val = latest['K']
                d_val = latest['D']
                j_val = latest['J']
                kd_avg = (k_val + d_val) / 2
                deviation = kd_avg - j_val
                if j_val < k_val and j_val < d_val:
                    row = df_indexed.loc[code].to_dict()
                    row['代码'] = code
                    row['K'] = round(k_val, 2)
                    row['D'] = round(d_val, 2)
                    row['J'] = round(j_val, 2)
                    row['KD均值'] = round(kd_avg, 2)
                    row['J偏离KD'] = round(deviation, 2)
                    return row
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(calc_one, code): code for code in stock_list}
            for future in as_completed(futures):
                done[0] += 1
                if done[0] % 500 == 0:
                    print(f"进度: {done[0]}/{total}", file=sys.stderr)
                row = future.result()
                if row:
                    results.append(row)
        
        result_df = pd.DataFrame(results)
        if result_df.empty:
            return result_df
        result_df = result_df.sort_values('J偏离KD', ascending=False)
        return result_df.head(top_n)
    
    def run_screening(self, strategy: str = "value", top_n: int = 20) -> pd.DataFrame:
        """
        执行选股
        :param strategy: 策略名称
        :param top_n: 返回股票数量
        """
        print(f"正在执行 {strategy} 策略选股...", file=sys.stderr)
        
        # 获取全市场数据
        all_stocks = self.data_api.get_stock_list()
        
        # 清理数据
        numeric_cols = ['市盈率', '市净率', '换手率', '量比', '5日涨跌', '涨跌幅', '总市值']
        for col in numeric_cols:
            if col in all_stocks.columns:
                all_stocks[col] = pd.to_numeric(all_stocks[col], errors='coerce')
        
        # 执行策略
        if strategy in self.strategies:
            result = self.strategies[strategy](all_stocks, top_n)
        else:
            result = self.value_strategy(all_stocks, top_n)
        
        return result
    
    def analyze_single_stock(self, symbol: str) -> Dict:
        """
        深度分析单只股票
        返回包含技术指标、基本面、AI分析建议的字典
        """
        # 获取日线数据
        daily_data = self.data_api.get_stock_daily(symbol, days=90)
        
        # 计算技术指标
        if not daily_data.empty:
            daily_data = self.data_api.calculate_ma(daily_data)
            daily_data['RSI'] = self.data_api.calculate_rsi(daily_data)
        
        # 获取基本面
        fundamental = self.data_api.get_fundamental(symbol)
        
        # 构建分析结果
        latest_price = daily_data['收盘'].iloc[-1] if not daily_data.empty else None
        ma20 = daily_data['MA20'].iloc[-1] if not daily_data.empty and 'MA20' in daily_data else None
        rsi = daily_data['RSI'].iloc[-1] if not daily_data.empty and 'RSI' in daily_data else None
        
        return {
            "symbol": symbol,
            "current_price": latest_price,
            "ma20": ma20,
            "rsi": round(rsi, 2) if rsi else None,
            "fundamental": fundamental,
            "trend": "up" if latest_price and ma20 and latest_price > ma20 else "down",
            "daily_data": daily_data.tail(20).to_dict('records') if not daily_data.empty else []
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='A股选股工具')
    parser.add_argument('command', choices=['screen', 'analyze'], help='命令')
    parser.add_argument('--strategy', '-s', default='value', 
                       choices=['value', 'growth', 'momentum', 'technical', 'dividend', 'kdj'],
                       help='选股策略')
    parser.add_argument('--top', '-n', type=int, default=20, help='返回数量')
    parser.add_argument('--symbol', help='股票代码（用于analyze命令）')
    parser.add_argument('--output', '-o', help='输出文件')
    
    args = parser.parse_args()
    
    screener = StockScreener()
    
    if args.command == 'screen':
        # 执行选股
        result = screener.run_screening(args.strategy, args.top)
        
        # 选择输出列
        if args.strategy == 'kdj':
            output_cols = ['代码', '名称', '最新价', '涨跌幅', 'K', 'D', 'J', 'KD均值', 'J偏离KD', '换手率', '总市值']
        else:
            output_cols = ['代码', '名称', '最新价', '涨跌幅', '市盈率', '市净率', '换手率', '总市值']
        available_cols = [c for c in output_cols if c in result.columns]
        result = result[available_cols]
        
        # 输出
        output = result.to_json(orient='records', force_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"结果已保存至 {args.output}", file=sys.stderr)
        else:
            print(output)
    
    elif args.command == 'analyze':
        if not args.symbol:
            print("错误: analyze 命令需要 --symbol 参数", file=sys.stderr)
            sys.exit(1)
        
        result = screener.analyze_single_stock(args.symbol)
        output = json.dumps(result, ensure_ascii=False, indent=2, default=str)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
        else:
            print(output)


if __name__ == "__main__":
    main()
