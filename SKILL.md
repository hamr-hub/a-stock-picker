---
name: a-stock-picker
description: A股 AI 选股与资讯推送系统。当用户需要 A股选股、股票分析、技术指标计算、早间资讯推送时使用。支持价值投资、成长投资、动量策略、技术分析、KDJ等多种选股策略。使用 AKShare 免费数据源，集成 Kim 消息推送。
---

# A股 AI 选股系统

基于 OpenClaw 的 A股智能选股与资讯推送工具。

## 核心功能

### 1. 数据获取 (`scripts/data_fetch.py`)
- 全市场股票列表
- 个股日线数据（前复权）
- 基本面数据（PE、PB、ROE 等）
- 热门板块、涨停股票
- 技术指标计算（MA、RSI、KDJ）

### 2. 选股策略 (`scripts/screen.py`)
支持策略：
- **value** - 价值投资：低 PE、低 PB、高 ROE
- **growth** - 成长投资：高换手、活跃度高
- **momentum** - 动量策略：近期强势、量价配合
- **technical** - 技术突破：当日大涨、放量
- **dividend** - 高股息：低估值、大盘股
- **kdj** - KDJ超卖：J线在K/D线下方，偏离越大排名越靠前

### 3. AI 分析 (`scripts/ai_analyze.py`)
- 生成 AI 分析 Prompt
- 基本面/技术面评分
- 投资建议生成

### 4. 早间资讯 (`scripts/morning_news.py`)
- 隔夜美股中概股表现
- 北向资金流向
- 热门板块排行
- 集合竞价高开个股

## 使用方法

### 选股
```bash
# 价值投资选股 (Top 20)
python3 ~/.openclaw/skills/a-stock-picker/scripts/screen.py screen --strategy value --top 20

# 成长投资选股
python3 ~/.openclaw/skills/a-stock-picker/scripts/screen.py screen --strategy growth --top 20

# 动量策略
python3 ~/.openclaw/skills/a-stock-picker/scripts/screen.py screen --strategy momentum --top 20

# KDJ 超卖选股（J线在K/D线下方，偏离越大排名越靠前）
python3 ~/.openclaw/skills/a-stock-picker/scripts/screen.py screen --strategy kdj --top 20
```

### 个股深度分析
```bash
python3 ~/.openclaw/skills/a-stock-picker/scripts/screen.py analyze --symbol 000001
```

### 获取早间资讯
```bash
# 文字格式（用于推送）
python3 ~/.openclaw/skills/a-stock-picker/scripts/morning_news.py

# JSON 格式
python3 ~/.openclaw/skills/a-stock-picker/scripts/morning_news.py --json
```

### AI 分析
```bash
# 生成分析 Prompt（用于 LLM 分析）
python3 ~/.openclaw/skills/a-stock-picker/scripts/ai_analyze.py <stock_data.json>
```

## 定时推送设置

### 添加到 crontab（每天早上 9:20）
```bash
# 编辑 crontab
crontab -e

# 添加行（替换为你的实际路径）
20 9 * * 1-5 /Users/hyx/.openclaw/skills/a-stock-picker/scripts/push_morning.sh >> /tmp/stock_push.log 2>&1
```

### 使用 OpenClaw 定时任务
在 `HEARTBEAT.md` 中添加：
```markdown
- 每天 09:20 执行 A股早间资讯推送
  → 运行: python3 ~/.openclaw/skills/a-stock-picker/scripts/morning_news.py
  → 推送到 Kim
```

## 数据源

使用 **AKShare** 免费开源财经数据接口：
- 安装: `pip install akshare`
- 文档: https://www.akshare.xyz/

## 依赖

```bash
pip install akshare pandas
```

## 输出格式

所有脚本默认输出 JSON，便于进一步处理或与 AI 分析集成。
