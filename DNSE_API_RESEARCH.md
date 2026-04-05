# DNSE (Chứng khoán DNSE) API Research Report

## Executive Summary

DNSE (formerly associated with ZaloPay Securities) operates a **LightSpeed API V2** platform for Vietnamese stock market access. The API is provided through **DNSE OpenAPI** (developers.dnse.com.vn) and supports:
- Real-time stock data
- Historical OHLCV data
- Account management
- Order placement and management
- WebSocket streaming

---

## Base URLs & Environments

### Production
- **REST API Base**: `https://openapi.dnse.com.vn`
- **WebSocket Base**: `wss://ws-openapi.dnse.com.vn`

### UAT (Testing)
- **WebSocket Base**: `wss://ws-openapi-uat.dnse.com.vn`

---

## API Endpoints

### Market Data Endpoints

#### 1. Get Security Definition
**Endpoint**: `GET /price/secdef/{symbol}`

**Parameters**:
- `symbol` (path): Stock symbol (e.g., "VND", "HPG", "VNM")
- `boardId` (query, optional): Board ID (e.g., "HOSE", "HNX")

**Response**: SecurityDefinition object
```json
{
  "symbol": "VND",
  "ceiling_price": 52.00,
  "floor_price": 48.00,
  "ref_price": 50.00,
  "lot_size": 100,
  "board_id": "HOSE"
}
```

#### 2. Get OHLC Data (Candles)
**Endpoint**: `GET /price/ohlc`

**Parameters**:
- `type` (query): Bar type (e.g., "stock")
- `symbol` (query, optional): Stock symbol
- `boardId` (query, optional): Board ID
- `from` (query, optional): Start date (format: YYYY-MM-DD)
- `to` (query, optional): End date (format: YYYY-MM-DD)
- `resolution` (query, optional): Timeframe - `1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1w`
- `pageSize` (query, optional): Items per page (default: 100)
- `pageIndex` (query, optional): Page number

**Response**: Array of OHLC objects
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

**Python Example**:
```python
ohlc_list = client.market_data.get_ohlc(
    bar_type="stock",
    symbol="VND",
    resolution="1m",
    from_date="2024-01-01",
    to_date="2024-01-02",
)
```

---

### Account Endpoints

#### 1. List Accounts
**Endpoint**: `GET /account/accounts` (implied)

**Response**: Array of Account objects
```python
accounts = client.accounts.list()
# Returns: [Account(account_no="...", account_name="...", status="..."), ...]
```

#### 2. Get Account Balances
**Endpoint**: `GET /account/balances/{account_no}` (implied)

**Parameters**:
- `account_no`: Account number/ID

**Response**: Array of Balance objects
```python
balances = client.accounts.list_balances(account_no="ACCOUNT123")
# Returns: [Balance(cash_balance=..., buying_power=...), ...]
```

#### 3. List Deals
**Endpoint**: `GET /account/deals` (implied)

**Parameters**:
- `account_no`: Account number
- `market_type`: "stock" or other market type

**Response**: Array of Deal objects

#### 4. List Loan Packages
**Endpoint**: `GET /account/loan-packages` (implied)

**Parameters**:
- `account_no`: Account number
- `market_type`: "stock"
- `symbol`: Stock symbol

**Response**: Array of LoanPackage objects

#### 5. Calculate PPSE (Buying Power)
**Endpoint**: `POST /account/ppse` (implied)

**Parameters**:
- `account_no`: Account number
- `market_type`: "stock"
- `symbol`: Stock symbol
- `price`: Stock price
- `loan_package_id`: Loan package ID

---

### Order Endpoints

#### 1. Create Trading Token
**Endpoint**: `POST /trading/token` (implied)

**Parameters**:
- `otp_type`: "EMAIL" or other OTP type
- `passcode`: OTP code from email

**Response**: Trading token string

#### 2. Place Order
**Endpoint**: `POST /market/order` (implied)

**Request Body**:
```json
{
  "account_no": "ACCOUNT123",
  "symbol": "VND",
  "side": "BUY",
  "order_type": "LO",
  "price": 50.0,
  "quantity": 100
}
```

