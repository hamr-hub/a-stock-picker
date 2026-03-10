#!/usr/bin/env python3
"""
Kim 推送脚本 - A股早间资讯
每天早上 9:20 自动执行
"""

import subprocess
import sys
import os
import json
import urllib.request

SKILL_DIR = "/Users/hyx/.openclaw/skills/a-stock-picker"
VENV_PYTHON = f"{SKILL_DIR}/venv/bin/python3"
NEWS_SCRIPT = f"{SKILL_DIR}/scripts/morning_news.py"

# Kim Webhook 配置
KIM_WEBHOOK_URL = "https://kim-robot.kwaitalk.com/api/robot/send?key=f42b0434-f61d-4aeb-898a-6acf49eb3510"

def get_morning_news():
    """获取早间资讯"""
    result = subprocess.run(
        [VENV_PYTHON, NEWS_SCRIPT],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def send_to_kim_webhook(message: str):
    """通过 Webhook 推送到 Kim"""
    try:
        # Kim webhook 正确格式
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            KIM_WEBHOOK_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('success'):
                print(f"[{os.path.basename(__file__)}] ✅ Webhook 推送成功")
                return True
            else:
                print(f"[{os.path.basename(__file__)}] ❌ Webhook 推送失败: {result}")
                return False
    except Exception as e:
        print(f"[{os.path.basename(__file__)}] ❌ Webhook 推送异常: {e}")
        return False

def main():
    timestamp = subprocess.run(["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True).stdout.strip()
    print(f"[{timestamp}] 开始推送早间资讯...")
    
    # 获取资讯
    message = get_morning_news()
    
    if not message:
        print(f"[{os.path.basename(__file__)}] ❌ 获取资讯失败")
        sys.exit(1)
    
    # 发送到 Kim Webhook
    success = send_to_kim_webhook(message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
