# Integration Map: Where to Add Realtime Polling & Discord Webhook

## Current Architecture

```
main.py (FastAPI entry + lifespan)
    ↓
    ├─→ api/routes/stocks.py (REST endpoints)
    │   ├─→ services/stock_data.py (DNSE API calls, caching)
    │   ├─→ services/technical.py (RSI, MACD, Bollinger, etc.)
    │   └─→ models/ensemble.py (LSTM + XGBoost + Prophet)
    │
    └─→ api/routes/rankings.py (Curated lists)
        └─→ services/rankings.py
            ├─→ services/stock_data.py
            ├─→ services/technical.py
            └─→ models/ensemble.py
```

---

## Integration Points for New Features

### 1. **Modify: main.py** (Startup/Shutdown)

```python
# Add to lifespan function (after line 46):

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Warming up caches…")
    try:
        get_stock_list()
        get_market_overview()
        logger.info("✅ Cache warm-up complete.")
    except Exception as exc:
        logger.warning("⚠️  Cache warm-up failed (non-critical): %s", exc)
    
    # ─────────────────────────────────────────────────────────────
    # NEW: Start realtime price polling + Discord notifier
    # ─────────────────────────────────────────────────────────────
    from services.realtime_poller import RealtimePoller      # NEW
    from services.discord_notifier import DiscordNotifier    # NEW
    
    poller = RealtimePoller()
    notifier = DiscordNotifier()
    
    # Start background tasks
    poller_task = asyncio.create_task(poller.poll_loop())
    notifier_task = asyncio.create_task(notifier.notify_loop())
    
    logger.info("✅ Realtime poller and Discord notifier started.")
    
    yield
    
    # Cleanup on shutdown
    poller_task.cancel()
    notifier_task.cancel()
    logger.info("🛑 Application shutdown.")
```

### 2. **New File: services/realtime_poller.py**

```python
"""Realtime Price Polling Service"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from services.stock_data import (
    _fetch_dnse_stock_prices,  # Private but accessible
    VN_STOCKS,
    _cache,
)

logger = logging.getLogger("securities.realtime_poller")

# Shared event queue (can use asyncio.Queue or similar)
PRICE_ALERT_QUEUE: asyncio.Queue[dict[str, Any]] = asyncio.Queue()


class RealtimePoller:
    """Background task that polls DNSE API for price updates."""
    
    def __init__(
        self,
        poll_interval: int = 60,              # seconds
        change_threshold: float = 2.0,        # % threshold
        alert_cooldown: int = 300,            # min seconds between alerts per stock
    ):
        self.poll_interval = poll_interval
        self.change_threshold = change_threshold
        self.alert_cooldown = alert_cooldown
        self.last_alert_time: dict[str, float] = {}  # symbol → timestamp
    
    async def poll_loop(self):
        """Main polling loop."""
        logger.info("Starting realtime price polling (interval=%ds)", self.poll_interval)
        
        while True:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                logger.info("Realtime poller cancelled.")
                break
            except Exception as exc:
                logger.error("Error in poll loop: %s", exc)
            
            await asyncio.sleep(self.poll_interval)
    
    async def _poll_once(self):
        """Fetch prices and emit alerts for significant changes."""
        symbols = [s["symbol"] for s in VN_STOCKS]
        
        try:
            prices = await asyncio.to_thread(
                lambda: _fetch_dnse_stock_prices(symbols)
            )
        except Exception as exc:
            logger.debug("Failed to fetch prices: %s", exc)
            return
        
        for symbol in symbols:
            if symbol not in prices:
                continue
            
            new_price = prices[symbol]
            
            # Get old price from cache
            cache_key = f"price:{symbol}"
            old_price = _cache.get(cache_key)
            
            # Store new price
            _cache[cache_key] = new_price
            
            # Check if change exceeds threshold
            if old_price is None:
                continue  # First poll, no baseline
            
            change_pct = abs(new_price - old_price) / old_price * 100
            
            if change_pct < self.change_threshold:
                continue  # Below threshold
            
            # Check cooldown (don't spam same stock)
            now = datetime.now().timestamp()
            last_time = self.last_alert_time.get(symbol, 0)
            if now - last_time < self.alert_cooldown:
                continue  # Still in cooldown
            
            # Update cooldown
            self.last_alert_time[symbol] = now
            
            # Emit alert
            direction = "📈" if new_price > old_price else "📉"
            alert = {
                "symbol": symbol,
                "old_price": old_price,
                "new_price": new_price,
                "change_pct": (new_price - old_price) / old_price * 100,
                "direction": direction,
                "timestamp": datetime.now().isoformat(),
            }
            
            await PRICE_ALERT_QUEUE.put(alert)
            logger.info(
                "Price alert: %s %s %s → %s (%.2f%%)",
                direction, symbol, old_price, new_price, alert["change_pct"]
            )
```

