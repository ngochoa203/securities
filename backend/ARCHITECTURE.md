# Securities Backend Architecture & Data Flow Report

## Project Overview
**Location:** `/Users/hoahn/securities/backend/`

Vietnamese Stock Market Prediction backend using FastAPI with three AI prediction models (LSTM, XGBoost, Prophet) in an ensemble, plus technical analysis and rankings engine.

---

## 1. FILE STRUCTURE & PATHS

```
/Users/hoahn/securities/backend/
├── main.py                          # FastAPI entry point with lifespan
├── requirements.txt                 # Dependencies
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── stocks.py                # Stock detail, history, predictions, technical
│       ├── rankings.py              # Top buy/decline/trustworthy/invest rankings
│       └── guide.py                 # Investment guide (not examined)
├── services/
│   ├── __init__.py
│   ├── stock_data.py                # DNSE/Entrade API, caching, data fetching
│   ├── rankings.py                  # Ranking computation logic
│   └── technical.py                 # Technical indicators & signal generation
└── models/
    ├── __init__.py
    ├── ensemble.py                  # EnsemblePredictor: blends 3 models
    ├── lstm_model.py                # LSTMPredictor (stat approximation)
    ├── xgboost_model.py             # XGBoostPredictor
    └── prophet_model.py             # ProphetPredictor
```

---

## 2. KEY DEPENDENCIES (requirements.txt)

```
fastapi==0.115.0              # Web framework
uvicorn[standard]==0.30.0     # ASGI server
vnstock3==0.3.0.9             # Vietnamese stock data
yfinance==0.2.40              # Stock data fallback
pandas==2.2.2                 # Data manipulation
numpy==1.26.4                 # Numerical ops
scikit-learn==1.5.1           # ML utilities
xgboost==2.1.0                # XGBoost model
prophet==1.1.5                # Facebook Prophet
tensorflow==2.16.1            # LSTM backend
pydantic==2.8.0               # Data validation
python-dotenv==1.0.1          # Config management
httpx==0.27.0                 # HTTP client for DNSE API
cachetools==5.4.0             # TTL caching
ta==0.11.0                    # Technical analysis library
```

---

## 3. MAIN.PY: APPLICATION STARTUP & LIFESPAN

**File:** `/Users/hoahn/securities/backend/main.py`