**Parameters**:
- `market_type`: "stock"
- `trading_token`: Token from trading token endpoint

**Response**:
```json
{
  "order_id": "ORDER123",
  "status": "PENDING",
  "account_no": "ACCOUNT123",
  "symbol": "VND"
}
```

#### 3. List Active Orders
**Endpoint**: `GET /market/orders` (implied)

**Parameters**:
- `account_no`: Account number
- `market_type`: "stock"

**Response**: Array of Order objects

#### 4. Get Order Details
**Endpoint**: `GET /market/order/{order_id}` (implied)

**Parameters**:
- `account_no`: Account number
- `order_id`: Order ID
- `market_type`: "stock"

#### 5. Cancel Order
**Endpoint**: `DELETE /market/order/{order_id}` (implied)

**Parameters**:
- `account_no`: Account number
- `order_id`: Order ID
- `market_type`: "stock"
- `trading_token`: Required for order modification

#### 6. List Order History
**Endpoint**: `GET /market/order-history` (implied)

**Parameters**:
- `account_no`: Account number
- `market_type`: "stock"
- `from_date`: Start date
- `to_date`: End date

**Response**: Array of OrderHistoryItem objects

#### 7. Close Deal
**Endpoint**: `POST /market/close-deal` (implied)

**Parameters**:
- `deal_id`: Deal ID to close
- `account_no`: Account number
- `market_type`: "stock"
- `payload`: `{"close_quantity": number}`
- `trading_token`: Required

---

## WebSocket Streaming

### Connection
```
wss://ws-openapi.dnse.com.vn  (Production)
wss://ws-openapi-uat.dnse.com.vn  (UAT)
```

### Supported Channels (Subscriptions)

#### Market Data Channels
1. **Trades**: `subscribe_trades(["VND", "HPG"])`
   - Real-time trade executions
   
2. **Quotes**: `subscribe_quotes(["VND", "HPG"])`
   - Real-time bid-ask prices
   - Response includes `best_bid`, `best_ask` as (price, quantity) tuples
   
3. **OHLC/Candles**: `subscribe_ohlc(["VND"], resolution="1m")`
   - Real-time candle updates
   - Resolutions: `1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1w`
   
4. **Expected Price**: `subscribe_expected_price(["VND"])`
   - Expected opening price
   
5. **Security Definition**: `subscribe_sec_def(["VND", "HPG"])`
   - Real-time security info updates

#### Private Channels (Authenticated)
1. **Orders**: `subscribe_orders()`
   - Order status updates
   
2. **Positions**: `subscribe_positions()`
   - Position updates
   
3. **Account**: `subscribe_account()`
   - Account balance updates

### Python WebSocket Example
```python
import asyncio
from dnse_morphe import AsyncDNSEClient

async def main():
    client = AsyncDNSEClient(
        api_key="your_api_key",
        api_secret="your_api_secret",
    )

    async with client.websocket(encoding="json") as ws:
        # Subscribe to trades and quotes
        await ws.subscribe_trades(["VND", "HPG"])
        await ws.subscribe_quotes(["VND", "HPG"])

        # Register event handlers
        def on_trade(trade):
            print(f"Trade: {trade.symbol} @ {trade.price}, Qty: {trade.quantity}")

        def on_quote(quote):
            print(f"Quote: {quote.symbol} | Bid: {quote.best_bid} | Ask: {quote.best_ask}")

        ws.on("trade", on_trade)
        ws.on("quote", on_quote)

        # Keep connection alive
        await asyncio.sleep(3600)

asyncio.run(main())
```

---

## Authentication

### HMAC Signature Authentication
The API uses HMAC-SHA256 signature authentication with date headers.

**Signature Algorithm**:
```
Signature = base64(HMAC-SHA256(
    secret,
    "(request-target): METHOD /path\ndate: DATE_VALUE\nnonce: NONCE"
))
```

