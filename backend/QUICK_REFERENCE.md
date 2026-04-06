# Securities Backend - Quick Reference for Realtime Polling & Discord Integration

## Key Entry Points

### 1. Data Fetching
- **Primary:** `_fetch_dnse_history(symbol: str, days: int) -> list[dict]`
  - Location: `services/stock_data.py:200`
  - Returns: `[{"time": "2024-04-05", "open": 72000, "high": 73000, "low": 71000, "close": 72500, "volume": 1500000}, ...]`
  - DNSE prices in units of 1000 VND (scaled to raw VND before return)
  - Endpoint: `GET https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={ts}&to={ts}&symbol={SYM}&resolution=1D`

- **Current Prices:** `_fetch_dnse_stock_prices(symbols: list[str]) -> dict[str, float]`
  - Returns: `{"VNM": 72500.0, "TCB": 22500.0, ...}`
  - Already cached individually (5 min TTL)

### 2. Signal Generation
- `generate_signal(indicators: dict) -> {"signal": "Buy|Sell|Hold", "confidence": 0.5-0.95, "reasons": [...]}`
  - Location: `services/technical.py:228`
  - Input: Flat dict of latest indicator values (from `calculate_all_indicators()`)

### 3. Lifespan/Startup
- `main.py:34-50` — Async context manager for startup/shutdown
- Warm caches on startup: `get_stock_list()`, `get_market_overview()`
- Perfect place to launch background polling tasks

### 4. Caching
- **Type:** `TTLCache(maxsize=256, ttl=300)` (5-minute TTL)
- **Location:** `services/stock_data.py:31`
- Cache keys:
  - `stock_list` — all 50 stocks
  - `history:{symbol}:{period}` — OHLCV records
  - `dnse_price:{symbol}` — latest close price
  - `market_overview` — VNINDEX + HNXINDEX
  - `info:{symbol}` — stock metadata

## Function Signatures Summary

```python
# Data Fetching
_fetch_dnse_history(symbol: str, days: int) -> list[dict]
_fetch_dnse_stock_prices(symbols: list[str]) -> dict[str, float]
get_stock_list() -> list[dict]
get_stock_history(symbol: str, period: str = "1y") -> list[dict]
get_stock_info(symbol: str) -> dict
get_market_overview() -> dict

# Technical Analysis
calculate_all_indicators(df: pd.DataFrame) -> dict[str, Any]
generate_signal(indicators: dict[str, Any]) -> dict[str, Any]

# Rankings
_quick_stats(symbol: str) -> dict[str, Any]
get_top_buy(limit: int = 10) -> list[dict]
get_top_decline(limit: int = 10) -> list[dict]
get_top_invest(limit: int = 10) -> list[dict]

# Prediction
EnsemblePredictor().predict(
    symbol: str,
    period: str = "1y",
    forecast_days: int = 7
) -> dict[str, Any]
```

## Available Stock Data

**Top 50 Vietnamese stocks:** `VN_STOCKS` (services/stock_data.py:36)

Sample symbols: VNM, FPT, VIC, VHM, HPG, MSN, MWG, TCB, VPB, ACB, BID, CTG, VCB, SSI, VND, HDB, STB, MBB, LPB, EIB, GAS, PLX, POW, REE, SAB, DGC, DCM, DPM, GMD, PNJ, KDH, NVL, PDR, DXG, VRE, IJC, BCM, VGC, HSG, NKG, TVS, SHS, PVS, HUT, PVC, VCS, IDC, NDN, CEO, L14

Base prices: `_BASE_PRICES` dict (e.g., VNM: 72000, TCB: 22000, VCB: 88000)

## Example: Building Realtime Price Monitor

```python
# 1. Poll DNSE for price updates
symbols = ["VNM", "TCB", "VCB"]
prices = await _fetch_dnse_stock_prices(symbols)  # {"VNM": 72500, ...}

# 2. Detect price changes
old_price = cache.get(f"price:{symbol}")
new_price = prices[symbol]
if abs(new_price - old_price) / old_price > 0.02:  # 2% threshold
    change_pct = (new_price - old_price) / old_price * 100
    # Emit alert to Discord
    
# 3. Get signal + indicators
history = get_stock_history(symbol, period="6mo")
df = pd.DataFrame(history)
indicators = calculate_all_indicators(df)
signal = generate_signal(indicators)  # {"signal": "Buy", "confidence": 0.85, ...}

# 4. Discord message example
message = (
    f"🚀 **{symbol}** price update!\n"
    f"New price: ₫{new_price:,.0f} ({change_pct:+.2f}%)\n"
    f"Signal: {signal['signal']} (confidence: {signal['confidence']})\n"
    f"Reasons: {', '.join(signal['reasons'][:3])}"
)
```

## HTTP Client Usage

```python
import httpx

# DNSE API uses httpx with timeout=10
with httpx.Client(timeout=10) as client:
    resp = client.get(url)
    data = resp.json()
```

Currently uses httpx==0.27.0

## Important Notes

1. **DNSE Price Units:** Returned prices are in units of 1000 VND. The code multiplies by 1000 before returning to app.

2. **Fallback Chain:** DNSE → vnstock3 → yfinance → simulated. If DNSE fails, automatically falls back.

3. **Time Format:** DNSE returns Unix timestamps, converted to `%Y-%m-%d` strings in records.

4. **Threading:** FastAPI is async. Use `asyncio.Queue` for event communication between background tasks.

5. **Imports Pattern:** Delayed imports in functions (e.g., `# noqa: PLC0415`) to avoid circular deps.

## Config Needs for Realtime Service

```python
# Environment variables
DISCORD_WEBHOOK_URL: str           # Discord webhook URL
POLL_INTERVAL_SECONDS: int = 60    # Poll frequency
PRICE_CHANGE_THRESHOLD: float = 2.0  # % change threshold
ALERT_SYMBOLS: str                 # Comma-separated: "VNM,TCB,VCB"
NOTIFICATION_COOLDOWN: int = 300   # Min seconds between alerts per stock
```

## Testing DNSE API Directly

```bash
# Example: Fetch VNM history for last 7 days
timestamp=$(date +%s)
from_ts=$((timestamp - 7*86400))
curl "https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from=$from_ts&to=$timestamp&symbol=VNM&resolution=1D"

# Response:
# {"t": [1712188800, ...], "o": [72.5, ...], "h": [73.0, ...], ...}
```

