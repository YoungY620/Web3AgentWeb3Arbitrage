import aiosqlite
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trades.db")


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                tid        INTEGER PRIMARY KEY,
                coin       TEXT    NOT NULL,
                side       TEXT    NOT NULL,
                px         REAL    NOT NULL,
                sz         REAL    NOT NULL,
                notional   REAL    NOT NULL,
                time_ms    INTEGER NOT NULL,
                hash       TEXT,
                users      TEXT
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_coin_time
            ON trades (coin, time_ms DESC)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_time
            ON trades (time_ms DESC)
        """)
        await db.commit()


async def insert_trades(trades: list[dict]):
    if not trades:
        return 0
    async with aiosqlite.connect(DB_PATH) as db:
        inserted = 0
        for t in trades:
            try:
                px = float(t.get("px", 0))
                sz = float(t.get("sz", 0))
                await db.execute(
                    "INSERT OR IGNORE INTO trades (tid, coin, side, px, sz, notional, time_ms, hash, users) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        t.get("tid"),
                        t.get("coin", ""),
                        t.get("side", ""),
                        px,
                        sz,
                        px * sz,
                        t.get("time", 0),
                        t.get("hash", ""),
                        str(t.get("users", [])),
                    ),
                )
                inserted += 1
            except Exception:
                pass
        await db.commit()
        return inserted


async def get_recent_trades(coin: str = None, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if coin:
            cursor = await db.execute(
                "SELECT * FROM trades WHERE coin = ? ORDER BY time_ms DESC LIMIT ?",
                (coin, limit),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM trades ORDER BY time_ms DESC LIMIT ?",
                (limit,),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_trade_stats(coin: str = None, hours: int = 24):
    cutoff = int((time.time() - hours * 3600) * 1000)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if coin:
            cursor = await db.execute(
                """
                SELECT coin,
                       COUNT(*)            as trade_count,
                       SUM(notional)       as total_volume,
                       AVG(px)             as avg_price,
                       MIN(px)             as min_price,
                       MAX(px)             as max_price,
                       MIN(time_ms)        as first_trade,
                       MAX(time_ms)        as last_trade
                FROM trades
                WHERE coin = ? AND time_ms >= ?
                GROUP BY coin
                """,
                (coin, cutoff),
            )
        else:
            cursor = await db.execute(
                """
                SELECT coin,
                       COUNT(*)            as trade_count,
                       SUM(notional)       as total_volume,
                       AVG(px)             as avg_price,
                       MIN(px)             as min_price,
                       MAX(px)             as max_price,
                       MIN(time_ms)        as first_trade,
                       MAX(time_ms)        as last_trade
                FROM trades
                WHERE time_ms >= ?
                GROUP BY coin
                ORDER BY total_volume DESC
                """,
                (cutoff,),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_price_series(coin: str, minutes: int = 60, interval_sec: int = 10):
    """按时间间隔聚合价格序列，用于绘图"""
    cutoff = int((time.time() - minutes * 60) * 1000)
    interval_ms = interval_sec * 1000
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT (time_ms / ?) * ? as bucket,
                   AVG(px)            as avg_px,
                   SUM(sz)            as total_sz,
                   SUM(notional)      as total_notional,
                   COUNT(*)           as cnt
            FROM trades
            WHERE coin = ? AND time_ms >= ?
            GROUP BY bucket
            ORDER BY bucket ASC
            """,
            (interval_ms, interval_ms, coin, cutoff),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_large_trades(coin: str = None, min_notional: float = 10000, limit: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if coin:
            cursor = await db.execute(
                "SELECT * FROM trades WHERE coin = ? AND notional >= ? ORDER BY time_ms DESC LIMIT ?",
                (coin, min_notional, limit),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM trades WHERE notional >= ? ORDER BY time_ms DESC LIMIT ?",
                (min_notional, limit),
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_available_coins():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT DISTINCT coin, COUNT(*) as cnt FROM trades GROUP BY coin ORDER BY cnt DESC"
        )
        rows = await cursor.fetchall()
        return [{"coin": r[0], "count": r[1]} for r in rows]


async def get_db_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM trades")
        total = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT MIN(time_ms), MAX(time_ms) FROM trades")
        row = await cursor.fetchone()
        return {
            "total_trades": total,
            "earliest_ms": row[0],
            "latest_ms": row[1],
            "db_path": DB_PATH,
        }
