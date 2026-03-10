#!/bin/bash
# A股早间资讯定时推送设置脚本

echo "🤖 正在设置 A股早间资讯自动推送..."
echo ""

SKILL_DIR="/Users/hyx/.openclaw/skills/a-stock-picker"
PYTHON="$SKILL_DIR/venv/bin/python3"
PUSH_SCRIPT="$SKILL_DIR/scripts/push_to_kim.py"

# 检查虚拟环境
if [ ! -f "$PYTHON" ]; then
    echo "❌ 虚拟环境未找到，请先运行:"
    echo "   cd $SKILL_DIR && python3 -m venv venv && source venv/bin/activate && pip install akshare pandas"
    exit 1
fi

# 检查推送脚本
if [ ! -f "$PUSH_SCRIPT" ]; then
    echo "❌ 推送脚本未找到: $PUSH_SCRIPT"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""
echo "📅 设置定时任务 (crontab)..."
echo ""

# 创建临时 crontab 文件
CRON_JOB="20 9 * * 1-5 export OPENCLAW_GATEWAY_TOKEN=\\\"\$OPENCLAW_GATEWAY_TOKEN\\\" && export OPENCLAW_GATEWAY_URL=\\\"\$OPENCLAW_GATEWAY_URL\\\" && cd $SKILL_DIR && $PYTHON $PUSH_SCRIPT >> /tmp/stock_morning.log 2>&1"

# 显示将要添加的任务
echo "将要添加的定时任务："
echo "  时间: 每天早上 9:20 (工作日)"
echo "  命令: $PYTHON $PUSH_SCRIPT"
echo ""

# 检查是否已存在相同任务
if crontab -l 2>/dev/null | grep -q "push_to_kim.py"; then
    echo "⚠️ 定时任务已存在，跳过添加"
else
    # 添加到 crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ 定时任务已添加"
fi

echo ""
echo "📋 当前 crontab 内容："
crontab -l | grep -E "(stock|push_to_kim)" || echo "  (未找到相关任务)"
echo ""
echo "🧪 测试运行一次..."
echo ""

# 执行一次测试
cd "$SKILL_DIR" && "$PYTHON" "$PUSH_SCRIPT"

echo ""
echo "✨ 设置完成！"
echo ""
echo "📌 提示："
echo "   • 推送将在每个工作日早上 9:20 自动执行"
echo "   • 日志文件: /tmp/stock_morning.log"
echo "   • 如需修改时间，运行: crontab -e"
echo "   • 如需停用，运行: crontab -e 删除对应行"
