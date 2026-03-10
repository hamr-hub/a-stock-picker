#!/bin/bash
# A股早间资讯定时推送 - 简化版
# 每天早上 9:20 执行

SKILL_DIR="/Users/hyx/.openclaw/skills/a-stock-picker"
PYTHON="$SKILL_DIR/venv/bin/python3"
PUSH_SCRIPT="$SKILL_DIR/scripts/morning_news.py"
LOG_FILE="/tmp/stock_morning.log"

# 记录日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行..." >> "$LOG_FILE"

# 生成资讯消息
MESSAGE=$($PYTHON "$PUSH_SCRIPT" 2>> "$LOG_FILE")

# 检查是否成功生成消息
if [ -z "$MESSAGE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: 消息生成失败" >> "$LOG_FILE"
    exit 1
fi

# 输出消息（可用于重定向或进一步处理）
echo "$MESSAGE"

# 记录完成
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行完成" >> "$LOG_FILE"
