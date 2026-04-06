# Securities Backend Exploration Report

This directory contains three comprehensive documentation files exploring the Vietnamese stock market prediction backend and providing a roadmap for adding realtime price polling + Discord webhook notifications.

## 📋 Documentation Files

### 1. **ARCHITECTURE.md** (829 lines, 23KB)
**Complete technical architecture & data flow documentation**

Covers:
- ✅ File structure & paths (14 core files)
- ✅ All dependencies (16 packages in requirements.txt)
- ✅ FastAPI startup/lifespan pattern
- ✅ **Stock Data Service** — DNSE/Entrade API integration
  - `_fetch_dnse_history()` function signature & implementation
  - Data source priority chain (DNSE → vnstock3 → yfinance → simulated)
  - Caching strategy (TTLCache, 5-min TTL)
- ✅ **Technical Analysis** — All 7 indicator calculators + signal generation
  - `calculate_all_indicators()` output format
  - `generate_signal()` weighted scoring system
  - RSI, MACD, Bollinger Bands, SMA, EMA, ATR, OBV
- ✅ **Rankings Engine** — Top buy, decline, trustworthy, invest
- ✅ **Ensemble Predictor** — LSTM (40%) + XGBoost (35%) + Prophet (25%)
- ✅ API routes & endpoints documentation
- ✅ Data flow diagrams
- ✅ Integration points for realtime services

**Use this for:** Complete understanding of system architecture and function signatures

---

### 2. **QUICK_REFERENCE.md** (149 lines, 5.2KB)
**Practical quick-lookup guide**

Contains:
- ✅ Key entry point functions & signatures
- ✅ Data fetching APIs (DNSE, caching, normalization)
- ✅ Signal generation API
- ✅ Lifespan startup pattern location
- ✅ Available stock data (50 Vietnamese stocks)
- ✅ Example code patterns for realtime monitoring
- ✅ HTTP client usage with httpx
- ✅ Important implementation notes
- ✅ DNSE API direct testing commands

**Use this for:** Fast lookups during development, function signatures, code examples

---

### 3. **INTEGRATION_MAP.md** (407 lines, 15KB)
**Ready-to-implement integration guide**

Complete working code for:
- ✅ **RealtimePoller** service (~150 LOC)
  - Poll DNSE API every 60 seconds
  - Track price changes against cache
  - Emit alerts when threshold exceeded (2%)
  - Built-in cooldown to prevent spam
  
- ✅ **DiscordNotifier** service (~100 LOC)
  - Listen to alert queue
  - Format messages beautifully
  - POST to Discord webhook with retry logic
  - Async implementation

- ✅ **Main.py modifications** (~20 LOC)
  - Initialize services in lifespan
  - Start background tasks on startup
  - Clean shutdown

- ✅ Configuration template (.env.example)
- ✅ Testing examples
- ✅ Data flow diagram showing integration

**Use this for:** Implementation — copy-paste ready code with full context

---

## 🎯 Quick Start: Understanding the Codebase

### Step 1: Overview (5 min)
Read: **QUICK_REFERENCE.md** sections 1-3

Key takeaway: DNSE API → TTLCache → Public functions

### Step 2: Architecture Deep Dive (15 min)
Read: **ARCHITECTURE.md** sections 1-8

Key takeaway: Layered service architecture with 3 data sources + AI models

### Step 3: Integration Ready (10 min)
Read: **INTEGRATION_MAP.md** section 1-3

Key takeaway: How to add realtime polling without breaking existing code

---

## 🔍 Core Concepts

### Data Flow
```
DNSE API (public, no auth)
    ↓
_fetch_dnse_history(symbol, days) → list[dict]
    ↓
TTLCache (5-min TTL, max 256 entries)
    ↓
get_stock_history() → public API
    ↓
REST endpoints (/api/stocks/*, /api/rankings/*)
Technical analysis & ensemble prediction
    ↓
Client (frontend or realtime poller)
```

### Key Functions You Need to Know

| Function | File | Purpose | Returns |
|----------|------|---------|---------|
| `_fetch_dnse_history()` | stock_data.py | Fetch OHLCV from API | list[dict] with OHLCV |
| `_fetch_dnse_stock_prices()` | stock_data.py | Get current prices | dict[symbol → price] |
| `calculate_all_indicators()` | technical.py | Compute indicators | dict[indicator → value] |
| `generate_signal()` | technical.py | Buy/Sell/Hold signal | {signal, confidence, reasons} |
| `EnsemblePredictor.predict()` | ensemble.py | Forecast prices | {predictions, direction, confidence} |
| `get_stock_list()` | stock_data.py | All 50 stocks + prices | list[dict] |
| `get_stock_history()` | stock_data.py | Historical OHLCV | list[dict] |

---

## 💾 Available Data

**50 Vietnamese stocks** tracked (services/stock_data.py:36-87)

Popular symbols:
- Banks: VCB, BID, CTG, TCB, VPB, ACB, MBB, HDB, STB, LPB, EIB
- Consumer: VNM, SAB, MSN, MWG, PNJ
- Tech: FPT
- Real Estate: VIC, VHM, KDH, NVL, PDR, DXG, VRE, IJC, BCM, IDC, NDN, CEO
- Energy: GAS, PLX, POW, PVS
- And more...

