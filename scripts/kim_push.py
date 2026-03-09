#!/usr/bin/env python3
"""
Kim 推送脚本 - A股早间资讯
"""

import subprocess
import sys
import os

SKILL_DIR = "/Users/hyx/.openclaw/skills/a-stock-picker"
VENV_PYTHON = f"{SKILL_DIR}/venv/bin/python3"

def get_morning_news():
    """获取早间资讯"""
    result = subprocess.run(
        [VENV_PYTHON, f"{SKILL_DIR}/scripts/morning_news.py"],
        capture_output=True,
        text=True
    )
    return result.stdout

def send_to_kim(message: str):
    """推送到 Kim"""
    # 使用 OpenClaw 的 message 工具
    result = subprocess.run(
        ["openclaw", "message", "send", "--channel", "kim", "--message", message],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    print(f"[{os.path.basename(__file__)}] 开始推送早间资讯...")
    
    # 获取资讯
    message = get_morning_news()
    
    # 发送到 Kim
    if send_to_kim(message):
        print(f"[{os.path.basename(__file__)}] 推送成功")
    else:
        print(f"[{os.path.basename(__file__)}] 推送失败")
        print(message)  # 打印消息内容以便调试

if __name__ == "__main__":
    main()
