#!/usr/bin/env python3
"""
A股早间资讯推送到 Kim
通过 OpenClaw gateway 发送消息
"""

import subprocess
import sys
import os

# 添加技能目录到路径
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from morning_news import MorningNewsCollector

def send_to_kim(message: str):
    """使用 OpenClaw CLI 发送 Kim 消息"""
    try:
        # 使用 osascript 发送消息（在 macOS 上）
        # 或者使用 openclaw 命令行工具
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "kim", "--message", message],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ 消息推送成功")
        else:
            print(f"❌ 推送失败: {result.stderr}")
    except FileNotFoundError:
        print("⚠️ OpenClaw CLI 未找到，消息内容：")
        print(message)
        print("\n请手动复制以上消息发送到 Kim")
    except Exception as e:
        print(f"❌ 发送错误: {e}")

def main():
    print("📊 开始生成早间资讯...")
    
    # 收集资讯
    collector = MorningNewsCollector()
    report = collector.compile_report()
    message = collector.format_kim_message(report)
    
    print("\n" + "="*50)
    print("生成的消息内容：")
    print("="*50)
    print(message)
    print("="*50 + "\n")
    
    # 推送到 Kim
    send_to_kim(message)

if __name__ == "__main__":
    main()
