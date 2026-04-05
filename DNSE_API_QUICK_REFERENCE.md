# DNSE API Quick Reference

## 🎯 Key Endpoints

### Market Data (REST)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/price/secdef/{symbol}` | GET | Get security definition (ceiling, floor, lot size) |
| `/price/ohlc` | GET | Get OHLC/candle data |

### Query Parameters for OHLC
```
type=stock          # Required: "stock"
symbol=VND          # Required: Stock symbol
from=2024-01-01     # Start date
to=2024-01-02       # End date
resolution=1d       # 1m, 5m, 15m, 30m, 1h, 1d, 1w
pageSize=100        # Items per page
pageIndex=1         # Page number
```

### Response Format
```json
[
  {
    "time": "2024-01-01T09:30:00",
    "open": 50.0,
    "high": 50.5,
    "low": 49.8,
    "close": 50.2,
    "volume": 1500000
  }
]
```

---

## 📡 Base URLs

| Environment | REST | WebSocket |
|---|---|---|
| Production | `https://openapi.dnse.com.vn` | `wss://ws-openapi.dnse.com.vn` |
| UAT | - | `wss://ws-openapi-uat.dnse.com.vn` |

---

## 🔐 Authentication

**Type**: HMAC-SHA256 signature  
**Headers Required**:
- `Date`: RFC 2822 format
- `Authorization`: Signature with algorithm="hmac-sha256"
- `Content-Type`: "application/json"

---

## 🚀 Python Quick Start

```python
from dnse_morphe import DNSEClient

# Initialize
client = DNSEClient(
    api_key="your_key",
    api_secret="your_secret",
    base_url="https://openapi.dnse.com.vn"
)

# Get OHLC data
ohlc = client.market_data.get_ohlc(
    bar_type="stock",
    symbol="VND",
    resolution="1d",
    from_date="2024-01-01",
    to_date="2024-01-31"
)

# Get security definition
sec_def = client.market_data.get_security_definition("VND")

# WebSocket streaming
async with client.websocket() as ws:
    await ws.subscribe_quotes(["VND", "HPG"])
    ws.on("quote", lambda q: print(f"{q.symbol}: {q.best_bid} | {q.best_ask}"))
    await asyncio.sleep(3600)
```

---

## 📊 Popular Vietnamese Stocks

| Symbol | Company | Exchange |
|--------|---------|----------|
| VNM | Vinamilk | HOSE |
| HPG | Hòa Phát Group | HOSE |
| VND | VND Direct | HOSE |
| VIC | Vingroup | HOSE |
| VHM | Vinhomes | HOSE |
| FPT | FPT Corporation | HOSE |
| TCB | Techcombank | HOSE |
| VCB | Vietcombank | HOSE |
| MSN | Masan Group | HOSE |
| MWG | Mobile World | HOSE |

---

## 🔗 Resources

- **Official API**: https://developers.dnse.com.vn
- **Python Library**: https://github.com/dinhhongkong/dnse-morphe
- **Contact**: hello@dnse.com.vn | +84 247 108 9234

---

## ⚠️ Websocket Channels

**Public**:
- `subscribe_trades(symbols)` - Real-time trades
- `subscribe_quotes(symbols)` - Real-time bid/ask
- `subscribe_ohlc(symbols, resolution)` - Real-time candles

**Private** (requires auth):
- `subscribe_orders()` - Order updates
- `subscribe_positions()` - Position updates
- `subscribe_account()` - Balance updates

---

## 🎁 Integration with Current Backend

Current system uses: **vnstock3** → **yfinance** → **Simulation**

Recommended addition: **DNSE** → **vnstock3** → **yfinance** → **Simulation**

```python
# Add to stock_data.py
from dnse_morphe import DNSEClient

client = DNSEClient(
    api_key=os.getenv("DNSE_API_KEY"),
    api_secret=os.getenv("DNSE_API_SECRET"),
)

# Try DNSE first before vnstock3
try:
    ohlc = client.market_data.get_ohlc(
        bar_type="stock",
        symbol=symbol,
        resolution="1d",
        from_date=start_date,
        to_date=end_date,
    )
    return ohlc  # Success
except:
    # Fall back to existing vnstock3 logic
    pass
```

