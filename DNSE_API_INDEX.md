# DNSE API Research & Integration - Complete Documentation Index

## 📚 Overview

This directory contains comprehensive research and implementation guides for integrating the **DNSE LightSpeed API V2** (Vietnamese stock market API) into your securities platform.

---

## 📋 Documentation Files

### 1. **DNSE_API_RESEARCH.md** ⭐ (Main Reference)
   **Size**: ~14 KB  
   **Purpose**: Comprehensive technical documentation
   
   Contains:
   - Executive summary
   - Complete API endpoints listing
   - Market Data endpoints (`/price/secdef`, `/price/ohlc`)
   - Account & Order endpoints
   - WebSocket streaming configuration
   - Authentication details (HMAC-SHA256)
   - Data types & response models
   - Error handling strategies
   - Integration recommendations
   
   **When to use**: Full technical reference, API details, implementation planning

---

### 2. **DNSE_API_QUICK_REFERENCE.md** 🚀 (Quick Lookup)
   **Size**: ~3.4 KB  
   **Purpose**: Quick lookup guide for developers
   
   Contains:
   - Key endpoints table
   - Query parameters
   - Base URLs
   - Python code examples
   - Popular Vietnamese stocks
   - WebSocket channels
   - Integration tips
   
   **When to use**: Quick coding reference, copy-paste examples

---

### 3. **DNSE_IMPLEMENTATION_GUIDE.md** 💻 (Step-by-Step)
   **Size**: ~8 KB  
   **Purpose**: Step-by-step integration guide
   
   Contains:
   - Installation instructions
   - Environment setup
   - Code examples (minimal to advanced)
   - Real-time streaming setup
   - Security definitions integration
   - API routes integration
   - Error handling patterns
   - Testing instructions
   - Production checklist
   - Troubleshooting guide
   
   **When to use**: During implementation, testing, deployment

---

### 4. **DNSE_API_INDEX.md** 📑 (This File)
   Navigation guide and quick reference for all documentation

---

## 🎯 Quick Start

### For Developers (First Time)
1. Read **DNSE_API_QUICK_REFERENCE.md** (5 min)
2. Follow **DNSE_IMPLEMENTATION_GUIDE.md** section 1-3 (15 min)
3. Run test script (5 min)
4. Refer to **DNSE_API_RESEARCH.md** for details as needed

### For Architects (Planning)
1. Read **DNSE_API_RESEARCH.md** Executive Summary (5 min)
2. Review endpoints (10 min)
3. Check integration recommendations (5 min)
4. Review authentication & rate limiting (5 min)

### For DevOps (Deployment)
1. Review environment setup (**DNSE_IMPLEMENTATION_GUIDE.md** section 2)
2. Check production checklist (**DNSE_IMPLEMENTATION_GUIDE.md** section 10)
3. Configure monitoring & logging (section 9)

---

## 🔑 Key Information At A Glance

### Base URLs
```
REST: https://openapi.dnse.com.vn
WebSocket: wss://ws-openapi.dnse.com.vn (Prod)
           wss://ws-openapi-uat.dnse.com.vn (UAT)
```

### Main Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/price/secdef/{symbol}` | GET | Security definition |
| `/price/ohlc` | GET | Historical OHLCV data |
| `/account/accounts` | GET | List accounts |
| `/market/order` | POST | Place order |

### Python Library
```bash
pip install dnse-morphe
```

### Authentication
- Type: HMAC-SHA256 signature
- Headers: Date, Authorization, Content-Type

### Resolutions Available
- Minutes: `1m`, `5m`, `15m`, `30m`
- Hours: `1h`
- Days: `1d`
- Weeks: `1w`

---

## 📊 Supported Stocks

Vietnamese stock market coverage:
- **Exchange**: HOSE (Ho Chi Minh), HNX (Hanoi), UpCoM
- **Stocks**: 50+ major Vietnamese companies
- **Popular**: VNM, HPG, VND, VIC, VHM, FPT, TCB, VCB, MSN, MWG

---

## 🔄 Data Source Priority (Recommended)

```
DNSE → vnstock3 → yfinance → Simulation
```

1. **DNSE**: Official Vietnamese broker API (primary)
2. **vnstock3**: Vietnamese stock library (fallback)
3. **yfinance**: Yahoo Finance (fallback)
4. **Simulation**: Synthetic data with Geometric Brownian Motion (offline)

---

## 📈 Integration Progress

### Phase 1: Setup
- [ ] Install `dnse-morphe` library
- [ ] Set environment variables
- [ ] Test connection

### Phase 2: Basic Integration
- [ ] Add DNSE client to `stock_data.py`
- [ ] Implement OHLC data fetching
- [ ] Add security definition queries
- [ ] Test with existing tests