### Key Function: Lifespan Pattern

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm caches on startup"""
    # Startup: Warm caches
    logger.info("🚀 Warming up caches…")
    try:
        get_stock_list()
        get_market_overview()
        logger.info("✅ Cache warm-up complete.")
    except Exception:
        logger.warning("⚠️  Cache warm-up failed (non-critical)")
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutdown.")
```

### FastAPI App Setup
- Title: "Vietnam Securities AI API"
- Version: 1.0.0
- CORS: Allows `localhost:3000`, `localhost:3001`, `127.0.0.1:3000/3001`
- Routes: Includes stocks, rankings, guide routers
- Docs: `/docs`, `/redoc`

### Health Endpoints
- `GET /` → Health status + available endpoints
- `GET /health` → Detailed service status (stock_data, market_overview)

---

## 4. STOCK_DATA.PY: DATA FETCHING & CACHING

**File:** `/Users/hoahn/securities/backend/services/stock_data.py`

### Cache Setup
```python
_cache: TTLCache = TTLCache(maxsize=256, ttl=300)  # 5-minute TTL
```

### Data Source Priority
1. **DNSE / Entrade API** (public, no auth)
2. **vnstock3**
3. **yfinance**
4. **Simulated data** (always succeeds)

---

### 4.1 DNSE/Entrade API Integration

**Base URL:** `https://services.entrade.com.vn`

#### Function: `_fetch_dnse_history(symbol: str, days: int) -> list[dict]`

**Signature:**
```python
def _fetch_dnse_history(symbol: str, days: int) -> list[dict]:
    """
    Fetch OHLCV history from DNSE chart API.
    
    - Prices from DNSE are in units of 1,000 VND (e.g., 72.5 = 72,500 VND)
    - Multiplied by 1,000 before returning (all app uses raw VND)
    - Returns empty list on error (graceful fallback)
    """
```

**API Call Details:**
```
GET {DNSE_BASE_URL}/chart-api/v2/ohlcs/stock
    ?from={ts_from}
    &to={ts_to}
    &symbol={symbol}
    &resolution=1D
```

**Response Format:**
```json
{
    "t": [timestamp1, timestamp2, ...],   // Unix timestamps
    "o": [open1, open2, ...],              // Opening prices (1000x VND)
    "h": [high1, high2, ...],              // High prices
    "l": [low1, low2, ...],                // Low prices
    "c": [close1, close2, ...],            // Closing prices
    "v": [volume1, volume2, ...]           // Volumes
}
```

**Output Format:**
```python
[
    {
        "time":   "2024-04-05",
        "open":   72000.0,      # Already scaled to raw VND
        "high":   73000.0,
        "low":    71000.0,
        "close":  72500.0,
        "volume": 1500000
    },
    ...
]
```

#### Function: `_fetch_dnse_index(symbol: str, days: int = 2) -> dict | None`

Fetches VNINDEX or HNXINDEX (market indices). Similar endpoint `/chart-api/v2/ohlcs/index`.

**Returns:**
```python
{
    "value":      1234.56,      # Index value
    "change":     12.34,        # Points changed
    "change_pct": 1.00,         # % change
    "volume":     500000000
}
```

#### Function: `_fetch_dnse_market_overview() -> dict | None`

Combines VNINDEX and HNXINDEX into market overview.

**Returns:**
```python
{
    "vnindex":    {...},         # Index data
    "hnxindex":   {...},         # Index data
    "updated_at": "2024-04-05T..."
}
```

#### Function: `_fetch_dnse_stock_prices(symbols: list[str]) -> dict[str, float]`

Fetches current prices, caches individually under `dnse_price:{SYMBOL}`.

---

### 4.2 Public API Functions

#### `get_stock_list() -> list[dict]`
- Returns top 50 Vietnamese stocks
- Cached: `stock_list` (5 min TTL)
- Tries DNSE first, falls back to simulated prices with realistic changes

**Output:**
```python
[
    {
        "symbol": "VNM",
        "name": "Vinamilk",
        "exchange": "HOSE",
        "sector": "Tiêu dùng",
        "price": 72500.0,
        "change": 500.0,
        "change_pct": 0.69,
        "volume": 1500000
    },
    ...
]
```

#### `get_stock_history(symbol: str, period: str = "1y") -> list[dict]`
- **Cache key:** `history:{symbol}:{period}`
- **Periods:** `1d|5d|1mo|3mo|6mo|1y|2y|5y`
- Tries DNSE → vnstock3 → yfinance → simulated
- Returns normalized OHLCV records

#### `get_stock_info(symbol: str) -> dict`
- **Cache key:** `info:{symbol}`
- Returns metadata + current price + market cap

#### `get_market_overview() -> dict`
- **Cache key:** `market_overview`
- Returns VNINDEX + HNXINDEX summary

---

### 4.3 Data Normalization

#### `_df_to_records(df: pd.DataFrame) -> list[dict]`
Normalizes varied column names to standard format:
- `time/date/Date/datetime` → `time`
- `open/Open` → `open`
- `high/High` → `high`
- `low/Low` → `low`
- `close/Close` → `close`
- `volume/Volume` → `volume`

#### `_simulate_history(symbol: str, days: int = 365) -> pd.DataFrame`
Generates realistic OHLCV using Geometric Brownian Motion:
- Deterministic seed from symbol
- Skips weekends
- Drift: +0.03% daily
- Volatility: ~1.8% std dev

---

## 5. TECHNICAL.PY: TECHNICAL INDICATORS & SIGNALS

**File:** `/Users/hoahn/securities/backend/services/technical.py`

### Technical Indicators Computed

#### Indicator Functions (return latest scalar values)

| Function | Returns | Default Period |
|----------|---------|-----------------|
| `calculate_rsi()` | RSI value | 14 |
| `calculate_macd()` | dict: macd, signal, histogram | EMA 12/26, signal 9 |
| `calculate_bollinger()` | dict: upper, middle, lower, bandwidth, pct_b | 20 |
| `calculate_sma()` | dict: sma_20, sma_50, sma_200 | [20, 50, 200] |
| `calculate_ema()` | dict: ema_12, ema_26 | [12, 26] |
| `calculate_volume_indicators()` | dict: obv, volume_sma | 20-day vol SMA |
| `calculate_atr()` | ATR value | 14 |

#### `calculate_all_indicators(df: pd.DataFrame) -> dict[str, Any]`

**Input:** DataFrame with columns: `close`, `open`, `high`, `low`, `volume`

**Output:** Flat dict of latest indicator values (JSON-friendly)
```python
{
    "close": 72500.0,
    "rsi": 65.2,
    "macd": 123.45,
    "macd_signal": 120.10,
    "macd_histogram": 3.35,
    "bb_upper": 75000.0,
    "bb_middle": 72000.0,
    "bb_lower": 69000.0,
    "bb_pct_b": 0.75,
    "atr": 1500.0,
    "obv": 5000000.0,
    "volume_sma": 1500000.0,
    "sma_20": 71500.0,
    "sma_50": 70000.0,
    "sma_200": 68000.0,
    "ema_12": 72200.0,
    "ema_26": 71900.0,
}
```

---

### Signal Generation

#### `generate_signal(indicators: dict[str, Any]) -> dict[str, Any]`

**Signature:**
```python
def generate_signal(indicators: dict[str, Any]) -> dict[str, Any]:
    """
    Produces Buy / Sell / Hold signal from latest indicator values.
    
    Returns:
        {
            "signal":     "Buy" | "Sell" | "Hold",
            "confidence": 0.0 – 1.0,
            "reasons":    [str, ...]      # Up to 5 reasons
        }
    """
```

**Scoring System (weighted average):**

| Indicator | Rule | Weight | Score |
|-----------|------|--------|-------|
| RSI | < 30 | 2 | +2 (oversold) |
| RSI | > 70 | 2 | -2 (overbought) |
| RSI | 30-45 | 2 | +0.5 (rising) |
| RSI | 55-70 | 2 | -0.5 (falling) |
| MACD | > signal | 2 | +2 (bullish) |
| MACD | < signal | 2 | -2 (bearish) |
| MACD histogram | > 0 | — | +0.5 (momentum) |
| Bollinger %B | < 0.2 | 1 | +1 (oversold) |
| Bollinger %B | > 0.8 | 1 | -1 (overbought) |
| SMA Price > 20 | — | 1.5 | +1 (short-term up) |
| SMA20 > SMA50 | Golden Cross | 1 | +1 (bullish) |

**Signal Logic:**
```
normalised_score = sum_score / sum_weights  ∈ [-1, 1]
confidence = min(|normalised_score| * 0.5 + 0.5, 0.95)  ∈ [0.5, 1.0]

if normalised_score > 0.2:      signal = "Buy"
elif normalised_score < -0.2:   signal = "Sell"
else:                            signal = "Hold"
```

---

## 6. RANKINGS.PY: RANKING COMPUTATION

**File:** `/Users/hoahn/securities/backend/services/rankings.py`

### Core Helper Function

#### `_quick_stats(symbol: str) -> dict[str, Any]`

Fetches 3-month history and computes:
```python
{
    "price":      float,        # Latest close
    "change":     float,        # Δ from prev close
    "change_pct": float,        # % change
    "signal":     str,          # Buy/Sell/Hold
    "confidence": float,        # 0.5-0.95
    "reasons":    list[str]     # Technical reasons
}
```

#### `_enrich(symbol: str, meta: dict) -> dict`

Merges metadata with quick stats:
```python
{
    "symbol": str,
    "name": str,
    "exchange": str,
    "sector": str,
    **_quick_stats()  # price, change, change_pct, signal, confidence, reasons
}
```

---

### Public Ranking Functions

#### `get_top_buy(limit: int = 10) -> list[dict]`
- Scans top 30 stocks
- Filters for `signal == "Buy"`
- Sorts by confidence descending
- Pads with Hold signals if needed

#### `get_top_decline(limit: int = 10) -> list[dict]`
- Scans top 40 stocks
- Sorts by `change_pct` ascending (biggest declines)
- Adds reason: "Giảm X.X% – Có thể là cơ hội mua đáy"

#### `get_trustworthy(limit: int = 10) -> list[dict]`
- Hardcoded blue-chip list (VCB, BID, CTG, VNM, GAS, FPT, SAB, MBB, ACB, TCB)
- Each has a reason: "Ngân hàng lớn nhất Việt Nam, ..."

#### `get_top_invest(limit: int = 10) -> list[dict]`
- Scans top 25 stocks
- Runs ensemble prediction (7-day forecast)
- Computes AI score: `confidence * signal_multiplier * pred_confidence`
  - `signal_multiplier`: Buy=1.0, Hold=0.5, Sell=0.1
- Sorts by AI score
- Adds: `ai_score`, `pred_direction`, `pred_change_7d`, `reason`

---

## 7. ENSEMBLE.PY: PREDICTION MODEL

**File:** `/Users/hoahn/securities/backend/models/ensemble.py`

### Class: `EnsemblePredictor`

#### Constructor
```python
def __init__(self):
    self._lstm    = LSTMPredictor()
    self._xgb     = XGBoostPredictor()
    self._prophet = ProphetPredictor()
```

#### Main Function: `predict()`

**Signature:**
```python
def predict(
    self,
    symbol: str,
    period: str = "1y",           # Training data period
    forecast_days: int = 7,       # Future forecast length
) -> dict[str, Any]:
```

**Process:**
1. Fetch stock history for the period
2. Run each sub-model (LSTM, XGBoost, Prophet)
3. Blend predictions at days 1, 7, 30 using weights:
   - LSTM: 40%
   - XGBoost: 35%
   - Prophet: 25%
4. Calculate ensemble direction and confidence

**Output:**
```python
{
    "symbol":        str,           # e.g., "VNM"
    "current_price": float,         # Latest close price
    "predictions": {
        "1":  float,               # 1-day forecast
        "7":  float,               # 7-day forecast
        "30": float,               # 30-day forecast
    },
    "direction":     "up" | "down",
    "confidence":    float,         # 0.45-0.95
    "model_details": {
        "lstm": {
            "direction": str,
            "confidence": float,
            "weight": 0.40,
        },
        "xgboost": {...},
        "prophet": {...},
    }
}
```

**Direction Logic:**
```python
ensemble_score = sum(model_dir_score * weight for each model)
                where dir_score = ±1.0 * model_confidence
direction = "up" if ensemble_score >= 0 else "down"
confidence = min(|ensemble_score| + 0.45, 0.95)
```

---

## 8. API ROUTES

### 8.1 STOCKS ROUTER

**File:** `/Users/hoahn/securities/backend/api/routes/stocks.py`

**Prefix:** `/api/stocks`

#### `GET /api/stocks`
**Query Params:**
- `exchange`: Filter by HOSE/HNX/UPCOM
- `sector`: Filter by sector name

**Output:**
```python
{
    "total": int,
    "stocks": list[dict],    # From get_stock_list()
    "market": dict           # Market overview
}
```

#### `GET /api/stocks/{symbol}`
**Query Params:**
- `period`: `1d|5d|1mo|3mo|6mo|1y|2y|5y` (default: `1y`)

**Output:**
```python
{
    "symbol": str,
    "name": str,
    "exchange": str,
    "sector": str,
    "price": float,
    "change": float,
    "change_pct": float,
    "volume": int,
    "market_cap": float,
    "history": [
        {
            "date": "2024-04-05",
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": int,
        },
        ...
    ]
}
```

#### `GET /api/stocks/{symbol}/technical`
**Query Params:**
- `period`: Analysis period (default: `6mo`)

**Output:**
```python
{
    "symbol": str,
    "period": str,
    "indicators": {
        "rsi": float,
        "macd": {"line": float, "signal": float, "histogram": float},
        "bollinger": {"upper": float, "middle": float, "lower": float},
        "sma": {"sma_20": float, "sma_50": float, "sma_200": float},
        "ema": {"ema_12": float, "ema_26": float, "ema_50": float},
    },
    "signal": "Buy" | "Sell" | "Hold",
    "signal_confidence": float,
    "reasons": [str, ...]
}
```

#### `GET /api/stocks/{symbol}/predict`
**Query Params:**
- `period`: Training data period (default: `1y`)
- `forecast_days`: Days to forecast, max 30 (default: 7)

**Output:** EnsemblePredictor result (see section 7)

---

### 8.2 RANKINGS ROUTER

**File:** `/Users/hoahn/securities/backend/api/routes/rankings.py`

**Prefix:** `/api/rankings`

#### `GET /api/rankings/top-buy`
**Query:** `limit` (1-50, default 10)

#### `GET /api/rankings/top-decline`
**Query:** `limit` (1-50, default 10)

#### `GET /api/rankings/trustworthy`
**Query:** `limit` (1-20, default 10)

#### `GET /api/rankings/top-invest`
**Query:** `limit` (1-25, default 10)

**Output Format (same for all):**
```python
{
    "category": str,           # e.g., "top-buy"
    "title": str,              # Vietnamese title
    "description": str,        # Vietnamese description
    "count": int,
    "stocks": list[dict]       # Enriched stock data
}
```

---

## 9. DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Entry Point (main.py)               │
│  Startup: Warm caches (get_stock_list, get_market_overview)        │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┬──────────────┬──────────────┐
        │                   │              │              │
        v                   v              v              v
   /api/stocks       /api/rankings    /api/guide        /health
        │                   │              │
        ├─List             ├─top-buy      │
        ├─Detail            ├─top-decline  │
        ├─Technical         ├─trustworthy  │
        └─Predict           └─top-invest   │
        │                   │              │
        v                   v              v
   stock_data.py      rankings.py    (not examined)
        │                   │
        ├─get_stock_list   └─→ _quick_stats(symbol)
        │   │                   │
        │   └─DNSE API──→ _fetch_dnse_stock_prices()
        │       │                │
        │       └─ TTL cache    └─→ _fetch_dnse_history()
        │
        ├─get_stock_history(symbol, period)
        │   │
        │   ├─Try DNSE API → _fetch_dnse_history()
        │   ├─Try vnstock3 → quote.history()
        │   ├─Try yfinance → Ticker.history()
        │   └─Fall back → _simulate_history()
        │       │
        │       └─ TTL cache
        │
        ├─get_stock_info()
        └─get_market_overview()
            │
            └─DNSE: _fetch_dnse_index("VNINDEX", "HNX")

        technical.py
        │
        ├─calculate_all_indicators(df)
        │   ├─calculate_rsi()          [ta library or manual]
        │   ├─calculate_macd()         [ta or EMA-based]
        │   ├─calculate_bollinger()    [ta or manual]
        │   ├─calculate_sma()
        │   ├─calculate_ema()
        │   ├─calculate_volume_indicators()
        │   └─calculate_atr()
        │
        └─generate_signal(indicators)
            └─Returns: {signal, confidence, reasons}

        ensemble.py
        │
        ├─EnsemblePredictor.predict(symbol, period, forecast_days)
        │   │
        │   ├─ get_stock_history() → fetch training data
        │   │
        │   ├─ LSTMPredictor.predict(df, days) → 40% weight
        │   ├─ XGBoostPredictor.predict(df, days) → 35% weight
        │   └─ ProphetPredictor.predict(df, days) → 25% weight
        │
        └─ Blend predictions & direction
            └─Returns: {symbol, current_price, predictions{1,7,30}, 
                        direction, confidence, model_details}
```

---

## 10. CACHING STRATEGY

**Cache:** TTLCache (maxsize=256, ttl=300 seconds / 5 minutes)

| Cache Key | TTL | Content |
|-----------|-----|---------|
| `stock_list` | 5min | All 50 stocks with prices |
| `history:{symbol}:{period}` | 5min | OHLCV records |
| `info:{symbol}` | 5min | Stock metadata + price |
| `market_overview` | 5min | VNINDEX + HNXINDEX |
| `dnse_price:{symbol}` | 5min | Latest close price |

---

## 11. INTEGRATION POINTS FOR REALTIME PRICE POLLING + DISCORD WEBHOOK

### Entry Points to Extend:

1. **Lifespan Startup** (`main.py`)
   - Launch background task for realtime polling
   - Initialize Discord webhook notifier

2. **Stock Data Service** (`stock_data.py`)
   - Add realtime price cache layer
   - Emit price change events

3. **New Service**: `services/realtime_poller.py`
   - Async background task polling DNSE API
   - Emit price alerts on thresholds

4. **New Service**: `services/discord_notifier.py`
   - Async Discord webhook sender
   - Rate limiting + retry logic
   - Message formatting

5. **Event Bus Pattern**
   - Use asyncio.Queue or trio for event propagation
   - Connect poller → notifier → Discord

### Recommended Architecture:

```python
# In main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    poller = RealtimePoller()
    notifier = DiscordNotifier()
    
    poller_task = asyncio.create_task(poller.poll_loop())
    event_loop = asyncio.get_event_loop()
    
    yield
    
    # Shutdown
    poller_task.cancel()

# In services/realtime_poller.py
class RealtimePoller:
    async def poll_loop(self):
        while True:
            prices = await self._fetch_dnse_prices()
            changes = self._detect_changes(prices)
            for alert in changes:
                await EVENT_QUEUE.put(alert)
            await asyncio.sleep(60)  # Poll every minute

# In services/discord_notifier.py
class DiscordNotifier:
    async def notify_loop(self):
        while True:
            alert = await EVENT_QUEUE.get()
            await self.send_webhook(alert)
```

---

## 12. KEY DESIGN PATTERNS

### Data Flow Patterns
- **Priority fallback chain:** DNSE → vnstock3 → yfinance → simulation
- **Graceful degradation:** Empty list on DNSE error allows fallback
- **Deterministic simulation:** Seeded RNG for reproducible synthetic data

### Service Architecture
- **Layered:** API routes → Services → Data layers
- **Dependency injection:** Models instantiated at request time (stocks.py line 28)
- **Caching middleware:** TTLCache reduces API calls

### Signal Processing
- **Weighted scoring:** Multiple indicators with explicit weights
- **Confidence normalization:** Maps score range to [0.5, 1.0]
- **Ensemble prediction:** Separate model weights + blending logic

---

## 13. IMPORTS PATTERN (How Services Connect)

### Stock Data → Technical
```python
# services/rankings.py line 18
from services.technical import calculate_all_indicators, generate_signal
```

### Stock Data → Ensemble
```python
# models/ensemble.py line 14-16
from models.lstm_model import LSTMPredictor
from models.xgboost_model import XGBoostPredictor
from models.prophet_model import ProphetPredictor
from services.stock_data import get_stock_history, get_stock_info
```

### Rankings → Ensemble (Late import)
```python
# services/rankings.py line 172-173 (inside get_top_invest function)
from models.ensemble import EnsemblePredictor  # noqa: PLC0415
ensemble = EnsemblePredictor()
```

### API Routes → Services
```python
# api/routes/stocks.py
from services.stock_data import get_stock_history, get_stock_info, ...
from services.technical import calculate_all_indicators, generate_signal
from models.ensemble import EnsemblePredictor
```

---

## 14. SUMMARY: Adding Realtime Polling + Discord

**Minimal additions needed:**

1. **New file:** `/services/realtime_poller.py`
   - Poll DNSE API every 60 seconds
   - Compare prices to cache
   - Emit alerts on thresholds (e.g., 2% change)

2. **New file:** `/services/discord_notifier.py`
   - Listen to alert queue
   - Format messages with stock data
   - POST to Discord webhook with retry logic

3. **Modify:** `/main.py`
   - Initialize poller + notifier in lifespan startup
   - Launch async polling tasks
   - Clean up on shutdown

4. **Shared event queue:** `asyncio.Queue` or similar

**Configuration:** Environment variables for:
- `DISCORD_WEBHOOK_URL`
- `POLL_INTERVAL` (seconds)
- `PRICE_CHANGE_THRESHOLD` (%)
- `DNSE_SYMBOLS` (comma-separated)

