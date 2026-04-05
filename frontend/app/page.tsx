'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  TrendingUp,
  TrendingDown,
  Search,
  BarChart2,
  Zap,
  Shield,
  ArrowRight,
} from 'lucide-react';
import {
  fetchStocks,
  fetchRankings,
  StockSummary,
  RankingStock,
} from '@/lib/api';

function MiniStockCard({ stock }: { stock: StockSummary }) {
  const isUp = stock.change_pct >= 0;
  return (
    <Link href={`/stocks/${stock.symbol}`}>
      <div className="flex items-center justify-between p-3 rounded-lg border border-gray-700 bg-gray-700/50 hover:border-emerald-500/50 transition-colors">
        <div>
          <p className="font-bold text-sm text-white">{stock.symbol}</p>
          <p className="text-xs truncate max-w-[120px] text-gray-400">{stock.name}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-white">
            {stock.price.toLocaleString('vi-VN')}
          </p>
          <p className={`text-xs font-medium flex items-center gap-0.5 justify-end ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
            {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {isUp ? '+' : ''}{stock.change_pct.toFixed(2)}%
          </p>
        </div>
      </div>
    </Link>
  );
}

function RankMiniCard({ stock, rank }: { stock: RankingStock; rank: number }) {
  const isUp = stock.change_pct >= 0;
  return (
    <Link href={`/stocks/${stock.symbol}`}>
      <div className="flex items-center gap-3 p-3 rounded-lg border border-gray-700 bg-gray-700/50 hover:border-emerald-500/50 transition-colors">
        <span className={`text-xs font-bold w-5 text-center ${rank === 1 ? 'text-yellow-400' : rank === 2 ? 'text-gray-400' : 'text-orange-400'}`}>
          {rank}
        </span>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-sm text-white">{stock.symbol}</p>
          <p className="text-xs truncate text-gray-400">{stock.reason}</p>
        </div>
        <span className={`text-xs font-semibold ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
          {isUp ? '+' : ''}{stock.change_pct.toFixed(2)}%
        </span>
      </div>
    </Link>
  );
}

export default function HomePage() {
  const router = useRouter();
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [topBuy, setTopBuy] = useState<RankingStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    Promise.all([fetchStocks(), fetchRankings('top-buy')]).then(
      ([stocksData, rankData]) => {
        if (stocksData) setStocks(stocksData);
        if (rankData) setTopBuy(rankData.slice(0, 3));
        setLoading(false);
      }
    );
  }, []);

  const topGainers = [...stocks].sort((a, b) => b.change_pct - a.change_pct).slice(0, 3);
  const topLosers = [...stocks].sort((a, b) => a.change_pct - b.change_pct).slice(0, 3);

  const totalUp = stocks.filter((s) => s.change_pct > 0).length;
  const totalDown = stocks.filter((s) => s.change_pct < 0).length;
  const avgChange = stocks.length > 0
    ? stocks.reduce((s, x) => s + x.change_pct, 0) / stocks.length
    : 0;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchQuery.trim().toUpperCase();
    if (q) router.push(`/stocks?q=${encodeURIComponent(q)}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 bg-emerald-500/10 text-emerald-400 px-4 py-1.5 rounded-full text-sm font-medium mb-4 border border-emerald-500/20">
          <Zap className="w-4 h-4" />
          Phân tích AI thời gian thực
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-4 leading-tight">
          Dự đoán cổ phiếu{' '}
          <span className="text-emerald-400">thông minh</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto mb-8">
          Ứng dụng trí tuệ nhân tạo (LSTM, XGBoost, Prophet) để phân tích và dự đoán
          xu hướng thị trường chứng khoán Việt Nam
        </p>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex max-w-lg mx-auto gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="Tìm cổ phiếu... (VD: VNM, FPT, VIC)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold rounded-xl transition-colors"
          >
            Tìm kiếm
          </button>
        </form>
      </div>

      {/* Quick stats */}
      {!loading && stocks.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Tổng cổ phiếu', val: stocks.length.toString(), color: 'text-blue-400', icon: <BarChart2 className="w-5 h-5 text-blue-400" /> },
            { label: 'Thay đổi TB', val: `${avgChange >= 0 ? '+' : ''}${avgChange.toFixed(2)}%`, color: avgChange >= 0 ? 'text-emerald-400' : 'text-red-400', icon: avgChange >= 0 ? <TrendingUp className="w-5 h-5 text-emerald-400" /> : <TrendingDown className="w-5 h-5 text-red-400" /> },
            { label: 'Cổ phiếu tăng', val: totalUp.toString(), color: 'text-emerald-400', icon: <TrendingUp className="w-5 h-5 text-emerald-400" /> },
            { label: 'Cổ phiếu giảm', val: totalDown.toString(), color: 'text-red-400', icon: <TrendingDown className="w-5 h-5 text-red-400" /> },
          ].map(({ label, val, color, icon }) => (
            <div key={label} className="bg-gray-800 border border-gray-700 rounded-xl p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-gray-400 mb-1">{label}</p>
                  <p className={`text-2xl font-bold ${color}`}>{val}</p>
                </div>
                <div className="p-2 bg-gray-700 rounded-lg">{icon}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-800 border border-gray-700 rounded-xl p-5 h-64 animate-pulse" />
          ))}
        </div>
      )}

      {/* Three columns */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Top Gainers */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-emerald-500/20 rounded-lg">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                </div>
                <h2 className="font-semibold text-white">Tăng mạnh nhất</h2>
              </div>
              <Link href="/stocks" className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
                Xem tất cả <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="space-y-2">
              {topGainers.map((s) => <MiniStockCard key={s.symbol} stock={s} />)}
            </div>
          </div>

          {/* Top Losers */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-red-500/20 rounded-lg">
                  <TrendingDown className="w-4 h-4 text-red-400" />
                </div>
                <h2 className="font-semibold text-white">Giảm mạnh nhất</h2>
              </div>
              <Link href="/stocks" className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1">
                Xem tất cả <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="space-y-2">
              {topLosers.map((s) => <MiniStockCard key={s.symbol} stock={s} />)}
            </div>
          </div>

          {/* AI Picks */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-blue-500/20 rounded-lg">
                  <Shield className="w-4 h-4 text-blue-400" />
                </div>
                <h2 className="font-semibold text-white">AI Khuyến nghị</h2>
              </div>
              <Link href="/rankings" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
                Xem tất cả <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="space-y-2">
              {topBuy.length > 0
                ? topBuy.map((s, i) => <RankMiniCard key={s.symbol} stock={s} rank={i + 1} />)
                : <p className="text-sm text-gray-500">Đang tải dữ liệu AI...</p>
              }
            </div>
          </div>
        </div>
      )}

      {/* CTA cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { href: '/stocks', icon: <BarChart2 className="w-6 h-6 text-emerald-400" />, bg: 'bg-emerald-500/10', title: 'Danh sách cổ phiếu', desc: 'Xem tất cả cổ phiếu với giá thời gian thực', accentColor: 'text-emerald-400' },
          { href: '/predictions', icon: <Zap className="w-6 h-6 text-blue-400" />, bg: 'bg-blue-500/10', title: 'Dự đoán AI', desc: 'Dự báo giá 1–30 ngày bằng mô hình học máy', accentColor: 'text-blue-400' },
          { href: '/guide', icon: <Shield className="w-6 h-6 text-purple-400" />, bg: 'bg-purple-500/10', title: 'Hướng dẫn đầu tư', desc: 'Kiến thức cơ bản cho nhà đầu tư mới', accentColor: 'text-purple-400' },
        ].map(({ href, icon, bg, title, desc, accentColor }) => (
          <Link key={href} href={href}>
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 hover:shadow-lg transition-all group hover:border-gray-600">
              <div className={`p-2.5 ${bg} rounded-lg w-fit mb-3`}>{icon}</div>
              <h3 className="font-semibold text-white mb-1">{title}</h3>
              <p className="text-gray-400 text-sm">{desc}</p>
              <div className={`flex items-center gap-1 ${accentColor} text-sm mt-3 group-hover:gap-2 transition-all`}>
                Khám phá <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
