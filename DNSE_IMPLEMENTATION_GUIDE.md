# DNSE Integration Implementation Guide

This guide provides step-by-step instructions for integrating DNSE API into your existing stock data service.

---

## 1. Installation

```bash
# Install the dnse-morphe library
pip install dnse-morphe

# Verify installation
python -c "from dnse_morphe import DNSEClient; print('✓ dnse-morphe installed')"
```

---

## 2. Environment Setup

Add to your `.env` file or environment variables:

```bash
# DNSE API Credentials
DNSE_API_KEY=your_api_key_here
DNSE_API_SECRET=your_api_secret_here

# Optional: Switch between environments
DNSE_ENV=production  # or "uat"
```

---

## 3. Update Backend - Minimal Integration

### Option A: Add DNSE as First Data Source (Recommended)

Modify `/Users/hoahn/securities/backend/services/stock_data.py`:

```python
import os
from dnse_morphe import DNSEClient
from dnse_morphe._exception import APIError

# Initialize DNSE client
_dnse_client = None

def _get_dnse_client():
    global _dnse_client
    if _dnse_client is None:
        api_key = os.getenv("DNSE_API_KEY")
        api_secret = os.getenv("DNSE_API_SECRET")
        
        if api_key and api_secret:
            _dnse_client = DNSEClient(
                api_key=api_key,
                api_secret=api_secret,
                base_url="https://openapi.dnse.com.vn",
                timeout=30.0,
            )
    return _dnse_client

def get_stock_history(symbol: str, period: str = "1y") -> list[dict]:
    """
    Return historical OHLCV data for a symbol.
    Tries DNSE first, then vnstock3, then yfinance, then falls back to simulation.
    """
    cache_key = f"history:{symbol}:{period}"
    if cache_key in _cache:
        return _cache[cache_key]

    symbol = symbol.upper()
    days = _period_to_days(period)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # --- Try DNSE FIRST ---
    try:
        dnse_client = _get_dnse_client()
        if dnse_client:
            ohlc_list = dnse_client.market_data.get_ohlc(
                bar_type="stock",
                symbol=symbol,
                from_date=start_date,
                to_date=end_date,
                resolution="1d",
                page_size=500,
            )
            if ohlc_list:
                records = [
                    {
                        "time": ohlc.time.strftime("%Y-%m-%d") if hasattr(ohlc.time, 'strftime') else str(ohlc.time),
                        "open": float(ohlc.open),
                        "high": float(ohlc.high),
                        "low": float(ohlc.low),
                        "close": float(ohlc.close),
                        "volume": int(ohlc.volume),
                    }
                    for ohlc in ohlc_list
                ]
                _cache[cache_key] = records
                return records
    except (APIError, Exception):
        pass  # Fall through to next source

    # --- Try vnstock3 (existing code) ---
    try:
        from vnstock3 import Vnstock  # noqa: PLC0415
        vs = Vnstock().stock(symbol=symbol, source="VCI")
        df = vs.quote.history(start=start_date, end=end_date)
        if df is not None and not df.empty:
            records = _df_to_records(df)
            if records:
                _cache[cache_key] = records
                return records
    except Exception:
        pass

    # --- Try yfinance (existing code) ---
    try:
        import yfinance as yf  # noqa: PLC0415
        ticker_sym = f"{symbol}.VN" if symbol in _STOCK_MAP else symbol
        tkr = yf.Ticker(ticker_sym)
        df = tkr.history(period=period)
        if df is not None and not df.empty:
            records = _df_to_records(df)
            if records:
                _cache[cache_key] = records
                return records
    except Exception:
        pass

    # --- Simulation fallback (existing code) ---
    df = _simulate_history(symbol, days)
    records = df.to_dict("records")
    _cache[cache_key] = records
    return records
```

---

## 4. Add Real-Time Price Streaming (Optional)

Create a new module `/Users/hoahn/securities/backend/services/realtime_prices.py`:

```python
"""
Real-time stock price streaming via DNSE WebSocket
"""

import asyncio
import json
import logging
from typing import Callable, Dict, List

from dnse_morphe import AsyncDNSEClient

logger = logging.getLogger(__name__)

class DnsePriceStreamer:
    def __init__(self, api_key: str, api_secret: str):
        self.client = AsyncDNSEClient(
            api_key=api_key,
            api_secret=api_secret,
        )
        self.callbacks: Dict[str, List[Callable]] = {}
        self.connected = False

    async def start(self, symbols: List[str]):
        """Start streaming quotes for given symbols"""
        try:
            async with self.client.websocket(encoding="json") as ws:
                self.connected = True
                logger.info(f"Connected to DNSE WebSocket")
                
                # Subscribe to quotes
                await ws.subscribe_quotes(symbols)
                logger.info(f"Subscribed to quotes: {symbols}")
                
                # Register handler
                def on_quote(quote):
                    """Handle incoming quote"""
                    logger.debug(f"Quote: {quote.symbol} - Bid: {quote.best_bid}, Ask: {quote.best_ask}")
                    
                    # Trigger callbacks
                    if quote.symbol in self.callbacks:
                        for callback in self.callbacks[quote.symbol]:
                            try:
                                callback({
                                    "symbol": quote.symbol,
                                    "bid": quote.best_bid[0] if quote.best_bid else None,
                                    "bid_volume": quote.best_bid[1] if quote.best_bid else None,
                                    "ask": quote.best_ask[0] if quote.best_ask else None,
                                    "ask_volume": quote.best_ask[1] if quote.best_ask else None,
                                    "timestamp": quote.timestamp,
                                })
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                
                ws.on("quote", on_quote)
                
                # Keep connection alive
                while True:
                    await asyncio.sleep(60)
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.connected = False
            # Reconnect after delay
            await asyncio.sleep(5)
            await self.start(symbols)

    def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to price updates for a symbol"""
        if symbol not in self.callbacks:
            self.callbacks[symbol] = []
        self.callbacks[symbol].append(callback)

    def unsubscribe(self, symbol: str, callback: Callable):
        """Unsubscribe from price updates"""
        if symbol in self.callbacks:
            self.callbacks[symbol].remove(callback)


# Usage example:
# streamer = DnsePriceStreamer(api_key, api_secret)
# streamer.subscribe("VND", lambda quote: print(f"Price update: {quote}"))
# asyncio.run(streamer.start(["VND", "HPG", "VNM"]))
```

---

## 5. Get Security Definition (Price Limits)

Add this to `stock_data.py` for market cap and price limits:

```python
def get_stock_info(symbol: str) -> dict:
    """Return stock detail: name, exchange, sector, and price limits."""
    cache_key = f"info:{symbol}"
    if cache_key in _cache:
        return _cache[cache_key]

    symbol = symbol.upper()
    base_info = _STOCK_MAP.get(symbol, {
        "symbol": symbol,
        "name": symbol,
        "exchange": "HOSE",
        "sector": "Khác",
    })

    price_info: dict = {}

    # --- Try DNSE for security definition and price ---
    try:
        dnse_client = _get_dnse_client()
        if dnse_client:
            sec_def = dnse_client.market_data.get_security_definition(symbol)
            price_info["ceiling_price"] = float(sec_def.ceiling_price)
            price_info["floor_price"] = float(sec_def.floor_price)
            price_info["ref_price"] = float(sec_def.ref_price)
            price_info["lot_size"] = int(sec_def.lot_size)
            
            # Get latest price from OHLC
            today = datetime.now().strftime("%Y-%m-%d")
            ohlc_list = dnse_client.market_data.get_ohlc(
                bar_type="stock",
                symbol=symbol,
                from_date=today,
                to_date=today,
                resolution="1d",
            )
            if ohlc_list:
                price_info["price"] = float(ohlc_list[-1].close)
    except Exception:
        pass

    # --- Fall back to existing logic ---
    if "price" not in price_info:
        hist = get_stock_history(symbol, period="5d")
        last = hist[-1] if hist else {}
        price_info["price"] = last.get("close", _BASE_PRICES.get(symbol, 30000))
    
    if "market_cap" not in price_info:
        rng = random.Random(_seed_for(symbol))
        shares = rng.randint(300_000_000, 5_000_000_000)
        price_info["market_cap"] = price_info.get("price", 30000) * shares

    result = {
        **base_info,
        **price_info,
    }
    _cache[cache_key] = result
    return result
```

---

## 6. API Routes Integration

Update your Flask/FastAPI routes to use the enhanced service:

### Flask Example:

```python
from flask import Flask, jsonify
from backend.services.stock_data import (
    get_stock_list,
    get_stock_history,
    get_stock_info,
    get_market_overview,
)

app = Flask(__name__)

@app.route("/api/stocks", methods=["GET"])
def stocks():
    """Get list of Vietnamese stocks with current prices"""
    return jsonify(get_stock_list())

@app.route("/api/stocks/<symbol>", methods=["GET"])
def stock_detail(symbol):
    """Get stock detail including price limits"""
    return jsonify(get_stock_info(symbol))

@app.route("/api/stocks/<symbol>/history", methods=["GET"])
def stock_history(symbol):
    """Get historical OHLCV data"""
    period = request.args.get("period", "1y")
    return jsonify(get_stock_history(symbol, period))

@app.route("/api/market/overview", methods=["GET"])
def market_overview():
    """Get market overview"""
    return jsonify(get_market_overview())
```

---

## 7. Error Handling

Implement proper error handling:

```python
from dnse_morphe._exception import (
    AuthenticationError,
    RateLimitError,
    APIError,
    ConnectionError as DNSEConnectionError,
)

def safe_dnse_call(func, *args, **kwargs):
    """Safely call DNSE API with fallback"""
    try:
        return func(*args, **kwargs)
    except AuthenticationError:
        logger.error("DNSE: Invalid API credentials")
        return None
    except RateLimitError:
        logger.warning("DNSE: Rate limit exceeded, retrying...")
        return None
    except DNSEConnectionError:
        logger.error("DNSE: Connection error")
        return None
    except APIError as e:
        logger.error(f"DNSE API Error: {e.status} - {e.body}")
        return None
    except Exception as e:
        logger.error(f"DNSE: Unexpected error: {e}")
        return None
```

---

## 8. Testing

Create a test script `/Users/hoahn/securities/test_dnse_integration.py`:

```python
"""Test DNSE integration"""

import os
from dnse_morphe import DNSEClient

def test_dnse_connection():
    """Test DNSE API connection"""
    api_key = os.getenv("DNSE_API_KEY")
    api_secret = os.getenv("DNSE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ DNSE credentials not found in environment")
        return False
    
    try:
        client = DNSEClient(
            api_key=api_key,
            api_secret=api_secret,
        )
        
        # Test security definition
        print("Testing security definition...")
        sec_def = client.market_data.get_security_definition("VND")
        print(f"✓ VND: Ceiling={sec_def.ceiling_price}, Floor={sec_def.floor_price}")
        
        # Test OHLC
        print("Testing OHLC data...")
        ohlc_list = client.market_data.get_ohlc(
            bar_type="stock",
            symbol="VND",
            from_date="2024-01-01",
            to_date="2024-01-02",
            resolution="1d",
        )
        print(f"✓ Got {len(ohlc_list)} candles for VND")
        
        # Test multiple symbols
        print("Testing multiple symbols...")
        symbols = ["VND", "HPG", "VNM"]
        for symbol in symbols:
            sec_def = client.market_data.get_security_definition(symbol)
            print(f"✓ {symbol}: {sec_def.symbol}")
        
        print("\n✅ All DNSE tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ DNSE test failed: {e}")
        return False

if __name__ == "__main__":
    test_dnse_connection()
```

Run tests:
```bash
export DNSE_API_KEY="your_key"
export DNSE_API_SECRET="your_secret"
python test_dnse_integration.py
```

---

## 9. Monitoring & Logging

Add structured logging:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logger = logging.getLogger("dnse_service")
logger.setLevel(logging.INFO)

# File handler
file_handler = RotatingFileHandler(
    "logs/dnse_api.log",
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
```

---

## 10. Production Checklist

- [ ] Environment variables set correctly
- [ ] API credentials validated
- [ ] Error handling implemented
- [ ] Fallback sources working
- [ ] Caching configured (5min TTL)
- [ ] Logging configured
- [ ] Rate limiting handled
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Monitoring alerts set

---

## Troubleshooting

### Issue: Authentication Error

```
from dnse_morphe._exception import AuthenticationError
# Solution: Verify DNSE_API_KEY and DNSE_API_SECRET in environment
```

### Issue: Rate Limiting

```
from dnse_morphe._exception import RateLimitError
# Solution: Implement exponential backoff and request throttling
```

### Issue: Connection Timeout

```
# Solution: Increase timeout in client initialization
client = DNSEClient(
    api_key=api_key,
    api_secret=api_secret,
    timeout=60.0  # Increase from default 30s
)
```

---

## References

- DNSE API Docs: https://developers.dnse.com.vn
- dnse-morphe GitHub: https://github.com/dinhhongkong/dnse-morphe
- Python Async: https://docs.python.org/3/library/asyncio.html