**Request Headers Required**:
- `Date`: RFC 2822 formatted date
- `Authorization`: Signature header with algorithm and credentials
- `X-API-Key` (optional): API key may be passed as header
- `Content-Type`: "application/json"

**Optional**:
- `nonce`: UUID for replay protection (enabled by default)

### Python Client Initialization
```python
from dnse_morphe import DNSEClient

client = DNSEClient(
    api_key="your_api_key",
    api_secret="your_api_secret",
    base_url="https://openapi.dnse.com.vn",
    hmac_nonce_enabled=True,  # Enable nonce for security
    timeout=30.0
)
```

---

## Data Types & Response Models

### SecurityDefinition
```python
{
    "symbol": str,           # Stock symbol (e.g., "VND")
    "ceiling_price": float,  # Daily ceiling price
    "floor_price": float,    # Daily floor price
    "ref_price": float,      # Reference price
    "lot_size": int,         # Minimum order size
    "board_id": str          # Board ID (HOSE, HNX, etc.)
}
```

### OHLC
```python
{
    "time": str,      # ISO format datetime
    "open": float,    # Opening price
    "high": float,    # Highest price in period
    "low": float,     # Lowest price in period
    "close": float,   # Closing price
    "volume": int     # Volume in shares
}
```

### Trade
```python
{
    "symbol": str,
    "price": float,
    "quantity": int,
    "timestamp": str,
    "side": str       # "BUY" or "SELL"
}
```

### Quote
```python
{
    "symbol": str,
    "best_bid": tuple,    # (price: float, quantity: int)
    "best_ask": tuple,    # (price: float, quantity: int)
    "timestamp": str,
    "spread": float       # Bid-ask spread
}
```

### Account
```python
{
    "account_no": str,
    "account_name": str,
    "status": str,        # "ACTIVE", etc.
    "account_type": str
}
```

### Balance
```python
{
    "cash_balance": float,
    "buying_power": float,
    "market_value": float,
    "total_value": float
}
```

### Order
```python
{
    "order_id": str,
    "account_no": str,
    "symbol": str,
    "side": str,          # "BUY" or "SELL"
    "quantity": int,
    "price": float,
    "status": str,        # "PENDING", "FILLED", "CANCELLED", etc.
    "filled_quantity": int,
    "order_type": str,    # "LO" (Limit), "MO" (Market), etc.
    "timestamp": str
}
```

---

## Request/Response Format Examples

### Example 1: Fetch OHLC Data
**Request**:
```
GET /price/ohlc?type=stock&symbol=VND&from=2024-01-01&to=2024-01-02&resolution=1d
Host: openapi.dnse.com.vn
Date: Mon, 01 Jan 2024 09:30:00 +0000
Authorization: Signature algorithm="hmac-sha256", headers="(request-target) date nonce", signature="..."
Content-Type: application/json
```

**Response** (200 OK):
```json
[
  {
    "time": "2024-01-01",
    "open": 50.0,
    "high": 50.5,
    "low": 49.8,
    "close": 50.2,
    "volume": 2500000
  }
]
```

### Example 2: Get Security Definition
**Request**:
```
GET /price/secdef/VND
Host: openapi.dnse.com.vn
Date: Mon, 01 Jan 2024 09:30:00 +0000
Authorization: Signature algorithm="hmac-sha256", headers="(request-target) date nonce", signature="..."
Content-Type: application/json
```

**Response** (200 OK):
```json
{
  "symbol": "VND",
  "ceiling_price": 52.0,
  "floor_price": 48.0,
  "ref_price": 50.0,
  "lot_size": 100,
  "board_id": "HOSE"
}
```

---

## Error Handling

### Exception Types
- `AuthenticationError`: Invalid API credentials
- `RateLimitError`: Rate limit exceeded
- `APIError`: General API error with status and body
- `WebSocketError`: WebSocket connection errors
- `ConnectionError`: Network connection issues
- `SubscriptionError`: WebSocket subscription issues

