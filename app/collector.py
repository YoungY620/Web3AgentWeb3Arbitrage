"""
Hyperliquid WebSocket 实时交易采集器
后台运行，持续将 trades 写入 SQLite
"""

import asyncio
import json
import logging
import time

import websockets

from app.database import insert_trades

logger = logging.getLogger("collector")

WS_URL = "wss://api.hyperliquid.xyz/ws"
DEFAULT_COINS = ["BTC", "ETH", "SOL", "HYPE", "PURR/USDC"]

RECONNECT_DELAY = 3
MAX_RECONNECT_DELAY = 60


class TradeCollector:
    def __init__(self, coins: list[str] = None):
        self.coins = coins or DEFAULT_COINS
        self.running = False
        self.stats = {
            "connected": False,
            "total_received": 0,
            "total_inserted": 0,
            "last_trade_time": None,
            "reconnect_count": 0,
            "start_time": None,
            "errors": [],
        }
        self._task = None

    async def start(self):
        if self.running:
            return
        self.running = True
        self.stats["start_time"] = time.time()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("采集器已启动, coins=%s", self.coins)

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.stats["connected"] = False
        logger.info("采集器已停止")

    async def _run_loop(self):
        delay = RECONNECT_DELAY
        while self.running:
            try:
                await self._connect_and_collect()
                delay = RECONNECT_DELAY
            except (
                websockets.exceptions.ConnectionClosed,
                websockets.exceptions.ConnectionClosedError,
                ConnectionRefusedError,
                OSError,
            ) as e:
                self.stats["connected"] = False
                self.stats["reconnect_count"] += 1
                logger.warning("连接断开: %s, %ds 后重连...", e, delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, MAX_RECONNECT_DELAY)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.stats["errors"].append(str(e))
                logger.error("采集异常: %s", e, exc_info=True)
                await asyncio.sleep(delay)

    async def _connect_and_collect(self):
        async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=10) as ws:
            self.stats["connected"] = True
            logger.info("已连接 %s", WS_URL)

            for coin in self.coins:
                sub = {"method": "subscribe", "subscription": {"type": "trades", "coin": coin}}
                await ws.send(json.dumps(sub))
                logger.info("已订阅 trades: %s", coin)

            batch = []
            last_flush = time.time()

            while self.running:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    if batch:
                        await self._flush(batch)
                        batch = []
                        last_flush = time.time()
                    continue

                msg = json.loads(raw)

                if msg.get("channel") == "trades":
                    data = msg.get("data", [])
                    batch.extend(data)
                    self.stats["total_received"] += len(data)

                    if len(data) > 0:
                        self.stats["last_trade_time"] = data[-1].get("time")

                now = time.time()
                if len(batch) >= 100 or (now - last_flush > 2 and batch):
                    await self._flush(batch)
                    batch = []
                    last_flush = now

    async def _flush(self, batch: list):
        if not batch:
            return
        try:
            inserted = await insert_trades(batch)
            self.stats["total_inserted"] += inserted
        except Exception as e:
            logger.error("写入数据库失败: %s", e)
            self.stats["errors"].append(f"db_write: {e}")


collector = TradeCollector()
