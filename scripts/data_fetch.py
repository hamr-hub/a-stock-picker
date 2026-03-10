#!/usr/bin/env python3
"""
A股数据获取模块 - 基于 AKShare
支持：股票列表、基本面、技术指标、财务数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import json

class AStockData:
    """A股数据获取类"""
    
    @staticmethod
    def get_stock_list() -> pd.DataFrame:
        """获取 A股所有股票列表"""
        df = ak.stock_zh_a_spot_em()
        
        # 列名标准化映射（处理 AKShare 不同版本的列名差异）
        column_mapping = {
            '市盈率': ['市盈率', '市盈率(动态)', '市盈率(TTM)', 'pe'],
            '市净率': ['市净率', '市净率(静态)', 'pb'],
            '换手率': ['换手率', '换手率(%)', 'turnover'],
            '量比': ['量比', 'volume_ratio', 'qr'],
            '涨跌幅': ['涨跌幅', '涨跌幅(%)', 'change_percent'],
            '最新价': ['最新价', '最新价(元)', 'close', 'price'],
            '总市值': ['总市值', '总市值(元)', 'market_cap'],
            '流通市值': ['流通市值', '流通市值(元)', 'float_cap'],
            '成交额': ['成交额', '成交额(元)', 'amount'],
            '成交量': ['成交量', 'volume'],
            '最高': ['最高', '最高价', 'high'],
            '最低': ['最低', '最低价', 'low'],
            '今开': ['今开', '开盘价', 'open'],
            '昨收': ['昨收', '昨收价', 'previous_close'],
        }
        
        for standard_name, possible_names in column_mapping.items():
            for name in possible_names:
                if name in df.columns and standard_name not in df.columns:
                    df[standard_name] = df[name]
                    break
        
        return df
    
    @staticmethod
    def get_stock_daily(symbol: str, days: int = 60) -> pd.DataFrame:
        """
        获取个股日线数据
        :param symbol: 股票代码, 如 "000001"
        :param days: 获取天数
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq"  # 前复权
        )
        return df
    
    @staticmethod
    def get_fundamental(symbol: str) -> dict:
        """
        获取个股基本面数据
        :param symbol: 股票代码
        """
        try:
            # 主要指标
            indicator = ak.stock_financial_analysis_indicator(symbol=symbol)
            
            # 最新一期数据
            latest = indicator.iloc[0] if not indicator.empty else {}
            
            return {
                "symbol": symbol,
                "pe": latest.get("市盈率", None),
                "pb": latest.get("市净率", None),
                "roe": latest.get("净资产收益率", None),
                "revenue_growth": latest.get("营业收入增长率", None),
                "profit_growth": latest.get("净利润增长率", None),
                "debt_ratio": latest.get("资产负债率", None),
                "gross_margin": latest.get("销售毛利率", None),
            }
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}
    
    @staticmethod
    def get_industry_stocks(industry: str) -> pd.DataFrame:
        """
        获取行业板块成分股
        :param industry: 行业名称, 如 "半导体"
        """
        df = ak.stock_board_industry_cons_em(symbol=industry)
        return df
    
    @staticmethod
    def get_hot_sectors() -> pd.DataFrame:
        """获取热门板块/行业涨幅排行"""
        df = ak.stock_board_industry_name_em()
        return df
    
    @staticmethod
    def get_limit_up_stocks() -> pd.DataFrame:
        """获取今日涨停股票"""
        df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        return df
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """计算移动平均线"""
        for period in periods:
            df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
        return df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算 RSI 指标"""
        delta = df['收盘'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算 KDJ 指标"""
        low_min = df['最低'].rolling(window=n).min()
        high_max = df['最高'].rolling(window=n).max()
        rsv = (df['收盘'] - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)
        k = rsv.ewm(com=m1 - 1, adjust=False).mean()
        d = k.ewm(com=m2 - 1, adjust=False).mean()
        j = 3 * k - 2 * d
        df['K'] = k
        df['D'] = d
        df['J'] = j
        return df

    @staticmethod
    def get_news_sentiment(symbol: str) -> List[dict]:
        """
        获取个股新闻（用于情绪分析）
        :param symbol: 股票代码
        """
        try:
            news = ak.stock_news_em(symbol=symbol)
            # 返回最近5条新闻
            return news.head(5).to_dict('records')
        except:
            return []


def save_to_json(data: dict, filename: str):
    """保存数据到 JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def main():
    """命令行入口"""
    import sys
    
    api = AStockData()
    
    if len(sys.argv) < 2:
        print("Usage: python data_fetch.py <command> [args]")
        print("Commands:")
        print("  list                    - 获取所有股票列表")
        print("  daily <symbol> [days]   - 获取个股日线数据")
        print("  fundamental <symbol>    - 获取基本面数据")
        print("  hot                     - 获取热门板块")
        print("  limitup                 - 获取涨停股票")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        df = api.get_stock_list()
        print(df.to_json(orient='records', force_ascii=False))
    
    elif cmd == "daily" and len(sys.argv) >= 3:
        symbol = sys.argv[2]
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        df = api.get_stock_daily(symbol, days)
        print(df.to_json(orient='records', force_ascii=False))
    
    elif cmd == "fundamental" and len(sys.argv) >= 3:
        symbol = sys.argv[2]
        data = api.get_fundamental(symbol)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    
    elif cmd == "hot":
        df = api.get_hot_sectors()
        print(df.to_json(orient='records', force_ascii=False))
    
    elif cmd == "limitup":
        df = api.get_limit_up_stocks()
        print(df.to_json(orient='records', force_ascii=False))


if __name__ == "__main__":
    main()
