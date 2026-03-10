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
        # 字段映射（兼容不同数据源）
        col_map = {
            '市盈率': ['市盈率', 'PE', 'pe', '市盈(静)', '市盈(动)'],
            '市净率': ['市净率', 'PB', 'pb'],
            '净资产收益率': ['净资产收益率', 'ROE', 'roe'],
            '总市值': ['总市值', '总市值(亿)', 'total_mv']
        }
        
        # 找到实际存在的列名
        pe_col = next((c for c in col_map['市盈率'] if c in df.columns), None)
        pb_col = next((c for c in col_map['市净率'] if c in df.columns), None)
        roe_col = next((c for c in col_map['净资产收益率'] if c in df.columns), None)
        mv_col = next((c for c in col_map['总市值'] if c in df.columns), None)
        
        # 构建筛选条件
        conditions = pd.Series([True] * len(df))
        if pe_col:
            conditions &= (df[pe_col] < 20) & (df[pe_col] > 0)
        if pb_col:
            conditions &= (df[pb_col] < 3) & (df[pb_col] > 0)
        if roe_col:
            conditions &= (df[roe_col] > 10)
        if mv_col:
            mv_threshold = 50e8 if df[mv_col].max() > 1e9 else 50
            conditions &= (df[mv_col] > mv_threshold)
        
        filtered = df[conditions].copy()
        
        # 按 PE 从低到高排序
        if pe_col:
            filtered = filtered.sort_values(pe_col)
        return filtered.head(top_n)
    
    def growth_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        成长投资策略
        筛选条件：
        - 营收增长率 > 20%
        - 净利润增长率 > 20%
        - ROE > 15%
        """
        # 字段映射
        col_map = {
            '换手率': ['换手率', 'turnover', 'HSL'],
            '量比': ['量比', 'volume_ratio', 'LB'],
            '涨跌幅': ['涨跌幅', 'change', '涨跌幅(%)']
        }
        
        turnover_col = next((c for c in col_map['换手率'] if c in df.columns), None)
        volume_ratio_col = next((c for c in col_map['量比'] if c in df.columns), None)
        change_col = next((c for c in col_map['涨跌幅'] if c in df.columns), None)
        
        conditions = pd.Series([True] * len(df))
        if turnover_col:
            conditions &= (df[turnover_col] > 3)
        if volume_ratio_col:
            conditions &= (df[volume_ratio_col] > 1.2)
        if change_col:
            conditions &= (df[change_col] > -5) & (df[change_col] < 20)
        
        filtered = df[conditions].copy()
        
        # 按市值和流动性排序
        if turnover_col and volume_ratio_col:
            filtered['score'] = filtered[turnover_col] * filtered[volume_ratio_col]
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
        col_map = {
            '5日涨跌': ['5日涨跌', 'change_5d', '5日涨幅'],
            '换手率': ['换手率', 'turnover', 'HSL'],
            '量比': ['量比', 'volume_ratio', 'LB']
        }
        
        change_5d_col = next((c for c in col_map['5日涨跌'] if c in df.columns), None)
        turnover_col = next((c for c in col_map['换手率'] if c in df.columns), None)
        volume_ratio_col = next((c for c in col_map['量比'] if c in df.columns), None)
        
        conditions = pd.Series([True] * len(df))
        if change_5d_col:
            conditions &= (df[change_5d_col] > 10)
        if turnover_col:
            conditions &= (df[turnover_col] > 3) & (df[turnover_col] < 20)
        if volume_ratio_col:
            conditions &= (df[volume_ratio_col] > 1.5)
        
        filtered = df[conditions].copy()
        
        # 按5日涨幅排序
        if change_5d_col:
            filtered = filtered.sort_values(change_5d_col, ascending=False)
        return filtered.head(top_n)
    
    def technical_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        技术突破策略
        筛选条件：
        - 当日涨幅 > 3%
        - 突破近期高点
        - 成交量放大
        """
        col_map = {
            '涨跌幅': ['涨跌幅', 'change', '涨跌幅(%)'],
            '换手率': ['换手率', 'turnover', 'HSL'],
            '量比': ['量比', 'volume_ratio', 'LB'],
            '最高': ['最高', 'high', '最高价'],
            '涨停价': ['涨停价', 'limit_up', '涨停']
        }
        
        change_col = next((c for c in col_map['涨跌幅'] if c in df.columns), None)
        turnover_col = next((c for c in col_map['换手率'] if c in df.columns), None)
        volume_ratio_col = next((c for c in col_map['量比'] if c in df.columns), None)
        high_col = next((c for c in col_map['最高'] if c in df.columns), None)
        limit_up_col = next((c for c in col_map['涨停价'] if c in df.columns), None)
        
        conditions = pd.Series([True] * len(df))
        if change_col:
            conditions &= (df[change_col] > 3)
        if turnover_col:
            conditions &= (df[turnover_col] > 5)
        if volume_ratio_col:
            conditions &= (df[volume_ratio_col] > 2)
        if high_col and limit_up_col:
            conditions &= (df[high_col] == df[limit_up_col])
        
        filtered = df[conditions].copy()
        
        if change_col:
            filtered = filtered.sort_values(change_col, ascending=False)
        return filtered.head(top_n)
    
    def dividend_strategy(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        高股息策略
        筛选条件：
        - 股息率 > 3%
        - PE < 15
        - 市值 > 100亿
        """
        col_map = {
            '市盈率': ['市盈率', 'PE', 'pe', '市盈(静)', '市盈(动)'],
            '市净率': ['市净率', 'PB', 'pb'],
            '总市值': ['总市值', '总市值(亿)', 'total_mv'],
            '涨跌幅': ['涨跌幅', 'change', '涨跌幅(%)']
        }
        
        pe_col = next((c for c in col_map['市盈率'] if c in df.columns), None)
        pb_col = next((c for c in col_map['市净率'] if c in df.columns), None)
        mv_col = next((c for c in col_map['总市值'] if c in df.columns), None)
        change_col = next((c for c in col_map['涨跌幅'] if c in df.columns), None)
        
        conditions = pd.Series([True] * len(df))
        if pe_col:
            conditions &= (df[pe_col] < 15)
        if pb_col:
            conditions &= (df[pb_col] < 2)
        if mv_col:
            mv_threshold = 100e8 if df[mv_col].max() > 1e9 else 100
            conditions &= (df[mv_col] > mv_threshold)
        if change_col:
            conditions &= (df[change_col] > -10)
        
        filtered = df[conditions].copy()
        
        if pe_col:
            filtered = filtered.sort_values(pe_col)
        return filtered.head(top_n)
    
    def kdj_strategy(self, df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """
        KDJ 选股策略（基于日线，大盘股）
        筛选条件：
        - 大盘股：市值 >= 500亿
        - J 线在 K 线和 D 线下方
        排序：股价越高 + J线偏离KD越大 综合排名
        """
        mv_candidates = ['总市值', 'total_mv', '总市值(亿)']
        price_candidates = ['最新价', '收盘', 'close', '最新价格']
        mv_col = next((c for c in mv_candidates if c in df.columns), None)
        price_col = next((c for c in price_candidates if c in df.columns), None)

        filtered_df = df.copy()
        if mv_col:
            filtered_df[mv_col] = pd.to_numeric(filtered_df[mv_col], errors='coerce')
            max_mv = filtered_df[mv_col].max()
            mv_threshold = 500e8 if max_mv > 1e9 else 500
            filtered_df = filtered_df[filtered_df[mv_col] >= mv_threshold]

        stock_list = filtered_df['代码'].tolist() if '代码' in filtered_df.columns else []

        total = len(stock_list)
        print(f"大盘股（市值>=500亿）共 {total} 只，开始计算 KDJ...", file=sys.stderr)

        df_indexed = filtered_df.set_index('代码')
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
                if done[0] % 200 == 0:
                    print(f"进度: {done[0]}/{total}", file=sys.stderr)
                row = future.result()
                if row:
                    results.append(row)

        result_df = pd.DataFrame(results)
        if result_df.empty:
            return result_df

        if price_col and price_col in result_df.columns:
            result_df[price_col] = pd.to_numeric(result_df[price_col], errors='coerce')
            price_max = result_df[price_col].max()
            price_min = result_df[price_col].min()
            dev_max = result_df['J偏离KD'].max()
            dev_min = result_df['J偏离KD'].min()

            price_range = price_max - price_min if price_max != price_min else 1
            dev_range = dev_max - dev_min if dev_max != dev_min else 1

            result_df['price_norm'] = (result_df[price_col] - price_min) / price_range
            result_df['dev_norm'] = (result_df['J偏离KD'] - dev_min) / dev_range
            result_df['综合得分'] = result_df['price_norm'] * 0.5 + result_df['dev_norm'] * 0.5
            result_df = result_df.sort_values('综合得分', ascending=False)
            result_df = result_df.drop(columns=['price_norm', 'dev_norm', '综合得分'])
        else:
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
        
        # 可能的数值列（兼容不同数据源命名）
        numeric_cols_map = {
            '市盈率': ['市盈率', 'PE', 'pe', '市盈(静)', '市盈(动)'],
            '市净率': ['市净率', 'PB', 'pb'],
            '换手率': ['换手率', 'turnover', 'HSL'],
            '量比': ['量比', 'volume_ratio', 'LB'],
            '5日涨跌': ['5日涨跌', 'change_5d', '5日涨幅'],
            '涨跌幅': ['涨跌幅', 'change', '涨跌幅(%)'],
            '总市值': ['总市值', '总市值(亿)', 'total_mv']
        }
        
        # 清理数据
        for std_col, possible_cols in numeric_cols_map.items():
            actual_col = next((c for c in possible_cols if c in all_stocks.columns), None)
            if actual_col:
                all_stocks[actual_col] = pd.to_numeric(all_stocks[actual_col], errors='coerce')
        
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
            output_cols = ['代码', '名称', '最新价', '收盘', '涨跌幅', 'K', 'D', 'J', 'KD均值', 'J偏离KD', '换手率', '总市值']
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
