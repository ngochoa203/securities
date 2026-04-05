'use client';

import { useState, useEffect, useMemo } from 'react';
import { fetchStocks, fetchPrediction, StockSummary, PredictionResult } from '@/lib/api';
import PredictionCard from '@/components/PredictionCard';
import { TrendingUp, TrendingDown, Filter } from 'lucide-react';

type FilterDir = 'all' | 'up' | 'down';
type SortBy = 'confidence' | 'change' | 'symbol';

interface StockWithPrediction {
  stock: StockSummary;
  prediction: PredictionResult;
}

export default function PredictionsPage() {
  const [items, setItems] = useState<StockWithPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [dirFilter, setDirFilter] = useState<FilterDir>('all');
  const [sortBy, setSortBy] = useState<SortBy>('confidence');
  const [loadedCount, setLoadedCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchStocks().then(async (stocks) => {
      if (!stocks) { setLoading(false); return; }
      // Load top 20 stocks only to avoid too many requests
      const top = stocks.slice(0, 20);
      setTotalCount(top.length);

      const results: StockWithPrediction[] = [];
      for (const stock of top) {
        const prediction = await fetchPrediction(stock.symbol);
        if (prediction) {
          results.push({ stock, prediction });
          setItems([...results]);
        }
        setLoadedCount((c) => c + 1);
      }
      setLoading(false);
    });
  }, []);

  const filtered = useMemo(() => {
    let data = [...items];
    if (dirFilter !== 'all') {
      data = data.filter((i) => i.prediction.direction === dirFilter);
    }
    data.sort((a, b) => {
      if (sortBy === 'confidence') return b.prediction.confidence - a.prediction.confidence;
      if (sortBy === 'change') {
        const pa = (a.prediction.predictions['30'] - a.prediction.current_price) / a.prediction.current_price;
        const pb = (b.prediction.predictions['30'] - b.prediction.current_price) / b.prediction.current_price;
        return pb - pa;
      }
      return a.stock.symbol.localeCompare(b.stock.symbol);
    });
    return data;
  }, [items, dirFilter, sortBy]);

  const upCount = items.filter((i) => i.prediction.direction === 'up').length;
  const downCount = items.filter((i) => i.prediction.direction === 'down').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">Dự đoán AI</h1>
        <p className="text-gray-400 text-sm">
          Dự đoán xu hướng giá cổ phiếu 1–30 ngày bằng mô hình học máy (LSTM, XGBoost, Prophet)
        </p>
      </div>

      {/* Stats + Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        {/* Direction stats */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <span className="text-emerald-400 font-semibold">{upCount}</span>
            <span className="text-gray-400">tăng</span>
          </div>
          <div className="flex items-center gap-1.5 text-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
            <span className="text-red-400 font-semibold">{downCount}</span>
            <span className="text-gray-400">giảm</span>
          </div>
          {loading && (
            <span className="text-gray-500 text-xs">
              ({loadedCount}/{totalCount} đang tải...)
            </span>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          {/* Direction filter */}
          <div className="flex rounded-lg bg-gray-800 border border-gray-700 p-0.5">
            {([
              { key: 'all', label: 'Tất cả' },
              { key: 'up', label: '▲ Tăng' },
              { key: 'down', label: '▼ Giảm' },
            ] as { key: FilterDir; label: string }[]).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setDirFilter(key)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  dirFilter === key
                    ? key === 'up'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : key === 'down'
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortBy)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="confidence">Độ tin cậy</option>
              <option value="change">% Thay đổi dự báo</option>
              <option value="symbol">Mã CP</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loading skeleton */}
      {loading && items.length === 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="bg-gray-800 border border-gray-700 rounded-xl h-64 animate-pulse" />
          ))}
        </div>
      )}

      {/* Grid */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map(({ stock, prediction }) => (
            <PredictionCard
              key={stock.symbol}
              prediction={prediction}
              stockName={stock.name}
              darkMode
              compact
            />
          ))}
        </div>
      ) : (
        !loading && (
          <div className="py-16 text-center">
            <p className="text-gray-400">Không có dữ liệu dự đoán.</p>
          </div>
        )
      )}

      {/* Still loading - show progress bar */}
      {loading && items.length > 0 && (
        <div className="mt-6">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Đang tải dữ liệu dự đoán...</span>
            <span>{loadedCount}/{totalCount}</span>
          </div>
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all duration-300"
              style={{ width: `${totalCount > 0 ? (loadedCount / totalCount) * 100 : 0}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