### Phase 3: Advanced Features
- [ ] WebSocket real-time streaming
- [ ] Order management integration
- [ ] Account information queries
- [ ] Advanced caching strategies

### Phase 4: Production
- [ ] Error handling & logging
- [ ] Monitoring setup
- [ ] Rate limiting
- [ ] Load testing
- [ ] Documentation

---

## 🛠️ Common Tasks

### Get Historical Data
```python
ohlc = client.market_data.get_ohlc(
    bar_type="stock",
    symbol="VND",
    resolution="1d",
    from_date="2024-01-01",
    to_date="2024-01-31",
)
```
→ See: DNSE_API_QUICK_REFERENCE.md

### Stream Real-Time Prices
```python
async with client.websocket() as ws:
    await ws.subscribe_quotes(["VND", "HPG"])
    ws.on("quote", callback)
```
→ See: DNSE_IMPLEMENTATION_GUIDE.md section 4

### Get Price Limits
```python
sec_def = client.market_data.get_security_definition("VND")
# Returns: ceiling_price, floor_price, ref_price, lot_size
```
→ See: DNSE_API_RESEARCH.md "Get Security Definition"

---

## 🚨 Important Notes

1. **Authentication Required**: API key and secret needed for most operations
2. **Rate Limiting**: Implement exponential backoff
3. **Fallback Strategy**: Always have fallback data sources
4. **Caching**: 5-minute TTL recommended
5. **Timezone**: Vietnamese Stock Market uses UTC+7 (Hanoi Time)

---

## 📞 Support & Resources

### Official
- **Website**: https://dnse.com.vn
- **API Portal**: https://developers.dnse.com.vn
- **Email**: hello@dnse.com.vn
- **Hotline**: +84 247 108 9234 (Mon-Fri, 8:30 AM - 5:30 PM)
- **Community**: Zalo group (1000+ members)

### Open Source
- **GitHub**: https://github.com/dinhhongkong/dnse-morphe
- **Python Library**: dnse-morphe
- **License**: MIT

---

## 📋 Document Cross-References

### Looking for...

**API Endpoints?**
→ DNSE_API_RESEARCH.md "API Endpoints" section

**How to authenticate?**
→ DNSE_API_RESEARCH.md "Authentication" section  
→ DNSE_IMPLEMENTATION_GUIDE.md section 2

**Python code examples?**
→ DNSE_API_QUICK_REFERENCE.md "Python Quick Start"  
→ DNSE_IMPLEMENTATION_GUIDE.md sections 3-5

**WebSocket configuration?**
→ DNSE_API_RESEARCH.md "WebSocket Streaming" section  
→ DNSE_IMPLEMENTATION_GUIDE.md section 4

**Error handling?**
→ DNSE_API_RESEARCH.md "Error Handling" section  
→ DNSE_IMPLEMENTATION_GUIDE.md section 7

**Response data formats?**
→ DNSE_API_RESEARCH.md "Data Types & Response Models"

**Data source priority?**
→ DNSE_API_RESEARCH.md "Recommendations for Integration"

**Troubleshooting?**
→ DNSE_IMPLEMENTATION_GUIDE.md "Troubleshooting" section

---

## 📦 Current Backend

**File**: `/Users/hoahn/securities/backend/services/stock_data.py`

**Current Features**:
- ✅ Stock list with prices
- ✅ Historical OHLCV data
- ✅ Stock information (name, exchange, sector)
- ✅ Market overview (indices)
- ✅ 5-minute caching
- ✅ Fallback data sources

**Enhancement Opportunities**:
- Add DNSE as primary source
- Real-time price streaming
- Price limits (ceiling/floor)
- Order management
- Account queries

---

## 🔐 Security

- **Credentials**: Use environment variables, never hardcode
- **Secrets**: API key and secret should be protected
- **Nonce**: Enabled by default for replay protection
- **Timeout**: Adjust based on network conditions
- **Rate Limiting**: Implement client-side throttling

---

## 📈 Performance Tips

1. **Caching**: Use 5-minute TTL for market data
2. **Pagination**: Use appropriate page sizes (default 100)
3. **Resolution**: Choose appropriate candlestick resolution
4. **WebSocket**: More efficient for real-time than polling
5. **Batch Requests**: Fetch multiple symbols efficiently

---

## 🎓 Learning Path

**Beginner**: 
- Start with DNSE_API_QUICK_REFERENCE.md
- Try Python code examples
- Run test script

**Intermediate**:
- Read DNSE_API_RESEARCH.md
- Implement basic integration
- Handle errors

**Advanced**:
- WebSocket streaming
- Order management
- Performance optimization
- Custom caching strategies

---

**Last Updated**: April 6, 2026  
**Research Status**: ✅ Complete  
**Documentation Status**: ✅ Complete  
**Implementation Status**: Ready for integration

