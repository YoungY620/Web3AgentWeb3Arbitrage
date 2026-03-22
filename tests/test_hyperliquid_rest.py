"""
测试 Hyperliquid REST API（Info Endpoint）
- recentTrades: 公开接口，查询某 coin 近期成交
- meta: 获取所有可用市场元信息
- spotMeta: 获取 Spot 市场元信息
- allMids: 获取所有市场中间价
"""

import json
import time
import sys

API_URL = "https://api.hyperliquid.xyz/info"


def post(payload: dict):
    import requests
    t0 = time.time()
    resp = requests.post(API_URL, json=payload, timeout=10)
    latency = (time.time() - t0) * 1000
    return resp, latency


def test_meta():
    """获取永续合约市场元信息"""
    print("\n" + "=" * 60)
    print("测试 1: 永续合约元信息 (meta)")
    print("=" * 60)

    try:
        resp, latency = post({"type": "meta"})
        if resp.status_code != 200:
            print(f"  [✗] HTTP {resp.status_code}")
            return False

        data = resp.json()
        universe = data.get("universe", [])
        print(f"  [✓] 响应 {resp.status_code} — 延迟 {latency:.0f}ms")
        print(f"  [✓] 可用永续合约数: {len(universe)}")

        if universe:
            sample = universe[:5]
            names = [c.get("name", "?") for c in sample]
            print(f"  [示例] 前 5 个: {', '.join(names)}")

            has_nvda = any(c.get("name") == "NVDA" for c in universe)
            print(f"  [{'✓' if has_nvda else '!'}] NVDA 永续合约: {'存在' if has_nvda else '不存在'}")

        return True

    except Exception as e:
        print(f"  [✗] 失败: {e}")
        return False


def test_spot_meta():
    """获取 Spot 市场元信息"""
    print("\n" + "=" * 60)
    print("测试 2: Spot 市场元信息 (spotMeta)")
    print("=" * 60)

    try:
        resp, latency = post({"type": "spotMeta"})
        if resp.status_code != 200:
            print(f"  [✗] HTTP {resp.status_code}")
            return False

        data = resp.json()
        universe = data.get("universe", [])
        tokens = data.get("tokens", [])
        print(f"  [✓] 响应 {resp.status_code} — 延迟 {latency:.0f}ms")
        print(f"  [✓] Spot 市场数: {len(universe)}")
        print(f"  [✓] Token 数: {len(tokens)}")

        if universe and tokens:
            for pair in universe[:5]:
                name = pair.get("name", "?")
                idx = pair.get("tokens", [])
                print(f"      {name} (token indices: {idx})")

            token_names = [t.get("name", "?") for t in tokens[:10]]
            print(f"  [Token 示例] {', '.join(token_names)}")

            nvda_tokens = [t for t in tokens if "NVDA" in t.get("name", "").upper()]
            if nvda_tokens:
                print(f"  [✓] 找到 NVDA 相关 token: {[t.get('name') for t in nvda_tokens]}")
            else:
                print(f"  [!] 未找到 NVDA token（可能用其他名称或 index）")

        return True

    except Exception as e:
        print(f"  [✗] 失败: {e}")
        return False


def test_all_mids():
    """获取所有市场中间价"""
    print("\n" + "=" * 60)
    print("测试 3: 所有市场中间价 (allMids)")
    print("=" * 60)

    try:
        resp, latency = post({"type": "allMids"})
        if resp.status_code != 200:
            print(f"  [✗] HTTP {resp.status_code}")
            return False

        data = resp.json()
        print(f"  [✓] 响应 {resp.status_code} — 延迟 {latency:.0f}ms")
        print(f"  [✓] 可用市场数: {len(data)}")

        if isinstance(data, dict):
            for coin in ["BTC", "ETH", "SOL", "NVDA"]:
                mid = data.get(coin)
                if mid:
                    print(f"      {coin}: ${float(mid):,.2f}")
                else:
                    print(f"      {coin}: 无数据")

        return True

    except Exception as e:
        print(f"  [✗] 失败: {e}")
        return False


