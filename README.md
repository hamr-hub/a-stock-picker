# A股 AI 选股助手

> **OpenClaw Skill** — 基于 [OpenClaw](https://openclaw.ai) 的 A股智能选股与资讯推送助手

使用 AKShare 免费数据源，支持多种选股策略、个股 AI 分析和早间资讯推送。

## 功能

- **多策略选股**：价值投资、成长投资、动量策略、技术突破、高股息
- **个股分析**：基本面/技术面评分，生成 AI 分析 Prompt
- **早间资讯**：美股中概股、北向资金、热门板块、高开个股
- **消息推送**：集成 Kim 推送，支持 crontab 定时任务

## 安装依赖

```bash
pip install akshare pandas
```

## 使用

```bash
# 价值投资选股
python3 scripts/screen.py screen --strategy value --top 20

# 动量策略
python3 scripts/screen.py screen --strategy momentum --top 20

# 个股分析
python3 scripts/screen.py analyze --symbol 000001

# 早间资讯
python3 scripts/morning_news.py
```

## 作为 OpenClaw Skill 使用

将本仓库克隆到 `~/.openclaw/skills/a-stock-picker`，OpenClaw 会自动识别 `SKILL.md` 并在需要 A股选股、股票分析时调用相关脚本。

```bash
git clone https://github.com/hamr-hub/a-stock-picker ~/.openclaw/skills/a-stock-picker
```

## 数据源

[AKShare](https://www.akshare.xyz/) — 免费开源财经数据接口
