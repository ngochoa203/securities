# Securities - Vietnam Stock Prediction Web App

AI-powered Vietnamese stock market prediction platform with real-time tracking, technical analysis, and investment recommendations.

## Features
- Real-time VN stock tracking (HOSE/HNX/UPCOM)
- AI Prediction Engine (LSTM + XGBoost + Prophet Ensemble)
- Technical Analysis (RSI, MACD, Bollinger Bands, SMA/EMA)
- Stock Rankings (Top Buy, Top Decline, Trustworthy, Investment Picks)
- Beginner Trading Guide (Vietnamese)
- Responsive Dashboard with Dark/Light Mode

## Tech Stack
- **Frontend**: Next.js 14 + TypeScript + TailwindCSS + Recharts
- **Backend**: Python FastAPI + VNStock + yfinance
- **ML Models**: LSTM + XGBoost + Prophet (Ensemble)

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## API Endpoints
- `GET /api/stocks` - List all VN stocks
- `GET /api/stocks/{symbol}` - Stock detail + history
- `GET /api/stocks/{symbol}/predict` - AI prediction
- `GET /api/stocks/{symbol}/technical` - Technical indicators
- `GET /api/rankings/top-buy` - Top recommended stocks
- `GET /api/rankings/top-decline` - Biggest decliners
- `GET /api/rankings/trustworthy` - Most trustworthy
- `GET /api/rankings/top-invest` - Best investment picks

## Disclaimer
This app is for educational purposes only. Stock predictions are not financial advice. Always do your own research before investing.
