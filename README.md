# A股 AI 选股系统 - 安装配置指南

## ✅ 已完成的设置

### 1. 技能安装位置
```
~/.openclaw/skills/a-stock-picker/
├── SKILL.md                      # 使用说明
├── venv/                         # Python 虚拟环境
└── scripts/
    ├── data_fetch.py            # 数据获取
    ├── screen.py                # 选股策略
    ├── ai_analyze.py            # AI 分析
    ├── morning_news.py          # 早间资讯收集
    ├── kim_push.py              # Kim 推送脚本 ⭐
    └── morning_cron.sh          # 定时任务脚本
```

### 2. 已安装的依赖
- akshare (A股数据源)
- pandas (数据处理)

### 3. 已配置的定时任务
```bash
crontab -l
# 输出: 20 9 * * 1-5 /Users/hyx/.openclaw/skills/a-stock-picker/scripts/kim_push.py >> /tmp/stock_morning.log 2>&1
```

---

## 🔧 需要完成的配置

### 配置 Kim 接收者（重要）

**方式1: 环境变量（推荐）**
```bash
# 添加到你的 ~/.zshrc 或 ~/.bash_profile
export KIM_STOCK_TARGET="你的Kim用户名或手机号"

# 立即生效
source ~/.zshrc
```

**方式2: 直接修改脚本**
```bash
# 编辑第14行，填入你的 Kim 用户名
nano ~/.openclaw/skills/a-stock-picker/scripts/kim_push.py
# KIM_TARGET = "你的Kim用户名"
```

---

## 🚀 使用指南

### 1. 早间资讯推送
```bash
# 手动测试推送
python3 ~/.openclaw/skills/a-stock-picker/scripts/kim_push.py

# 查看定时任务日志
tail -f /tmp/stock_morning.log
```

### 2. 选股策略
```bash
cd ~/.openclaw/skills/a-stock-picker
source venv/bin/activate

# 价值投资选股 (Top 20)
python3 scripts/screen.py screen --strategy value --top 20

# 成长投资选股
python3 scripts/screen.py screen --strategy growth --top 20

# 动量策略
python3 scripts/screen.py screen --strategy momentum --top 20

# 技术突破
python3 scripts/screen.py screen --strategy technical --top 20
```

### 3. 个股深度分析
```bash
# 分析单只股票（如平安银行 000001）
python3 scripts/screen.py analyze --symbol 000001
```

### 4. 早间资讯（仅显示）
```bash
# 生成早间资讯
python3 scripts/morning_news.py
```

---

## 📋 推送内容示例

每天早上 9:20 你会收到类似这样的 Kim 消息：

```
📊 A股早间资讯 [2026-03-09]

🌍 隔夜市场情绪: 中性 (中概股平均 +0.00%)
💰 北向资金: 流出 (0万)

🔥 热门板块:
  1. 逆变器 (+7.97%)
  2. 储能 (+6.26%)
  3. 油气开采Ⅲ (+3.76%)

⬆️ 高开个股:
  • N觅睿(920036) +91.91%
  • 派诺科技(920375) +22.04%

⚠️ 风险提示: 以上数据仅供参考，不构成投资建议。
```

---

## 🛠️ 故障排查

### 检查定时任务
```bash
crontab -l
```

### 手动测试
```bash
# 测试资讯收集
python3 ~/.openclaw/skills/a-stock-picker/venv/bin/python3 \
  ~/.openclaw/skills/a-stock-picker/scripts/morning_news.py

# 测试完整推送
python3 ~/.openclaw/skills/a-stock-picker/scripts/kim_push.py
```

### 查看日志
```bash
# 推送日志
tail /tmp/stock_morning.log

# 系统邮件（cron 输出）
mail
```

---

## ⚠️ 免责声明

本系统提供的所有数据和分析仅供学习和参考，不构成任何投资建议。股市有风险，投资需谨慎。

---

## 📞 支持

如有问题，可以：
1. 检查日志文件 `/tmp/stock_morning.log`
2. 手动运行脚本测试
3. 更新 akshare: `pip install -U akshare`
