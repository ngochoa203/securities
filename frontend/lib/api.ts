const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Types ──────────────────────────────────────────────────────────────────

export interface StockSummary {
  symbol: string;
  name: string;
  exchange: string;
  sector: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
}

export interface HistoryPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockDetail extends StockSummary {
  market_cap: number;
  history: HistoryPoint[];
}

export interface Predictions {
  '1': number;
  '7': number;
  '30': number;
}

export interface ModelDetails {
  lstm?: number;
  xgboost?: number;
  prophet?: number;
  [key: string]: number | undefined;
}

export interface PredictionResult {
  symbol: string;
  current_price: number;
  predictions: Predictions;
  direction: 'up' | 'down';
  confidence: number;
  model_details: ModelDetails;
}

export interface MacdIndicator {
  line: number;
  signal: number;
  histogram: number;
}

export interface BollingerIndicator {
  upper: number;
  middle: number;
  lower: number;
}

export interface SmaIndicator {
  sma_20: number;
  sma_50: number;
  sma_200: number;
}

export interface EmaIndicator {
  ema_12?: number;
  ema_26?: number;
  ema_50?: number;
  [key: string]: number | undefined;
}

export interface TechnicalIndicators {
  rsi: number;
  macd: MacdIndicator;
  bollinger: BollingerIndicator;
  sma: SmaIndicator;
  ema: EmaIndicator;
}

export interface TechnicalResult {
  symbol: string;
  indicators: TechnicalIndicators;
  signal: 'Buy' | 'Sell' | 'Hold';
  signal_confidence: number;
}

export interface RankingStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  signal: string;
  reason: string;
}

export interface GuideSection {
  title: string;
  content: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      next: { revalidate: 30 },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// ── API Functions ──────────────────────────────────────────────────────────

export async function fetchStocks(): Promise<StockSummary[] | null> {
  const data = await get<{ stocks: StockSummary[] }>('/api/stocks');
  return data?.stocks ?? null;
}

export async function fetchStock(symbol: string): Promise<StockDetail | null> {
  return get<StockDetail>(`/api/stocks/${encodeURIComponent(symbol)}`);
}

export async function fetchPrediction(symbol: string): Promise<PredictionResult | null> {
  return get<PredictionResult>(`/api/stocks/${encodeURIComponent(symbol)}/predict`);
}

export async function fetchTechnical(symbol: string): Promise<TechnicalResult | null> {
  return get<TechnicalResult>(`/api/stocks/${encodeURIComponent(symbol)}/technical`);
}

export async function fetchRankings(
  type: 'top-buy' | 'top-decline' | 'trustworthy' | 'top-invest'
): Promise<RankingStock[] | null> {
  const data = await get<{ stocks: RankingStock[] }>(`/api/rankings/${type}`);
  return data?.stocks ?? null;
}

export async function fetchGuide(): Promise<GuideSection[] | null> {
  const data = await get<{ sections: GuideSection[] }>('/api/guide');
  return data?.sections ?? null;
}

// ── Watchlist Types ────────────────────────────────────────────────────────

export interface WatchlistItem {
  symbol: string;
  target_low: number;
  target_high: number;
  current_price?: number;
  name?: string;
  change_pct?: number;
}

export interface AlertItem {
  type: string;
  symbol: string;
  message: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface PollerStatus {
  running: boolean;
  market_hours: boolean;
  last_poll_time: string | null;
  watchlist_count: number;
  discord_configured: boolean;
}

// ── Watchlist API ──────────────────────────────────────────────────────────

export async function fetchWatchlist(): Promise<WatchlistItem[] | null> {
  const data = await get<{ watchlist: WatchlistItem[] }>('/api/watchlist');
  return data?.watchlist ?? null;
}

export async function addToWatchlist(
  symbol: string,
  targetLow: number = 0,
  targetHigh: number = 0,
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/watchlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: symbol.toUpperCase(),
        target_low: targetLow,
        target_high: targetHigh,
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function removeFromWatchlist(symbol: string): Promise<boolean> {
  try {
    const res = await fetch(
      `${API_BASE}/api/watchlist/${encodeURIComponent(symbol)}`,
      { method: 'DELETE' },
    );
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchAlertHistory(
  limit: number = 50,
): Promise<AlertItem[] | null> {
  const data = await get<{ alerts: AlertItem[] }>(
    `/api/alerts/history?limit=${limit}`,
  );
  return data?.alerts ?? null;
}

export async function testDiscordAlert(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/alerts/test`, { method: 'POST' });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchPollerStatus(): Promise<PollerStatus | null> {
  return get<PollerStatus>('/api/poller/status');
}
