#!/usr/bin/env python3
"""
AI 选股分析模块
使用 LLM 分析股票数据并给出投资建议
"""

import json
import os
import sys
from typing import Dict, List, Optional

# OpenClaw 可以通过环境变量或标准输入接收 LLM 分析结果

class AIStockAnalyzer:
    """AI 股票分析器"""
    
    @staticmethod
    def format_prompt(stock_data: dict, strategy: str = "value") -> str:
        """
        格式化 AI 分析 Prompt
        :param stock_data: 股票数据字典
        :param strategy: 选股策略 (value/growth/momentum/technical)
        """
        
        strategy_desc = {
            "value": "价值投资策略 - 关注低估值、高股息、稳定盈利的公司",
            "growth": "成长投资策略 - 关注高增长、高ROE、行业龙头的公司", 
            "momentum": "动量策略 - 关注趋势向上、突破关键均线的股票",
            "technical": "技术分析策略 - 关注K线形态、成交量、技术指标"
        }
        
        prompt = f"""你是一位专业的 A股投资分析师，请基于以下数据进行股票分析。

【选股策略】{strategy_desc.get(strategy, strategy_desc['value'])}

【股票数据】
{json.dumps(stock_data, ensure_ascii=False, indent=2)}

请提供以下分析：
1. 基本面评分 (1-10分)：评估公司的盈利能力、成长性、估值合理性
2. 技术面评分 (1-10分)：评估趋势、支撑压力、成交量配合
3. 综合评级：强烈推荐/推荐/中性/回避
4. 关键亮点：列出2-3个最重要的积极因素
5. 主要风险：列出2-3个主要风险点
6. 操作建议：买入/持有/观望/卖出的具体建议

请以 JSON 格式返回结果：
{{
  "fundamental_score": 8,
  "technical_score": 7,
  "overall_rating": "推荐",
  "highlights": ["亮点1", "亮点2"],
  "risks": ["风险1", "风险2"],
  "recommendation": "建议逢低分批买入，目标价XX元，止损价XX元"
}}
"""
        return prompt
    
    @staticmethod
    def parse_llm_response(response: str) -> dict:
        """解析 LLM 返回的 JSON"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except:
            # 尝试从文本中提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return {"raw_response": response, "parse_error": True}
    
    @staticmethod
    def batch_analyze(stocks_data: List[dict], strategy: str = "value") -> List[dict]:
        """
        批量分析股票
        返回包含 AI 分析结果的股票列表
        """
        results = []
        for stock in stocks_data:
            prompt = AIStockAnalyzer.format_prompt(stock, strategy)
            results.append({
                "symbol": stock.get("symbol"),
                "name": stock.get("name"),
                "prompt": prompt,
                "status": "ready_for_analysis"
            })
        return results
    
    @staticmethod
    def screen_stocks(stocks: List[dict], min_score: int = 7) -> List[dict]:
        """
        筛选高分股票
        :param stocks: 带 AI 评分的股票列表
        :param min_score: 最低综合评分
        """
        filtered = []
        for stock in stocks:
            fundamental = stock.get("ai_analysis", {}).get("fundamental_score", 0)
            technical = stock.get("ai_analysis", {}).get("technical_score", 0)
            avg_score = (fundamental + technical) / 2 if fundamental and technical else 0
            
            if avg_score >= min_score:
                stock['avg_score'] = avg_score
                filtered.append(stock)
        
        # 按评分排序
        return sorted(filtered, key=lambda x: x['avg_score'], reverse=True)


def main():
    """命令行入口 - 生成 AI 分析 Prompt"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ai_analyze.py <stock_json_file> [strategy]")
        print("Strategy: value | growth | momentum | technical")
        return
    
    # 从文件或标准输入读取股票数据
    if sys.argv[1] == '-':
        data = json.load(sys.stdin)
    else:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    strategy = sys.argv[2] if len(sys.argv) > 2 else "value"
    
    analyzer = AIStockAnalyzer()
    
    # 处理单只股票或多只股票
    if isinstance(data, list):
        results = analyzer.batch_analyze(data, strategy)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        prompt = analyzer.format_prompt(data, strategy)
        print(prompt)


if __name__ == "__main__":
    main()
