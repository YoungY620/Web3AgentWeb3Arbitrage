"""
综合测试入口 — 一键运行所有 API / 数据源测试
"""

import asyncio
import sys
import time


def print_banner():
    print()
    print("╔" + "═" * 62 + "╗")
    print("║                                                              ║")
    print("║   Web3 Arbitrage — 数据源可用性综合测试                      ║")
    print("║                                                              ║")
    print("║   测试项目:                                                  ║")
    print("║     1. Hyperliquid WebSocket API (trades 实时推送)           ║")
    print("║     2. Hyperliquid REST API (info 端点)                     ║")
    print("║     3. SDK 与生态系统调研                                    ║")
    print("║                                                              ║")
    print("╚" + "═" * 62 + "╝")
    print()


async def run_ws_tests():
    print("\n" + "█" * 62)
    print("  PART 1: Hyperliquid WebSocket API 测试")
    print("█" * 62)

    from test_hyperliquid_ws import main as ws_main
    return await ws_main()


def run_rest_tests():
    print("\n" + "█" * 62)
    print("  PART 2: Hyperliquid REST API 测试")
    print("█" * 62)

    from test_hyperliquid_rest import main as rest_main
    return rest_main()


def run_sdk_tests():
    print("\n" + "█" * 62)
    print("  PART 3: SDK 与生态系统调研")
    print("█" * 62)

    from test_sdk_ecosystem import main as sdk_main
    sdk_main()
    return True


def print_final_report(results: dict, total_time: float):
    print("\n")
    print("╔" + "═" * 62 + "╗")
    print("║                    综  合  测  试  报  告                    ║")
    print("╠" + "═" * 62 + "╣")

    for section, passed in results.items():
        icon = "✓ PASS" if passed else "✗ FAIL"
        line = f"║  [{icon}] {section}"
        print(line + " " * (63 - len(line)) + "║")

    print("╠" + "═" * 62 + "╣")

    cost_table = [
        ("Hyperliquid WebSocket API", "$0/月", "免费", "不需要"),
        ("Hyperliquid REST API",      "$0/月", "免费", "不需要"),
        ("Python SDK (官方)",         "$0",    "免费", "pip install"),
        ("Node.js SDK",              "$0",    "免费", "npm install"),
        ("QuickNode (第三方)",        "付费",  "按量", "需要 Key"),
        ("Chainstack (第三方)",       "付费",  "按量", "需要 Key"),
    ]

    print("║                                                              ║")
    print("║  数据源           费用     计费方式   认证要求               ║")
    print("║  ─────────────────────────────────────────────────────────    ║")
    for name, cost, billing, auth in cost_table:
        line = f"║  {name:<20s} {cost:<9s} {billing:<10s} {auth}"
        print(line + " " * (63 - len(line)) + "║")

    print("╠" + "═" * 62 + "╣")
    print("║                                                              ║")
    print("║  结论:                                                       ║")
    print("║  • Hyperliquid 官方 API（REST + WebSocket）完全免费          ║")
    print("║  • 无需 API Key，直连即可                                    ║")
    print("║  • Python / Node.js SDK 生态成熟，可直接使用                 ║")
    print("║  • 第三方服务 (QuickNode 等) 提供增值但需付费                ║")
    print("║  • 推荐方案: 直连官方 API + 官方 SDK = $0 成本               ║")
    print("║                                                              ║")
    print(f"║  总测试耗时: {total_time:.1f}s" + " " * (49 - len(f"{total_time:.1f}")) + "║")
    print("║                                                              ║")
    print("╚" + "═" * 62 + "╝")


async def main():
    print_banner()

    total_start = time.time()
    results = {}

    results["Hyperliquid WebSocket API"] = await run_ws_tests()
    results["Hyperliquid REST API"] = run_rest_tests()
    results["SDK 与生态系统"] = run_sdk_tests()

    total_time = time.time() - total_start
    print_final_report(results, total_time)

    all_pass = all(results.values())
    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
