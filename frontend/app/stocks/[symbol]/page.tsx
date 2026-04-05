'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Activity,
} from 'lucide-react';
import {
  fetchStock,
  fetchPrediction,
  fetchTechnical,
  StockDetail,
  PredictionResult,
  TechnicalResult,
} from '@/lib/api';
import StockChart from '@/components/StockChart';
import PredictionCard from '@/components/PredictionCard';
import TechnicalIndicators from '@/components/TechnicalIndicators';

function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <div className="w-10 h-10 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-gray-400">Đang tải dữ liệu...</p>
    </div>
  );
}

function ErrorState({ symbol }: { symbol: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <p className="text-red-400 font-semibold mb-2">
        Không tìm thấy cổ phiếu "{symbol}"
      </p>
      <p className="text-gray-500 text-sm mb-4">
        Máy chủ không phản hồi hoặc mã cổ phiếu không tồn tại.
      </p>
      <Link
        href="/stocks"
        className="text-emerald-400 hover:text-emerald-300 flex items-center gap-2"
      >
        <ArrowLeft className="w-4 h-4" /> Quay lại danh sách
      </Link>
    </div>
  );
}

export default function StockDetailPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = decodeURIComponent(params.symbol).toUpperCase();

  const [stock, setStock] = useState<StockDetail | null>(null);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [technical, setTechnical] = useState<TechnicalResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'chart' | 'technical' | 'prediction'>('chart');

  const load = () => {
    setLoading(true);
    Promise.all([
      fetchStock(symbol),
      fetchPrediction(symbol),
      fetchTechnical(symbol),
    ]).then(([s, p, t]) => {
      setStock(s);
      setPrediction(p);
      setTechnical(t);
      setLoading(false);
    });
  };

  useEffect(() => { load(); }, [symbol]);

  if (loading) return (
    <div className="max-w-7xl mx-auto px-4 py-8"><LoadingSpinner /></div>
  );
  if (!stock) return (
    <div className="max-w-7xl mx-auto px-4 py-8"><ErrorState symbol={symbol} /></div>
  );

  const isUp = stock.change >= 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6">
        <Link href="/stocks" className="text-gray-400 hover:text-white flex items-center gap-1 text-sm">
          <ArrowLeft className="w-4 h-4" /> Cổ phiếu
        </Link>
        <span className="text-gray-600">/</span>
        <span className="text-white font-semibold">{symbol}</span>
      </div>

      {/* Header */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-extrabold text-white">{stock.symbol}</h1>
              <span className="text-xs px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 font-medium">
                {stock.exchange}
              </span>
              <span className="text-xs px-2 py-1 rounded-full bg-gray-700 text-gray-400">
                {stock.sector}
              </span>
            </div>
            <p className="text-gray-300 text-lg">{stock.name}</p>
          </div>
          <div className="flex items-end gap-4">
            <div className="text-right">
              <p className="text-3xl font-extrabold text-white">
                {stock.price.toLocaleString('vi-VN')}
                <span className="text-lg text-gray-400 ml-1">đ</span>
              </p>
              <p className={`flex items-center gap-1 justify-end text-lg font-semibold ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
                {isUp ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                {isUp ? '+' : ''}{stock.change.toLocaleString('vi-VN')} ({isUp ? '+' : ''}{stock.change_pct.toFixed(2)}%)
              </p>
            </div>
            <button onClick={load} className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-gray-300" title="Làm mới">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick stats row */}
        <div className="grid grid-cols-3 gap-4 mt-5 pt-5 border-t border-gray-700">
          {[
            { label: 'Khối lượng', value: stock.volume.toLocaleString('vi-VN') },
            { label: 'Vốn hóa', value: stock.market_cap ? `${(stock.market_cap / 1e9).toFixed(1)}B đ` : '—' },
            { label: 'Sàn giao dịch', value: stock.exchange },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-xs text-gray-500 mb-0.5">{label}</p>
              <p className="text-sm font-semibold text-white">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-800 border border-gray-700 p-1 rounded-xl w-fit">
        {([
          { key: 'chart', label: 'Biểu đồ', icon: <Activity className="w-4 h-4" /> },
          { key: 'technical', label: 'Kỹ thuật', icon: <Activity className="w-4 h-4" /> },
          { key: 'prediction', label: 'Dự đoán AI', icon: <TrendingUp className="w-4 h-4" /> },
        ] as { key: typeof activeTab; label: string; icon: React.ReactNode }[]).map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === key
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content - chart or technical */}
        <div className="lg:col-span-2">
          {activeTab === 'chart' && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
              <h2 className="text-white font-semibold mb-4">Lịch sử giá</h2>
              {stock.history && stock.history.length > 0 ? (
                <StockChart history={stock.history} darkMode />
              ) : (
                <div className="h-48 flex items-center justify-center text-gray-500">
                  Không có dữ liệu lịch sử
                </div>
              )}
            </div>
          )}

          {activeTab === 'technical' && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
              <h2 className="text-white font-semibold mb-4">Chỉ số kỹ thuật</h2>
              {technical ? (
                <TechnicalIndicators data={technical} darkMode />
              ) : (
                <div className="py-12 text-center text-gray-500">
                  Không có dữ liệu kỹ thuật
                </div>
              )}
            </div>
          )}

          {activeTab === 'prediction' && prediction && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
              <h2 className="text-white font-semibold mb-4">Phân tích dự đoán chi tiết</h2>
              <PredictionCard prediction={prediction} stockName={stock.name} darkMode />
            </div>
          )}

          {activeTab === 'prediction' && !prediction && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 py-12 text-center text-gray-500">
              Không có dữ liệu dự đoán
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Prediction sidebar card */}
          {prediction && activeTab !== 'prediction' && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-3">Dự đoán nhanh</h3>
              <div className={`flex items-center gap-2 mb-3 ${prediction.direction === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
                {prediction.direction === 'up' ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                <span className="font-semibold">
                  {prediction.direction === 'up' ? 'Xu hướng tăng' : 'Xu hướng giảm'}
                </span>
                <span className="text-sm opacity-70">
                  ({Math.round(prediction.confidence * 100)}% tin cậy)
                </span>
              </div>
              <div className="space-y-2">
                {(['1', '7', '30'] as const).map((days) => {
                  const pred = prediction.predictions[days];
                  const diff = pred - prediction.current_price;
                  const pct = (diff / prediction.current_price) * 100;
                  return (
                    <div key={days} className="flex justify-between items-center p-2 bg-gray-700/50 rounded-lg">
                      <span className="text-gray-400 text-sm">{days} ngày</span>
                      <div className="text-right">
                        <span className="text-white text-sm font-semibold">{pred.toLocaleString('vi-VN')}</span>
                        <span className={`ml-2 text-xs ${pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {pct >= 0 ? '+' : ''}{pct.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Technical signal */}
          {technical && activeTab !== 'technical' && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-3">Tín hiệu kỹ thuật</h3>
              <div className={`flex items-center justify-between p-3 rounded-lg ${
                technical.signal === 'Buy' ? 'bg-emerald-500/10 border border-emerald-500/30' :
                technical.signal === 'Sell' ? 'bg-red-500/10 border border-red-500/30' :
                'bg-yellow-500/10 border border-yellow-500/30'
              }`}>
                <span className={`font-bold text-lg ${
                  technical.signal === 'Buy' ? 'text-emerald-400' :
                  technical.signal === 'Sell' ? 'text-red-400' :
                  'text-yellow-400'
                }`}>
                  {technical.signal === 'Buy' ? '▲ Mua' : technical.signal === 'Sell' ? '▼ Bán' : '◆ Giữ'}
                </span>
                <span className="text-gray-400 text-sm">
                  {Math.round(technical.signal_confidence * 100)}% tin cậy
                </span>
              </div>
              <div className="mt-3 space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">RSI</span>
                  <span className="text-white">{technical.indicators.rsi.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">MACD</span>
                  <span className={technical.indicators.macd.line >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                    {technical.indicators.macd.line.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
