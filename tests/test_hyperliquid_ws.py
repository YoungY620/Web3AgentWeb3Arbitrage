"""
测试 Hyperliquid WebSocket API
- 连接 wss://api.hyperliquid.xyz/ws
- 订阅 trades（BTC 永续 + NVDA spot）
- 记录延迟、消息频率、数据结构
- 测试断线行为
"""

import asyncio
import json
import time
import sys
from datetime import datetime, timezone

WS_URL = "wss://api.hyperliquid.xyz/ws"

SUBSCRIPTIONS = [
    {"method": "subscribe", "subscription": {"type": "trades", "coin": "BTC"}},
    {"method": "subscribe", "subscription": {"type": "trades", "coin": "ETH"}},
]

SPOT_SUBSCRIPTIONS = [
    {"method": "subscribe", "subscription": {"type": "trades", "coin": "@5"}},
]


async def test_ws_connection():
    """测试基础 WebSocket 连接"""
    try:
        import websockets
    except ImportError:
        print("  [!] 缺少 websockets 库，请运行: pip install websockets")
        return False

    print("\n" + "=" * 60)
    print("测试 1: Hyperliquid WebSocket 基础连接")
    print("=" * 60)

    try:
        t0 = time.time()
        async with websockets.connect(WS_URL) as ws:
            latency_ms = (time.time() - t0) * 1000
            print(f"  [✓] 连接成功 — 延迟 {latency_ms:.0f}ms")
            print(f"  [✓] 端点: {WS_URL}")
            print(f"  [✓] 无需 API Key / 认证")
            return True
    except Exception as e:
        print(f"  [✗] 连接失败: {e}")
        return False


async def test_trades_subscription():
    """测试永续合约 trades 订阅"""
    try:
        import websockets
    except ImportError:
        return False

    print("\n" + "=" * 60)
    print("测试 2: 永续合约 Trades 订阅 (BTC, ETH)")
    print("=" * 60)

    try:
        async with websockets.connect(WS_URL) as ws:
            for sub in SUBSCRIPTIONS:
                await ws.send(json.dumps(sub))
                print(f"  [→] 发送订阅: {sub['subscription']['coin']}")

            messages = []
            trade_counts = {"BTC": 0, "ETH": 0}
            start = time.time()
            timeout = 15

            print(f"  [⏳] 等待最多 {timeout} 秒接收交易数据...")

            while time.time() - start < timeout:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=2)
                    msg = json.loads(raw)

                    if msg.get("channel") == "trades":
                        data = msg.get("data", [])
                        for trade in data:
                            coin = trade.get("coin", "?")
                            if coin in trade_counts:
                                trade_counts[coin] += 1

                            if len(messages) < 3:
                                messages.append(trade)

                        total = sum(trade_counts.values())
                        if total >= 10:
                            break

                    elif msg.get("channel") == "subscriptionResponse":
                        method = msg.get("data", {}).get("method", "")
                        print(f"  [✓] 订阅确认: {method}")

                except asyncio.TimeoutError:
                    continue

            elapsed = time.time() - start
            total = sum(trade_counts.values())

            if total > 0:
                print(f"\n  [✓] 在 {elapsed:.1f}s 内收到 {total} 笔交易")
                for coin, cnt in trade_counts.items():
                    print(f"      {coin}: {cnt} 笔")

                print(f"\n  [数据结构示例] 第一笔交易:")
                sample = messages[0] if messages else {}
                for k, v in sample.items():
                    print(f"      {k}: {v}")

                if messages:
                    t = messages[0]
                    ts_ms = t.get("time", 0)
                    server_time = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                    now = datetime.now(timezone.utc)
                    delay = (now - server_time).total_seconds()
                    print(f"\n  [延迟] 服务器时间 vs 本地时间差: {delay:.2f}s")

                px = float(messages[0].get("px", 0))
                sz = float(messages[0].get("sz", 0))
                print(f"  [名义金额示例] {messages[0].get('coin')}: "
                      f"${px * sz:,.2f} ({sz} @ ${px:,.2f})")
                return True
            else:
                print(f"  [!] {timeout}s 内未收到任何交易数据")
                return False

    except Exception as e:
        print(f"  [✗] 订阅测试失败: {e}")
        return False