### 3. **New File: services/discord_notifier.py**

```python
"""Discord Webhook Notification Service"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("securities.discord_notifier")

# Import queue from realtime_poller
from services.realtime_poller import PRICE_ALERT_QUEUE


class DiscordNotifier:
    """Background task that sends alerts to Discord webhook."""
    
    def __init__(
        self,
        webhook_url: str | None = None,
        retry_max: int = 3,
        retry_delay: float = 1.0,
    ):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.retry_max = retry_max
        self.retry_delay = retry_delay
        
        if not self.webhook_url:
            logger.warning("DISCORD_WEBHOOK_URL not set – notifications disabled")
    
    async def notify_loop(self):
        """Main notification loop."""
        if not self.webhook_url:
            logger.info("Discord notifier disabled (no webhook URL)")
            return
        
        logger.info("Starting Discord notifier")
        
        while True:
            try:
                alert = await asyncio.wait_for(PRICE_ALERT_QUEUE.get(), timeout=60.0)
                await self._send_alert(alert)
            except asyncio.TimeoutError:
                # Queue empty – no alerts, keep running
                pass
            except asyncio.CancelledError:
                logger.info("Discord notifier cancelled.")
                break
            except Exception as exc:
                logger.error("Error in notify loop: %s", exc)
    
    async def _send_alert(self, alert: dict[str, Any]) -> bool:
        """Send a single alert to Discord webhook with retry logic."""
        message = self._format_message(alert)
        
        for attempt in range(self.retry_max):
            try:
                await self._post_webhook(message)
                logger.info("Alert sent to Discord: %s", alert["symbol"])
                return True
            except Exception as exc:
                logger.warning(
                    "Attempt %d/%d failed: %s",
                    attempt + 1, self.retry_max, exc
                )
                if attempt < self.retry_max - 1:
                    await asyncio.sleep(self.retry_delay)
        
        logger.error("Failed to send Discord alert after %d retries", self.retry_max)
        return False
    
    async def _post_webhook(self, content: str) -> None:
        """POST to Discord webhook (async)."""
        payload = {
            "content": content,
            "username": "Securities Bot",
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(self.webhook_url, json=payload)
            resp.raise_for_status()
    
    def _format_message(self, alert: dict[str, Any]) -> str:
        """Format alert into Discord message."""
        symbol = alert["symbol"]
        direction = alert["direction"]
        old_price = alert["old_price"]
        new_price = alert["new_price"]
        change_pct = alert["change_pct"]
        
        message = (
            f"{direction} **{symbol}** Stock Alert!\n"
            f"```\n"
            f"Old Price: ₫{old_price:,.0f}\n"
            f"New Price: ₫{new_price:,.0f}\n"
            f"Change:    {change_pct:+.2f}%\n"
            f"Time:      {alert['timestamp']}\n"
            f"```"
        )
        
        return message
```

### 4. **New File: .env.example** (for configuration)

```env
# Discord Webhook
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/YOUR_ID/YOUR_TOKEN

