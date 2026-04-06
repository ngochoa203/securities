'use client';

import { useEffect, useState, useRef } from 'react';
import { fetchStocks, StockSummary } from '@/lib/api';
import { TrendingUp, TrendingDown } from 'lucide-react';

function TickerItem({ stock }: { stock: StockSummary }) {
  const isUp = stock.change >= 0;
  return (
    <span className="inline-flex items-center gap-2 px-4 border-r border-gray-700/50 last:border-r-0">
      <span className="font-bold text-white text-sm">{stock.symbol}</span>
      <span className={`text-sm font-medium ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
        {stock.price.toLocaleString('vi-VN')}
      </span>
      <span className={`flex items-center gap-0.5 text-xs ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
        {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        {isUp ? '+' : ''}{stock.change_pct.toFixed(2)}%
      </span>
    </span>
  );
}

export default function StockTicker() {
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const load = () => {
      fetchStocks().then((data) => {
        if (data) setStocks(data.slice(0, 20));
        setLoading(false);
      });
    };
    load();
    const interval = setInterval(load, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-900 border-b border-gray-700 h-9 flex items-center px-4">
        <span className="text-gray-500 text-xs animate-pulse">Đang tải dữ liệu thị trường...</span>
      </div>
    );
  }

  if (stocks.length === 0) {
    return (
      <div className="bg-gray-900 border-b border-gray-700 h-9 flex items-center px-4">
        <span className="text-gray-500 text-xs">Không có dữ liệu thị trường</span>
      </div>
    );
  }

  // Duplicate for seamless loop
  const doubled = [...stocks, ...stocks];

  return (
    <div className="bg-gray-900 border-b border-gray-700 overflow-hidden h-9 flex items-center">
      <div className="flex-none px-3 border-r border-gray-700 h-full flex items-center">
        <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider whitespace-nowrap">
          Thị trường
        </span>
      </div>
      <div className="overflow-hidden flex-1 relative">
        <div
          ref={containerRef}
          className="flex items-center animate-ticker whitespace-nowrap"
          style={{
            animation: 'ticker 40s linear infinite',
          }}
        >
          {doubled.map((stock, i) => (
            <TickerItem key={`${stock.symbol}-${i}`} stock={stock} />
          ))}
        </div>
      </div>
      <style jsx global>{`
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