def test_recent_trades():
    """获取近期成交"""
    print("\n" + "=" * 60)
    print("测试 4: 近期成交查询 (recentTrades)")
    print("=" * 60)

    coins = ["BTC", "ETH"]
    all_ok = True

    for coin in coins:
        try:
            resp, latency = post({"type": "recentTrades", "coin": coin})
            if resp.status_code != 200:
                print(f"  [✗] {coin}: HTTP {resp.status_code}")
                all_ok = False
                continue

            trades = resp.json()
            print(f"\n  [{coin}] 响应 {resp.status_code} — 延迟 {latency:.0f}ms")
            print(f"  [{coin}] 返回 {len(trades)} 笔交易")

            if trades:
                t = trades[0]
                fields = list(t.keys())
                print(f"  [{coin}] 数据字段: {fields}")
                print(f"  [{coin}] 示例: px={t.get('px')} sz={t.get('sz')} "
                      f"side={t.get('side')} time={t.get('time')}")

                px = float(t.get("px", 0))
                sz = float(t.get("sz", 0))
                notional = px * sz
                print(f"  [{coin}] 名义金额: ${notional:,.2f}")

                from datetime import datetime, timezone
                ts = t.get("time", 0)
                dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                print(f"  [{coin}] 最新交易时间: {dt.isoformat()}")

        except Exception as e:
            print(f"  [✗] {coin}: {e}")
            all_ok = False

    return all_ok


def test_spot_recent_trades():
    """测试 Spot 市场近期成交"""
    print("\n" + "=" * 60)
    print("测试 5: Spot 市场近期成交")
    print("=" * 60)

    spot_coins = ["PURR/USDC", "HYPE/USDC", "@1", "@5"]

    for coin in spot_coins:
        try:
            resp, latency = post({"type": "recentTrades", "coin": coin})
            trades = resp.json() if resp.status_code == 200 else None

            if trades and isinstance(trades, list) and len(trades) > 0:
                t = trades[0]
                print(f"  [✓] coin='{coin}' — {len(trades)} 笔 — "
                      f"px={t.get('px')} sz={t.get('sz')} — {latency:.0f}ms")
            elif trades is not None and isinstance(trades, list):
                print(f"  [~] coin='{coin}' — 返回空列表 — {latency:.0f}ms")
            else:
                body = resp.text[:100] if resp else "无响应"
                print(f"  [✗] coin='{coin}' — HTTP {resp.status_code} — {body}")

        except Exception as e:
            print(f"  [✗] coin='{coin}' — {e}")

    return True


def test_rate_limit():
    """测试速率限制"""
    print("\n" + "=" * 60)
    print("测试 6: REST API 速率限制测试")
    print("=" * 60)

    import requests

    errors = 0
    total = 20
    latencies = []

    for i in range(total):
        try:
            t0 = time.time()
            resp = requests.post(API_URL, json={"type": "allMids"}, timeout=5)
            lat = (time.time() - t0) * 1000
            latencies.append(lat)

            if resp.status_code != 200:
                errors += 1
                if resp.status_code == 429:
                    print(f"  [!] 第 {i+1} 次请求被限流 (429)")
                    break
        except Exception:
            errors += 1

    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    print(f"  [✓] 连续 {total} 次请求: {total - errors} 成功, {errors} 失败")
    print(f"  [✓] 平均延迟: {avg_lat:.0f}ms")
    print(f"  [✓] 最小/最大: {min(latencies):.0f}ms / {max(latencies):.0f}ms")

    if errors == 0:
        print(f"  [✓] 未触发速率限制")
    return errors == 0


def main():
    print("╔" + "═" * 58 + "╗")
    print("║   Hyperliquid REST API (Info Endpoint) 综合测试          ║")
    print("║   端点: https://api.hyperliquid.xyz/info                 ║")
    print("╚" + "═" * 58 + "╝")

    try:
        import requests
    except ImportError:
        print("  [!] 缺少 requests 库，请运行: pip install requests")
        sys.exit(1)

    results = {}
    results["永续合约元信息"] = test_meta()
    results["Spot 市场元信息"] = test_spot_meta()
    results["市场中间价"] = test_all_mids()
    results["永续近期成交"] = test_recent_trades()
    results["Spot 近期成交"] = test_spot_recent_trades()
    results["速率限制"] = test_rate_limit()

    print("\n" + "=" * 60)
    print("REST API 测试结果汇总")
    print("=" * 60)
    for name, passed in results.items():
        icon = "✓" if passed else "✗"
        print(f"  [{icon}] {name}")

    print(f"\n  费用: $0（完全免费，无需 API Key）")
    print(f"  认证: 不需要（只读 info 端点）")
    print(f"  可用端点: meta, spotMeta, allMids, recentTrades, l2Book 等")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