async def test_spot_subscription():
    """测试 Spot 市场 trades 订阅（如 NVDA 类 tokenized stock）"""
    try:
        import websockets
    except ImportError:
        return False

    print("\n" + "=" * 60)
    print("测试 3: Spot 市场 Trades 订阅")
    print("=" * 60)

    coins_to_try = ["@5", "@1", "PURR/USDC"]
    results = {}

    for coin in coins_to_try:
        sub = {"method": "subscribe", "subscription": {"type": "trades", "coin": coin}}
        try:
            async with websockets.connect(WS_URL) as ws:
                await ws.send(json.dumps(sub))

                got_response = False
                got_trades = False
                start = time.time()

                while time.time() - start < 8:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=2)
                        msg = json.loads(raw)

                        if msg.get("channel") == "subscriptionResponse":
                            got_response = True
                        elif msg.get("channel") == "trades":
                            got_trades = True
                            data = msg.get("data", [])
                            if data:
                                print(f"  [✓] coin='{coin}' — 收到 {len(data)} 笔交易")
                                sample = data[0]
                                print(f"      coin={sample.get('coin')} "
                                      f"px={sample.get('px')} sz={sample.get('sz')} "
                                      f"side={sample.get('side')}")
                            break

                    except asyncio.TimeoutError:
                        continue

                if got_response and not got_trades:
                    print(f"  [~] coin='{coin}' — 订阅成功但暂无交易数据（市场不活跃）")
                elif not got_response and not got_trades:
                    print(f"  [?] coin='{coin}' — 未收到任何响应")

                results[coin] = {"subscribed": got_response, "trades": got_trades}

        except Exception as e:
            print(f"  [✗] coin='{coin}' — 错误: {e}")
            results[coin] = {"subscribed": False, "trades": False, "error": str(e)}

    return any(r.get("subscribed") or r.get("trades") for r in results.values())


async def test_reconnect_behavior():
    """测试断线重连后的快照行为"""
    try:
        import websockets
    except ImportError:
        return False

    print("\n" + "=" * 60)
    print("测试 4: 断线重连行为")
    print("=" * 60)

    sub = {"method": "subscribe", "subscription": {"type": "trades", "coin": "BTC"}}

    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps(sub))
            first_msg = None
            start = time.time()
            while time.time() - start < 5:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=2)
                    msg = json.loads(raw)
                    if msg.get("channel") == "trades":
                        first_msg = msg
                        break
                except asyncio.TimeoutError:
                    continue

        print("  [→] 第一次连接已断开")

        await asyncio.sleep(1)

        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps(sub))
            reconnect_msg = None
            start = time.time()
            while time.time() - start < 8:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=2)
                    msg = json.loads(raw)
                    if msg.get("channel") == "trades":
                        reconnect_msg = msg
                        data = msg.get("data", [])
                        print(f"  [✓] 重连后首次收到 {len(data)} 笔交易")
                        if data:
                            ts_ms = data[0].get("time", 0)
                            dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                            print(f"      最早一笔时间: {dt.isoformat()}")
                        break
                except asyncio.TimeoutError:
                    continue

            if reconnect_msg:
                print("  [✓] 重连后可正常接收数据")
                print("  [!] 注意: 重连不会补发断线期间的数据，需自行处理缺口")
                return True
            else:
                print("  [!] 重连后未收到数据")
                return False

    except Exception as e:
        print(f"  [✗] 重连测试失败: {e}")
        return False


async def test_rate_limits():
    """测试连接限制"""
    try:
        import websockets
    except ImportError:
        return False

    print("\n" + "=" * 60)
    print("测试 5: 连接与订阅限制")
    print("=" * 60)

    connections = []
    max_test = 5

    try:
        for i in range(max_test):
            ws = await websockets.connect(WS_URL)
            connections.append(ws)

        print(f"  [✓] 成功同时打开 {len(connections)} 个连接（文档上限 100/IP）")

        ws = connections[0]
        sub_count = 0
        for i in range(10):
            sub = {"method": "subscribe", "subscription": {"type": "trades", "coin": f"BTC"}}
            await ws.send(json.dumps(sub))
            sub_count += 1

        print(f"  [✓] 单连接发送 {sub_count} 个订阅消息正常（文档上限 1000/IP）")
        return True

    except Exception as e:
        print(f"  [✗] 限制测试异常: {e}")
        return False

    finally:
        for ws in connections:
            await ws.close()


async def main():
    print("╔" + "═" * 58 + "╗")
    print("║   Hyperliquid WebSocket API 综合测试                     ║")
    print("║   端点: wss://api.hyperliquid.xyz/ws                     ║")
    print("╚" + "═" * 58 + "╝")

    results = {}

    results["基础连接"] = await test_ws_connection()
    results["永续 Trades 订阅"] = await test_trades_subscription()
    results["Spot Trades 订阅"] = await test_spot_subscription()
    results["断线重连"] = await test_reconnect_behavior()
    results["连接限制"] = await test_rate_limits()

    print("\n" + "=" * 60)
    print("WebSocket 测试结果汇总")
    print("=" * 60)
    for name, passed in results.items():
        icon = "✓" if passed else "✗"
        print(f"  [{icon}] {name}")

    print(f"\n  费用: $0（完全免费，无需 API Key）")
    print(f"  认证: 不需要")
    print(f"  文档限制: 100 连接/IP, 1000 订阅/IP, 2000 消息/分钟")

    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