### Python Error Handling Example
```python
from dnse_morphe import DNSEClient
from dnse_morphe._exception import AuthenticationError, RateLimitError, APIError

try:
    accounts = client.accounts.list()
except AuthenticationError:
    print("Invalid API credentials")
except RateLimitError:
    print("Rate limit exceeded, try again later")
except APIError as e:
    print(f"API Error: {e.status} - {e.body}")
```

---

## Rate Limiting & Performance

- **Default HTTP Timeout**: 60 seconds
- **WebSocket Max Retries**: 10 attempts
- **WebSocket Heartbeat**: 25 seconds (keep-alive)
- **Default Page Size**: 100 items
- **Authentication**: HMAC-SHA256 with optional nonce

---

## Vietnamese Stock Exchanges

DNSE provides access to:
- **HOSE** (Sở Giao dịch Chứng khoán Thành phố Hồ Chí Minh) - Ho Chi Minh Stock Exchange
- **HNX** (Sở Giao dịch Chứng khoán Hà Nội) - Hanoi Stock Exchange
- **UpCoM** (Sàn Giao dịch Công ty cổ phần chưa niêm yết) - Unlisted Public Company Market

Popular Stocks Available:
- `VNM` (Vinamilk)
- `HPG` (Hòa Phát Group)
- `VND` (VND Direct)
- `VIC` (Vingroup)
- `VHM` (Vinhomes)
- `FPT` (FPT Corporation)
- `TCB` (Techcombank)
- `VCB` (Vietcombank)
- And 40+ other major Vietnamese stocks

---

## Official Resources

- **Official Website**: https://dnse.com.vn
- **Developers Portal**: https://developers.dnse.com.vn
- **API Documentation**: https://developers.dnse.com.vn/docs
- **Contact**: 
  - Hotline: +84 247 108 9234 (Mon-Fri, 8:30 AM - 5:30 PM)
  - Email: hello@dnse.com.vn
- **Community**: Zalo group with 1000+ members

---

## Python Library: dnse-morphe

An excellent unofficial but well-maintained library for DNSE API integration:

**GitHub**: https://github.com/dinhhongkong/dnse-morphe

**Features**:
- Fully async and sync support
- Pydantic type-safe models
- WebSocket real-time streaming
- Order management
- Market data access
- Comprehensive error handling

**Installation**:
```bash
pip install dnse-morphe
```

---

## Current Backend Implementation

The current backend at `/Users/hoahn/securities/backend/services/stock_data.py`:
- Uses **vnstock3** as primary data source (Vietnamese stock library)
- Falls back to **yfinance** if vnstock3 fails
- Uses **simulated data** (Geometric Brownian Motion) for offline resilience
- Has a **5-minute TTL cache** with 256 max entries
- Provides endpoints for:
  - Stock list
  - Historical OHLCV data
  - Stock information (name, exchange, sector, market cap)
  - Market overview (VN-Index, HNX-Index)

---

## Recommendations for Integration

### To replace/augment current implementation:

1. **Add DNSE client** to `stock_data.py` alongside vnstock3:
   ```python
   from dnse_morphe import DNSEClient
   
   client = DNSEClient(
       api_key=os.getenv("DNSE_API_KEY"),
       api_secret=os.getenv("DNSE_API_SECRET"),
   )
   ```

2. **Fetch real-time data** from DNSE before falling back to vnstock3:
   ```python
   try:
       ohlc = client.market_data.get_ohlc(
           bar_type="stock",
           symbol=symbol,
           resolution="1d",
           from_date=start_date,
           to_date=end_date,
       )
   except Exception:
       # Fall back to vnstock3 or simulation
   ```

3. **Use WebSocket** for real-time price streaming:
   ```python
   async with client.websocket() as ws:
       await ws.subscribe_quotes(symbols)
       ws.on("quote", handle_price_update)
   ```

4. **Implement market overview** using DNSE data:
   ```python
   # Fetch VNINDEX and HNX data from DNSE
   vnindex = client.market_data.get_security_definition("VNINDEX")
   hnxindex = client.market_data.get_security_definition("HNXINDEX")
   ```

---

**End of Report**