Base prices: ~10,000 to 130,000 VND per share

---

## 🚀 Integration Checklist: Adding Realtime + Discord

From **INTEGRATION_MAP.md**:

- [ ] Create `services/realtime_poller.py` (150 LOC)
- [ ] Create `services/discord_notifier.py` (100 LOC)
- [ ] Modify `main.py` lifespan section (20 LOC)
- [ ] Create `.env.example` with Discord webhook
- [ ] Test with: `asyncio.run(test_poller())`
- [ ] Test Discord: `asyncio.run(test_discord())`
- [ ] Deploy with `DISCORD_WEBHOOK_URL` environment variable

**Total impact:** ~270 new LOC, minimal changes to existing code (non-breaking)

---

## 📊 Architecture Highlights

### Caching
- **Type:** cachetools.TTLCache
- **Size:** 256 entries max
- **TTL:** 300 seconds (5 minutes)
- **Keys:** `stock_list`, `history:{symbol}:{period}`, `dnse_price:{symbol}`, etc.

### Data Sources (Priority Order)
1. DNSE / Entrade (Vietnamese official)
2. vnstock3 (Vietnamese wrapper)
3. yfinance (International)
4. Simulated (deterministic, always works)

### Technical Indicators
- **Momentum:** RSI
- **Trend:** MACD (line, signal, histogram)
- **Volatility:** Bollinger Bands, ATR
- **Moving Averages:** SMA (20, 50, 200), EMA (12, 26)
- **Volume:** OBV, Volume SMA

### AI Models
- **LSTM:** 40% weight (trend extrapolation)
- **XGBoost:** 35% weight (ML prediction)
- **Prophet:** 25% weight (time series decomposition)

Ensemble provides:
- 1-day, 7-day, 30-day price forecasts
- Direction (up/down)
- Confidence score (0.45-0.95)

---

## 🔧 Dependencies

From requirements.txt:
```
fastapi==0.115.0        # Web framework
httpx==0.27.0           # DNSE API client
pandas==2.2.2           # Data manipulation
cachetools==5.4.0       # TTL caching
ta==0.11.0              # Technical indicators
prophet==1.1.5          # Facebook Prophet
xgboost==2.1.0          # XGBoost model
tensorflow==2.16.1      # LSTM backend
```

---

## 📞 Where to Ask Questions

**File → Where in Documentation:**
- How does DNSE API work? → ARCHITECTURE.md section 4.1
- Function signatures? → QUICK_REFERENCE.md section 1-2
- How to implement realtime polling? → INTEGRATION_MAP.md section 2
- What's the caching strategy? → ARCHITECTURE.md section 10
- How do technical indicators work? → ARCHITECTURE.md section 5
- Complete data flow? → ARCHITECTURE.md section 9

---

## ✅ Exploration Scope (What Was Covered)

| Item | ✅ Covered | File |
|------|-----------|------|
| stock_data.py | ✅ Complete | ARCHITECTURE + QUICK_REFERENCE |
| services/rankings.py | ✅ Complete | ARCHITECTURE section 6 |
| services/technical.py | ✅ Complete | ARCHITECTURE section 5 |
| models/ensemble.py | ✅ Complete | ARCHITECTURE section 7 |
| main.py startup/lifespan | ✅ Complete | ARCHITECTURE section 3 |
| requirements.txt | ✅ Complete | ARCHITECTURE section 2 |
| API routes | ✅ Complete | ARCHITECTURE section 8 |
| Function signatures | ✅ Complete | All documents |
| Import patterns | ✅ Complete | ARCHITECTURE section 13 |
| Data flow | ✅ Complete | ARCHITECTURE section 9 & INTEGRATION_MAP |

---

## 📄 Document Sizes

- **ARCHITECTURE.md:** 829 lines (23KB) — Comprehensive reference
- **QUICK_REFERENCE.md:** 149 lines (5.2KB) — Practical guide
- **INTEGRATION_MAP.md:** 407 lines (15KB) — Implementation guide
- **Total:** 1,385 lines, 43KB of documentation

---

## 🎓 Learning Path

**Beginner (30 min total):**
1. QUICK_REFERENCE.md (5 min) — Key functions
2. ARCHITECTURE.md section 9 (10 min) — Data flow diagram
3. INTEGRATION_MAP.md section 1 (15 min) — Current architecture

**Intermediate (1 hour total):**
1. ARCHITECTURE.md sections 1-7 (30 min) — Each service
2. QUICK_REFERENCE.md section 1-4 (10 min) — Function details
3. INTEGRATION_MAP.md section 2-3 (20 min) — Code templates

**Advanced (2+ hours):**
1. Read all three documents thoroughly
2. Study actual code alongside documentation
3. Implement realtime polling + Discord using templates

---

**Generated:** 2024-04-05  
**Project:** Vietnamese Stock Market Prediction Backend  
**Purpose:** Architecture exploration & integration planning
