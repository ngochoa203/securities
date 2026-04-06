'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Bell,
  Plus,
  Trash2,
  RefreshCw,
  Send,
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import {
  fetchWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  fetchAlertHistory,
  testDiscordAlert,
  fetchPollerStatus,
  type WatchlistItem,
  type AlertItem,
  type PollerStatus,
} from '@/lib/api';

// ── Helpers ────────────────────────────────────────────────────────────────

function fmtPrice(n?: number) {
  if (n == null) return '—';
  return n.toLocaleString('vi-VN');
}

function fmtRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s} giây trước`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} phút trước`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} giờ trước`;
  return `${Math.floor(h / 24)} ngày trước`;
}

function alertIcon(type: string): string {
  switch (type) {
    case 'price_alert': return '🚨';
    case 'signal_change': return '📊';
    case 'good_price': return '💰';
    case 'buy_recommendation': return '📈';
    case 'session_summary': return '🔔';
    case 'test': return '🧪';
    default: return '🔔';
  }
}

// ── Poller Status Bar ──────────────────────────────────────────────────────

function PollerStatusBar({ status }: { status: PollerStatus | null }) {
  if (!status) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-xl px-5 py-3 flex items-center gap-2 text-sm text-gray-400">
        <Activity className="w-4 h-4 animate-pulse" />
        <span>Đang tải trạng thái hệ thống...</span>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl px-5 py-3">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
        {/* Poller running state */}
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              status.running ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]' : 'bg-gray-500'
            }`}
          />
          <span className={status.running ? 'text-emerald-400' : 'text-gray-400'}>
            Poller: {status.running ? 'Đang chạy ✅' : 'Dừng ⏸️'}
          </span>
        </span>

        {/* Market hours */}
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              status.market_hours ? 'bg-emerald-500' : 'bg-red-500'
            }`}
          />
          <span className={status.market_hours ? 'text-emerald-400' : 'text-red-400'}>
            {status.market_hours
              ? 'Trong giờ giao dịch 🟢'
              : 'Ngoài giờ giao dịch 🔴'}
          </span>
        </span>

        {/* Discord */}
        <span className="flex items-center gap-1.5">
          {status.discord_configured ? (
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />
          )}
          <span className={status.discord_configured ? 'text-emerald-400' : 'text-yellow-400'}>
            Discord:{' '}
            {status.discord_configured ? 'Đã kết nối ✅' : 'Chưa cấu hình ⚠️'}
          </span>
        </span>

        {/* Watchlist count */}
        <span className="text-gray-400 ml-auto">
          <span className="text-white font-semibold">{status.watchlist_count}</span>{' '}
          cổ phiếu đang theo dõi
        </span>
      </div>
    </div>
  );
}

// ── Add Stock Form ─────────────────────────────────────────────────────────

interface AddFormProps {
  onAdded: () => void;
}

function AddStockForm({ onAdded }: AddFormProps) {
  const [symbol, setSymbol] = useState('');
  const [low, setLow] = useState('');
  const [high, setHigh] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const sym = symbol.trim().toUpperCase();
    if (!sym) {
      setError('Vui lòng nhập mã cổ phiếu.');
      return;
    }
    setError('');
    setLoading(true);
    const ok = await addToWatchlist(
      sym,
      low ? parseFloat(low) : 0,
      high ? parseFloat(high) : 0,
    );
    setLoading(false);
    if (ok) {
      setSymbol('');
      setLow('');
      setHigh('');
      onAdded();
    } else {
      setError('Không thể thêm cổ phiếu. Vui lòng thử lại.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
      <input
        type="text"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
        placeholder="Mã CP (VD: FPT)"
        maxLength={10}
        className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 text-sm uppercase transition-colors"
      />
      <input
        type="number"
        value={low}
        onChange={(e) => setLow(e.target.value)}
        placeholder="Giá mua (đ)"
        min={0}
        className="w-full sm:w-36 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 text-sm transition-colors"
      />
      <input
        type="number"
        value={high}
        onChange={(e) => setHigh(e.target.value)}
        placeholder="Giá bán (đ)"
        min={0}
        className="w-full sm:w-36 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 text-sm transition-colors"
      />
      <button
        type="submit"
        disabled={loading}
        className="flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg px-4 py-2 text-sm transition-colors"
      >
        {loading ? (
          <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : (
          <Plus className="w-4 h-4" />
        )}
        Thêm
      </button>
      {error && (
        <p className="w-full text-red-400 text-xs mt-1 col-span-full">{error}</p>
      )}
    </form>
  );
}

// ── Watchlist Table ────────────────────────────────────────────────────────

interface WatchlistTableProps {
  items: WatchlistItem[];
  loading: boolean;
  onRefresh: () => void;
  onRemove: (symbol: string) => void;
  removing: string | null;
}

function WatchlistTable({
  items,
  loading,
  onRefresh,
  onRemove,
  removing,
}: WatchlistTableProps) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
      {/* Section header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-700">
        <h2 className="font-semibold text-white flex items-center gap-2">
          <Bell className="w-4 h-4 text-emerald-400" />
          Cổ phiếu theo dõi
          {items.length > 0 && (
            <span className="ml-1 text-xs bg-emerald-500/15 text-emerald-400 rounded-full px-2 py-0.5">
              {items.length}
            </span>
          )}
        </h2>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white disabled:opacity-50 transition-colors"
          title="Làm mới"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Làm mới
        </button>
      </div>

      {loading ? (
        <div className="py-14 text-center">
          <div className="inline-block w-7 h-7 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-gray-400 text-sm">Đang tải...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="py-14 text-center">
          <Bell className="w-10 h-10 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 text-sm">Chưa có cổ phiếu nào trong danh sách</p>
          <p className="text-gray-600 text-xs mt-1">Thêm mã cổ phiếu ở trên để bắt đầu theo dõi</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-900/50 border-b border-gray-700 text-gray-400 text-xs uppercase tracking-wider">
                <th className="text-left py-3 px-4 font-semibold">Mã CP</th>
                <th className="text-left py-3 px-4 font-semibold hidden sm:table-cell">Tên</th>
                <th className="text-right py-3 px-4 font-semibold">Giá hiện tại</th>
                <th className="text-right py-3 px-4 font-semibold">Thay đổi %</th>
                <th className="text-center py-3 px-4 font-semibold hidden md:table-cell">
                  Giá mục tiêu
                </th>
                <th className="text-center py-3 px-4 font-semibold">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const isUp = (item.change_pct ?? 0) >= 0;
                const price = item.current_price ?? 0;
                const inRange =
                  item.target_low > 0 &&
                  item.target_high > 0 &&
                  price >= item.target_low &&
                  price <= item.target_high;

                return (
                  <tr
                    key={item.symbol}
                    className={`border-b border-gray-700 transition-colors ${
                      inRange
                        ? 'bg-emerald-900/20 hover:bg-emerald-900/30'
                        : 'hover:bg-gray-700/40'
                    }`}
                  >
                    {/* Symbol */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        {inRange && (
                          <span
                            className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_4px_#34d399] flex-shrink-0"
                            title="Trong vùng giá mục tiêu"
                          />
                        )}
                        <span className="font-bold text-white">{item.symbol}</span>
                      </div>
                    </td>

                    {/* Name */}
                    <td className="py-3.5 px-4 hidden sm:table-cell text-gray-400 max-w-[180px] truncate">
                      {item.name || '—'}
                    </td>

                    {/* Current price */}
                    <td className="py-3.5 px-4 text-right font-semibold text-white">
                      {fmtPrice(item.current_price)}
                    </td>

                    {/* Change % */}
                    <td className="py-3.5 px-4 text-right">
                      {item.change_pct != null ? (
                        <span
                          className={`inline-flex items-center justify-end gap-1 font-semibold ${
                            isUp ? 'text-emerald-400' : 'text-red-400'
                          }`}
                        >
                          {isUp ? (
                            <TrendingUp className="w-3.5 h-3.5" />
                          ) : (
                            <TrendingDown className="w-3.5 h-3.5" />
                          )}
                          {isUp ? '+' : ''}
                          {item.change_pct.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>

                    {/* Target range */}
                    <td className="py-3.5 px-4 hidden md:table-cell text-center">
                      {item.target_low > 0 || item.target_high > 0 ? (
                        <span
                          className={`text-xs px-2 py-1 rounded-lg ${
                            inRange
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-gray-700 text-gray-300'
                          }`}
                        >
                          {fmtPrice(item.target_low)} – {fmtPrice(item.target_high)}
                        </span>
                      ) : (
                        <span className="text-gray-600 text-xs">Chưa đặt</span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="py-3.5 px-4 text-center">
                      <button
                        onClick={() => onRemove(item.symbol)}
                        disabled={removing === item.symbol}
                        className="inline-flex items-center justify-center p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                        title={`Xóa ${item.symbol}`}
                      >
                        {removing === item.symbol ? (
                          <span className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Alert History Panel ────────────────────────────────────────────────────

interface AlertPanelProps {
  alerts: AlertItem[];
  loading: boolean;
  onTestAlert: () => void;
  testingAlert: boolean;
  testResult: string | null;
}

function AlertPanel({
  alerts,
  loading,
  onTestAlert,
  testingAlert,
  testResult,
}: AlertPanelProps) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-700">
        <h2 className="font-semibold text-white flex items-center gap-2">
          <span className="text-base">📢</span>
          Lịch sử cảnh báo
          {alerts.length > 0 && (
            <span className="ml-1 text-xs bg-blue-500/15 text-blue-400 rounded-full px-2 py-0.5">
              {alerts.length}
            </span>
          )}
        </h2>
        <button
          onClick={onTestAlert}
          disabled={testingAlert}
          className="flex items-center gap-1.5 text-xs bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg px-3 py-1.5 transition-colors font-medium"
          title="Gửi thông báo test đến Discord"
        >
          {testingAlert ? (
            <span className="w-3.5 h-3.5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
          Gửi thông báo test
        </button>
      </div>

      {/* Test result toast */}
      {testResult && (
        <div
          className={`mx-5 mt-3 px-3 py-2 rounded-lg text-sm flex items-center gap-2 ${
            testResult.startsWith('✅')
              ? 'bg-emerald-500/15 text-emerald-300'
              : 'bg-red-500/15 text-red-300'
          }`}
        >
          {testResult}
        </div>
      )}

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto max-h-[520px]">
        {loading ? (
          <div className="py-14 text-center">
            <div className="inline-block w-7 h-7 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-gray-400 text-sm">Đang tải cảnh báo...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="py-14 text-center">
            <Bell className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">Chưa có cảnh báo nào</p>
            <p className="text-gray-600 text-xs mt-1">
              Cảnh báo sẽ xuất hiện khi có biến động giá hoặc tín hiệu
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-700/70">
            {alerts.map((alert, idx) => (
              <li
                key={`${alert.timestamp}-${idx}`}
                className="px-5 py-3.5 hover:bg-gray-700/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg leading-none mt-0.5 flex-shrink-0">
                    {alertIcon(alert.type)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="font-semibold text-white text-sm">
                        {alert.symbol}
                      </span>
                      <span className="text-xs text-gray-500 flex-shrink-0">
                        {fmtRelativeTime(alert.timestamp)}
                      </span>
                    </div>
                    <p className="text-gray-300 text-xs mt-0.5 leading-relaxed">
                      {alert.message}
                    </p>
                    <span className="inline-block mt-1 text-xs text-gray-600 bg-gray-700/50 rounded px-1.5 py-0.5">
                      {alert.type}
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function WatchlistPage() {
  const [pollerStatus, setPollerStatus] = useState<PollerStatus | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loadingWatchlist, setLoadingWatchlist] = useState(true);
  const [loadingAlerts, setLoadingAlerts] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);
  const [testingAlert, setTestingAlert] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const loadWatchlist = useCallback(async () => {
    setLoadingWatchlist(true);
    const data = await fetchWatchlist();
    if (data) setWatchlist(data);
    setLoadingWatchlist(false);
  }, []);

  const loadAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    const data = await fetchAlertHistory(50);
    if (data) setAlerts(data);
    setLoadingAlerts(false);
  }, []);

  const loadPollerStatus = useCallback(async () => {
    const data = await fetchPollerStatus();
    if (data) setPollerStatus(data);
  }, []);

  // Initial load
  useEffect(() => {
    loadWatchlist();
    loadAlerts();
    loadPollerStatus();
  }, [loadWatchlist, loadAlerts, loadPollerStatus]);

  // Auto-refresh alerts every 30s
  useEffect(() => {
    const id = setInterval(() => {
      loadAlerts();
      loadPollerStatus();
    }, 30_000);
    return () => clearInterval(id);
  }, [loadAlerts, loadPollerStatus]);

  const handleRemove = async (symbol: string) => {
    setRemoving(symbol);
    const ok = await removeFromWatchlist(symbol);
    setRemoving(null);
    if (ok) {
      setWatchlist((prev) => prev.filter((i) => i.symbol !== symbol));
    }
  };

  const handleTestAlert = async () => {
    setTestingAlert(true);
    setTestResult(null);
    const ok = await testDiscordAlert();
    setTestingAlert(false);
    setTestResult(
      ok
        ? '✅ Đã gửi thông báo test thành công!'
        : '❌ Gửi thất bại. Kiểm tra cấu hình Discord.',
    );
    setTimeout(() => setTestResult(null), 5000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          📋 Danh sách theo dõi
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Theo dõi cổ phiếu và nhận cảnh báo Discord khi đạt vùng giá mục tiêu
        </p>
      </div>

      {/* Poller status bar */}
      <PollerStatusBar status={pollerStatus} />

      {/* Add stock form */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl px-5 py-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <Plus className="w-4 h-4 text-emerald-400" />
          Thêm cổ phiếu mới
        </h3>
        <AddStockForm onAdded={loadWatchlist} />
      </div>

      {/* Main two-column content */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: watchlist table (3/5) */}
        <div className="lg:col-span-3">
          <WatchlistTable
            items={watchlist}
            loading={loadingWatchlist}
            onRefresh={loadWatchlist}
            onRemove={handleRemove}
            removing={removing}
          />
        </div>

        {/* Right: alert history (2/5) */}
        <div className="lg:col-span-2">
          <AlertPanel
            alerts={alerts}
            loading={loadingAlerts}
            onTestAlert={handleTestAlert}
            testingAlert={testingAlert}
            testResult={testResult}
          />
        </div>
      </div>
    </div>
  );
}
