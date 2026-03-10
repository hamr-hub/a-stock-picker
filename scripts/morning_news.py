#!/usr/bin/env python3
"""
A股早间资讯收集模块
收集：重大新闻、涨停预告、热门板块、北向资金流向
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import json

class MorningNewsCollector:
    """早间资讯收集器"""
    
    def __init__(self):
        self.today = datetime.now()
        self.date_str = self.today.strftime("%Y%m%d")
    
    def get_major_news(self) -> list:
        """获取财经重大新闻"""
        try:
            # 东方财富财经新闻
            news = ak.stock_news_em(symbol="")
            # 取最近20条
            recent_news = news.head(20)
            return recent_news.to_dict('records')
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_limit_up_preview(self) -> list:
        """获取涨停预测/昨日涨停表现"""
        try:
            # 昨日涨停股今日表现
            zt_pool = ak.stock_zt_pool_previous_em(date=self.date_str)
            # 筛选今日表现好的
            if '涨跌幅' in zt_pool.columns:
                strong = zt_pool[zt_pool['涨跌幅'] > 0].head(10)
                return strong.to_dict('records')
            return zt_pool.head(10).to_dict('records')
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_hot_sectors(self) -> list:
        """获取热门板块涨幅排行"""
        try:
            sectors = ak.stock_board_industry_name_em()
            # 按涨幅排序
            if '涨跌幅' in sectors.columns:
                sectors = sectors.sort_values('涨跌幅', ascending=False)
            return sectors.head(10).to_dict('records')
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_north_flow(self) -> dict:
        """获取北向资金流向"""
        try:
            # 使用 stock_hsgt_hist_em 获取北向资金历史数据
            flow = ak.stock_hsgt_hist_em(symbol="北向资金")
            if not flow.empty:
                latest = flow.iloc[0]
                # 尝试多种可能的列名
                net_amount = latest.get('当日资金流入', latest.get('净流入', latest.get('净买入', 0)))
                return {
                    "date": latest.get('日期', ''),
                    "total_net": float(net_amount) if net_amount else 0,
                    "trend": "流入" if float(net_amount) > 0 else "流出" if net_amount else "未知"
                }
        except Exception as e:
            pass
        
        # 备用方案：尝试分别获取沪股通和深股通
        try:
            sh_flow = ak.stock_hsgt_hist_em(symbol="沪股通")
            sz_flow = ak.stock_hsgt_hist_em(symbol="深股通")
            
            sh_net = 0
            sz_net = 0
            latest_date = ""
            
            if not sh_flow.empty:
                latest_sh = sh_flow.iloc[0]
                sh_net = float(latest_sh.get('当日资金流入', latest_sh.get('净流入', 0)) or 0)
                latest_date = latest_sh.get('日期', '')
            
            if not sz_flow.empty:
                latest_sz = sz_flow.iloc[0]
                sz_net = float(latest_sz.get('当日资金流入', latest_sz.get('净流入', 0)) or 0)
            
            total = sh_net + sz_net
            return {
                "date": latest_date,
                "shanghai_net": sh_net,
                "shenzhen_net": sz_net,
                "total_net": total,
                "trend": "流入" if total > 0 else "流出" if total < 0 else "持平"
            }
        except Exception as e:
            return {"error": str(e), "total_net": 0, "trend": "未知"}
    
    def get_pre_market_auction(self) -> list:
        """获取集合竞价数据（9:15-9:25）"""
        try:
            # 早盘集合竞价情况
            spot = ak.stock_zh_a_spot_em()
            # 筛选高开的股票
            if '涨跌幅' in spot.columns:
                gap_up = spot[spot['涨跌幅'] > 2].sort_values('涨跌幅', ascending=False)
                return gap_up.head(15).to_dict('records')
            return []
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_overnight_us_stocks(self) -> dict:
        """获取隔夜美股中概股表现"""
        try:
            us_chinese = ak.stock_us_zh_spot()
            # 计算平均涨跌幅
            if '涨跌幅' in us_chinese.columns:
                avg_change = us_chinese['涨跌幅'].mean()
                top_gainers = us_chinese.sort_values('涨跌幅', ascending=False).head(5)
                return {
                    "avg_change": round(avg_change, 2),
                    "top_gainers": top_gainers[['名称', '涨跌幅']].to_dict('records'),
                    "sentiment": "积极" if avg_change > 0 else "谨慎"
                }
        except Exception as e:
            return {"error": str(e)}
    
    def compile_report(self) -> dict:
        """编译完整早间报告"""
        print(f"[{datetime.now()}] 开始收集资讯...")
        
        report = {
            "date": self.today.strftime("%Y-%m-%d"),
            "time": self.today.strftime("%H:%M"),
            "sections": {
                "market_sentiment": self.get_overnight_us_stocks(),
                "north_flow": self.get_north_flow(),
                "hot_sectors": self.get_hot_sectors(),
                "pre_market": self.get_pre_market_auction(),
                "limit_up_preview": self.get_limit_up_preview(),
            }
        }
        
        print(f"[{datetime.now()}] 资讯收集完成")
        return report
    
    def format_kim_message(self, report: dict) -> str:
        """格式化为 Kim 消息格式"""
        today = report['date']
        
        # 隔夜美股情绪
        us_data = report['sections']['market_sentiment']
        us_sentiment = us_data.get('sentiment', '中性') if isinstance(us_data, dict) else '未知'
        us_change = us_data.get('avg_change', 0) if isinstance(us_data, dict) else 0
        
        # 北向资金
        north = report['sections']['north_flow']
        north_trend = north.get('trend', '未知') if isinstance(north, dict) else '未知'
        north_amount = north.get('total_net', 0) if isinstance(north, dict) else 0
        
        # 热门板块
        hot_sectors = report['sections']['hot_sectors']
        sector_text = ""
        if isinstance(hot_sectors, list) and hot_sectors:
            for i, s in enumerate(hot_sectors[:5], 1):
                name = s.get('板块名称', s.get('名称', '未知'))
                change = s.get('涨跌幅', 0)
                sector_text += f"  {i}. {name} ({change:+.2f}%)\n"
        
        # 高开个股
        pre_market = report['sections']['pre_market']
        gap_up_text = ""
        if isinstance(pre_market, list) and pre_market:
            count = 0
            for s in pre_market:
                if isinstance(s, dict) and 'error' not in s:
                    name = s.get('名称', '未知')
                    code = s.get('代码', '')
                    change = s.get('涨跌幅', 0)
                    gap_up_text += f"  • {name}({code}) {change:+.2f}%\n"
                    count += 1
                    if count >= 5:
                        break
        
        message = f"""📊 A股早间资讯 [{today}]

🌍 隔夜市场情绪: {us_sentiment} (中概股平均 {us_change:+.2f}%)
💰 北向资金: {north_trend} ({north_amount:.0f}万)

🔥 热门板块:
{sector_text}
⬆️ 高开个股:
{gap_up_text}
⚠️ 风险提示: 以上数据仅供参考，不构成投资建议。
"""
        return message


def main():
    """命令行入口"""
    import sys
    
    collector = MorningNewsCollector()
    report = collector.compile_report()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        message = collector.format_kim_message(report)
        print(message)


if __name__ == "__main__":
    main()