# Realtime Polling
POLL_INTERVAL_SECONDS=60
PRICE_CHANGE_THRESHOLD=2.0
NOTIFICATION_COOLDOWN_SECONDS=300
ALERT_SYMBOLS=VNM,TCB,VCB,BID,CTG,MBB,ACB
```

### 5. **Modify: requirements.txt** (Add if needed)

```diff
  fastapi==0.115.0
  uvicorn[standard]==0.30.0
  httpx==0.27.0
+ httpx[http2]==0.27.0      # For async support
  ...
```

---

## Data Flow After Integration

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Startup (main.py)                 │
│         ↓ Lifespan yield point                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Background Task 1: RealtimePoller.poll_loop()              │
│  ┌──────────────────────────────────────┐                   │
│  │ Every 60s:                           │                   │
│  │ 1. Fetch prices: _fetch_dnse_stock_prices() ────→ DNSE  │
│  │ 2. Compare to _cache[f"price:{symbol}"]         API     │
│  │ 3. If change > 2%: emit to PRICE_ALERT_QUEUE   │       │
│  └──────────────────────────────────────┘         │       │
│                        ↓                          │        │
│                 ┌────────────────────┐            │        │
│                 │ PRICE_ALERT_QUEUE  │◄───────────┘        │
│                 └────────────────────┘                     │
│                        ↑                                    │
│  Background Task 2: DiscordNotifier.notify_loop()          │
│  ┌──────────────────────────────────────┐                   │
│  │ Loop: await alert from queue         │                   │
│  │ Format message                        │                   │
│  │ POST to Discord webhook (with retry)  │────→ Discord    │
│  └──────────────────────────────────────┘                   │
│                                                              │
│  HTTP Requests (continue serving as normal)                │
│  ┌──────────────────────────────────────┐                   │
│  │ GET /api/stocks                      │                   │
│  │ GET /api/stocks/{symbol}/predict     │────→ Clients    │
│  │ GET /api/rankings/top-invest         │                   │
│  └──────────────────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

On Shutdown:
  poller_task.cancel() → poll_loop breaks
  notifier_task.cancel() → notify_loop breaks
```

---

## Testing the Integration

```python
# Test 1: Direct DNSE API call
from services.stock_data import _fetch_dnse_stock_prices
prices = _fetch_dnse_stock_prices(["VNM", "TCB"])
print(prices)  # {"VNM": 72500.0, "TCB": 22500.0}

# Test 2: Run poller manually (for testing)
import asyncio
from services.realtime_poller import RealtimePoller

async def test_poller():
    poller = RealtimePoller(poll_interval=5)  # 5 seconds for testing
    await poller._poll_once()

asyncio.run(test_poller())

# Test 3: Send Discord test message
import asyncio
from services.discord_notifier import DiscordNotifier

async def test_discord():
    notifier = DiscordNotifier(
        webhook_url="https://discordapp.com/api/webhooks/..."
    )
    alert = {
        "symbol": "VNM",
        "old_price": 72000,
        "new_price": 73440,
        "change_pct": 2.0,
        "direction": "📈",
        "timestamp": "2024-04-05T12:00:00",
    }
    await notifier._send_alert(alert)

asyncio.run(test_discord())
```

---

## Summary of Changes

| Component | Type | Location | Purpose |
|-----------|------|----------|---------|
| `RealtimePoller` | New Service | `services/realtime_poller.py` | Poll DNSE API every 60s |
| `DiscordNotifier` | New Service | `services/discord_notifier.py` | Send alerts to Discord |
| `PRICE_ALERT_QUEUE` | Shared Queue | `services/realtime_poller.py` | Event bus between services |
| `main.py` | Modified | Lifespan section | Start/stop background tasks |
| `.env.example` | Config | Project root | Document required env vars |

**Lines of code:** ~150 (RealtimePoller) + ~100 (DiscordNotifier) + ~20 (main.py changes) = ~270 LOC

**Existing code touched:** 
- `main.py`: Import and initialize (4 lines in lifespan)
- No breaking changes to existing services

