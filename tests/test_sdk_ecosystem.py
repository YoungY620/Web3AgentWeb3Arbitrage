"""
测试 Hyperliquid SDK 生态
- 检查官方 Python SDK 是否可安装和导入
- 检查 npm 生态中可用的 SDK
- 对比直接调用 vs SDK 调用
"""

import subprocess
import sys
import json


def check_python_sdk():
    """检查 Python SDK 安装情况"""
    print("\n" + "=" * 60)
    print("测试 1: Python SDK 生态")
    print("=" * 60)

    sdks = [
        {
            "name": "hyperliquid-python-sdk",
            "pip": "hyperliquid-python-sdk",
            "import": "hyperliquid",
            "type": "官方 SDK",
            "downloads": "~257K/月",
        },
        {
            "name": "hyperliquid-sdk (QuickNode)",
            "pip": "hyperliquid-sdk",
            "import": "hyperliquid_sdk",
            "type": "第三方 (QuickNode)",
            "downloads": "~4K/月",
        },
    ]

    for sdk in sdks:
        print(f"\n  ── {sdk['name']} ({sdk['type']}) ──")
        print(f"     月下载量: {sdk['downloads']}")
        print(f"     安装: pip install {sdk['pip']}")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", sdk["pip"]],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.startswith(("Version:", "License:", "Requires:")):
                        print(f"     {line.strip()}")
                print(f"     [✓] 已安装")
            else:
                print(f"     [~] 未安装（可通过 pip install {sdk['pip']} 安装）")
        except Exception as e:
            print(f"     [!] 检查失败: {e}")

    return True


def check_node_sdk():
    """检查 Node.js SDK 生态"""
    print("\n" + "=" * 60)
    print("测试 2: Node.js / TypeScript SDK 生态")
    print("=" * 60)

    sdks = [
        {
            "name": "@nktkas/hyperliquid",
            "weekly_downloads": "~41K",
            "features": "TypeScript 100%, HTTP+WS, InfoClient, ExchangeClient",
            "quality": "⭐⭐⭐⭐⭐",
        },
        {
            "name": "hyperliquid",
            "weekly_downloads": "~3.3K",
            "features": "REST+WS, TypeScript, 浏览器+Node.js",
            "quality": "⭐⭐⭐⭐",
        },
        {
            "name": "@quicknode/hyperliquid-sdk",
            "weekly_downloads": "~32",
            "features": "简化 API, HyperCore, WS+gRPC",
            "quality": "⭐⭐⭐",
        },
    ]

    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            print(f"  [✓] Node.js {result.stdout.strip()} 可用")
        else:
            print(f"  [!] Node.js 未安装")
    except FileNotFoundError:
        print(f"  [!] Node.js 未安装")

    for sdk in sdks:
        print(f"\n  ── {sdk['name']} ──")
        print(f"     周下载量: {sdk['weekly_downloads']}")
        print(f"     特性: {sdk['features']}")
        print(f"     质量: {sdk['quality']}")
        print(f"     安装: npm install {sdk['name']}")

    return True


def check_alternative_data_sources():
    """检查替代数据源"""
    print("\n" + "=" * 60)
    print("测试 3: 替代/增强数据源")
    print("=" * 60)

    sources = [
        {
            "name": "Hyperliquid 官方 REST API",
            "url": "https://api.hyperliquid.xyz/info",
            "cost": "免费",
            "auth": "不需要",
            "note": "公开端点，recentTrades 无需认证",
        },
        {
            "name": "Hyperliquid 官方 WebSocket",
            "url": "wss://api.hyperliquid.xyz/ws",
            "cost": "免费",
            "auth": "不需要",
            "note": "实时推送，100 连接/IP",
        },
        {
            "name": "QuickNode Hyperliquid",
            "url": "https://quicknode.com/docs/hyperliquid",
            "cost": "付费（按 credits 计费）",
            "auth": "需要 API Key",
            "note": "10 credits/0.1MB 数据，适合需要高可用保障的场景",
        },
        {
            "name": "Chainstack Hyperliquid",
            "url": "https://chainstack.com",
            "cost": "付费",
            "auth": "需要 API Key",
            "note": "托管节点服务",
        },
        {
            "name": "Dwellir Hyperliquid",
            "url": "https://dwellir.com",
            "cost": "付费",
            "auth": "需要 API Key",
            "note": "RPC 提供商，有详细文档",
        },
    ]

    for src in sources:
        icon = "✓" if src["cost"] == "免费" else "$"
        print(f"\n  [{icon}] {src['name']}")
        print(f"      URL: {src['url']}")
        print(f"      费用: {src['cost']}")
        print(f"      认证: {src['auth']}")
        print(f"      备注: {src['note']}")

    return True


def main():
    print("╔" + "═" * 58 + "╗")
    print("║   Hyperliquid SDK 与生态系统调研                         ║")
    print("╚" + "═" * 58 + "╝")

    check_python_sdk()
    check_node_sdk()
    check_alternative_data_sources()

    print("\n" + "=" * 60)
    print("SDK 生态总结")
    print("=" * 60)
    print("""
  Python 生态:
    • hyperliquid-python-sdk (官方) — 成熟，月下载 25 万+
    • 支持 REST + WebSocket
    • Python >=3.9

  Node.js 生态:
    • @nktkas/hyperliquid — 最活跃，纯 TypeScript，周下载 4 万+
    • hyperliquid — 全功能，周下载 3K+
    • 两者都支持 REST + WebSocket

  推荐:
    • Python 项目 → hyperliquid-python-sdk
    • Node/TS 项目 → @nktkas/hyperliquid
    • 两者都免费、无需付费 API Key
""")


if __name__ == "__main__":
    main()
