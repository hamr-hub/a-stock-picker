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
        KDJ 选股策略（日线+周线分别排行，大盘股）
        筛选条件：
        - 大盘股：市值 >= 500亿
        - 日线 J 线在 K/D 下方，选偏离最大的 top_n
        - 周线 J 线在 K/D 下方，选偏离最大的 top_n
        - 合并两个榜单（去重），附带来源标记
        """
        mv_candidates = ['总市值', 'total_mv', '总市值(亿)']
        mv_col = next((c for c in mv_candidates if c in df.columns), None)

        filtered_df = df.copy()
        if mv_col:
            filtered_df[mv_col] = pd.to_numeric(filtered_df[mv_col], errors='coerce')
            max_mv = filtered_df[mv_col].max()
            mv_threshold = 500e8 if max_mv > 1e9 else 500
            filtered_df = filtered_df[filtered_df[mv_col] >= mv_threshold]

        stock_list = filtered_df['代码'].tolist() if '代码' in filtered_df.columns else []

        total = len(stock_list)
        print(f"大盘股（市值>=500亿）共 {total} 只，开始计算日线+周线 KDJ...", file=sys.stderr)

        df_indexed = filtered_df.set_index('代码')
        daily_results = []
        weekly_results = []
        done = [0]

        def calc_one(code):
            try:
                daily = self.data_api.get_stock_daily(code, days=60)
                weekly = self.data_api.get_stock_weekly(code, days=180)

                d_row = None
                w_row = None
                base = df_indexed.loc[code].to_dict()
                base['代码'] = code

                if not daily.empty and len(daily) >= 15:
                    daily = self.data_api.calculate_kdj(daily)
                    d = daily.iloc[-1]
                    dk, dd, dj = d['K'], d['D'], d['J']
                    if dj < dk and dj < dd:
                        d_row = dict(base)
                        d_row['日K'] = round(dk, 2)
                        d_row['日D'] = round(dd, 2)
                        d_row['日J'] = round(dj, 2)
                        d_row['日J偏离KD'] = round((dk + dd) / 2 - dj, 2)

                if not weekly.empty and len(weekly) >= 9:
                    weekly = self.data_api.calculate_kdj(weekly)
                    w = weekly.iloc[-1]
                    wk, wd, wj = w['K'], w['D'], w['J']
                    if wj < wk and wj < wd:
                        w_row = dict(base)
                        w_row['周K'] = round(wk, 2)
                        w_row['周D'] = round(wd, 2)
                        w_row['周J'] = round(wj, 2)
                        w_row['周J偏离KD'] = round((wk + wd) / 2 - wj, 2)

                return d_row, w_row
            except Exception:
                pass
            return None, None

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(calc_one, code): code for code in stock_list}
            for future in as_completed(futures):
                done[0] += 1
                if done[0] % 200 == 0:
                    print(f"进度: {done[0]}/{total}", file=sys.stderr)
                d_row, w_row = future.result()
                if d_row:
                    daily_results.append(d_row)
                if w_row:
                    weekly_results.append(w_row)

        daily_df = pd.DataFrame(daily_results)
        weekly_df = pd.DataFrame(weekly_results)

        if daily_df.empty and weekly_df.empty:
            return pd.DataFrame()

        top_daily = pd.DataFrame()
        top_weekly = pd.DataFrame()

        if not daily_df.empty:
            top_daily = daily_df.sort_values('日J偏离KD', ascending=False).head(top_n).copy()
            top_daily['来源'] = '日线'

        if not weekly_df.empty:
            top_weekly = weekly_df.sort_values('周J偏离KD', ascending=False).head(top_n).copy()
            top_weekly['来源'] = '周线'

        merged = pd.concat([top_daily, top_weekly], ignore_index=True)

        seen = set()
        deduped = []
        for _, row in merged.iterrows():
            code = row['代码']
            if code in seen:
                idx = next(i for i, r in enumerate(deduped) if r['代码'] == code)
                deduped[idx]['来源'] = '日线+周线'
                d_dev = row.get('日J偏离KD', deduped[idx].get('日J偏离KD', 0))
                w_dev = row.get('周J偏离KD', deduped[idx].get('周J偏离KD', 0))
                for k, v in row.items():
                    if pd.notna(v) and k not in deduped[idx]:
                        deduped[idx][k] = v
                    elif pd.notna(v) and k in ('日K', '日D', '日J', '日J偏离KD', '周K', '周D', '周J', '周J偏离KD'):
                        deduped[idx][k] = v
            else:
                seen.add(code)
                deduped.append(row.to_dict())

        result_df = pd.DataFrame(deduped)

        daily_rank = {row['代码']: i for i, (_, row) in enumerate(top_daily.iterrows())} if not top_daily.empty else {}
        weekly_rank = {row['代码']: i for i, (_, row) in enumerate(top_weekly.iterrows())} if not top_weekly.empty else {}

        def sort_key(row):
            code = row['代码']
            dr = daily_rank.get(code, top_n)
            wr = weekly_rank.get(code, top_n)
            return min(dr, wr)

        result_df['_sort'] = result_df.apply(sort_key, axis=1)
        result_df = result_df.sort_values('_sort').drop(columns=['_sort'])

        return result_df
    
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
            output_cols = ['代码', '名称', '来源', '最新价', '收盘', '涨跌幅', '日K', '日D', '日J', '日J偏离KD', '周K', '周D', '周J', '周J偏离KD', '换手率', '总市值']
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
