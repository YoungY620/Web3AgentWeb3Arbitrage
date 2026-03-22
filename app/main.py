import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import requests
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.collector import collector
from app.database import (
    get_available_coins,
    get_db_stats,
    get_large_trades,
    get_price_series,
    get_recent_trades,
    get_trade_stats,
    init_db,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

HL_INFO = "https://api.hyperliquid.xyz/info"

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await collector.start()
    yield
    await collector.stop()


app = FastAPI(title="Hyperliquid Trade Dashboard", lifespan=lifespan)


# ── API Routes ──────────────────────────────────────────

@app.get("/api/status")
async def api_status():
    db = await get_db_stats()
    return {
        "collector": collector.stats,
        "database": db,
        "server_time": int(time.time() * 1000),
    }


@app.get("/api/trades")
async def api_trades(
    coin: str = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    return await get_recent_trades(coin, limit)


@app.get("/api/stats")
async def api_stats(
    coin: str = Query(None),
    hours: int = Query(24, ge=1, le=168),
):
    return await get_trade_stats(coin, hours)


@app.get("/api/price_series")
async def api_price_series(
    coin: str = Query("BTC"),
    minutes: int = Query(60, ge=1, le=1440),
    interval: int = Query(10, ge=5, le=300),
):
    return await get_price_series(coin, minutes, interval)


@app.get("/api/large_trades")
async def api_large_trades(
    coin: str = Query(None),
    min_notional: float = Query(10000),
    limit: int = Query(50, ge=1, le=200),
):
    return await get_large_trades(coin, min_notional, limit)


@app.get("/api/coins")
async def api_coins():
    return await get_available_coins()


@app.get("/api/market_overview")
async def api_market_overview():
    """从 Hyperliquid 实时获取市场概览"""
    try:
        r = requests.post(HL_INFO, json={"type": "allMids"}, timeout=5)
        mids = r.json() if r.status_code == 200 else {}
    except Exception:
        mids = {}

    try:
        r2 = requests.post(HL_INFO, json={"type": "meta"}, timeout=5)
        meta = r2.json() if r2.status_code == 200 else {}
    except Exception:
        meta = {}

    universe = {c["name"]: c for c in meta.get("universe", [])}

    highlights = ["BTC", "ETH", "SOL", "HYPE", "DOGE", "ARB", "SUI"]
    result = []
    for coin in highlights:
        mid = mids.get(coin)
        info = universe.get(coin, {})
        if mid:
            result.append({
                "coin": coin,
                "mid_price": float(mid),
                "max_leverage": info.get("maxLeverage"),
            })

    return {"markets": result, "total_perps": len(universe), "total_mids": len(mids)}


# ── Frontend ────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
