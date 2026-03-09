#!/bin/bash
# A股早间资讯推送脚本
# 每天早上 9:20 执行

SKILL_DIR="/Users/hyx/.openclaw/skills/a-stock-picker"
PYTHON="$SKILL_DIR/venv/bin/python3"

# 收集资讯并发送
echo "[$(date)] 开始推送早间资讯..."

# 生成 Kim 消息
MESSAGE=$($PYTHON "$SKILL_DIR/scripts/morning_news.py" 2>/dev/null)

# 发送到 Kim (使用 OpenClaw 的 message 工具)
# 注意：需要在 OpenClaw 环境中执行，或配置 Kim Webhook
if command -v openclaw &> /dev/null; then
    openclaw message send --channel kim --message "$MESSAGE"
    echo "[$(date)] 推送完成"
else
    echo "OpenClaw 未安装，消息内容："
    echo "$MESSAGE"
fi
