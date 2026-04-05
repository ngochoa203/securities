'use client';

import { useState, useEffect, useMemo, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Search, TrendingUp, TrendingDown, ChevronUp, ChevronDown, Eye } from 'lucide-react';
import { fetchStocks, StockSummary } from '@/lib/api';

type SortKey = 'symbol' | 'name' | 'price' | 'change_pct' | 'volume';
type SortDir = 'asc' | 'desc';

function StocksContent() {
  const searchParams = useSearchParams();
  const [stocks, setStocks] = useState<StockSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [sortKey, setSortKey] = useState<SortKey>('symbol');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  useEffect(() => {
    fetchStocks().then((data) => {
      if (data) setStocks(data);
      setLoading(false);
    });
  }, []);

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    return stocks.filter(
      (s) =>
        !q ||
        s.symbol.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q)
    );
  }, [stocks, query]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (typeof va === 'string' && typeof vb === 'string') {
        return sortDir === 'asc'
          ? va.localeCompare(vb)
          : vb.localeCompare(va);
      }
      return sortDir === 'asc'
        ? (va as number) - (vb as number)
        : (vb as number) - (va as number);
    });
  }, [filtered, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <ChevronUp className="w-3 h-3 opacity-30" />;
    return sortDir === 'asc' ? (
      <ChevronUp className="w-3 h-3 text-emerald-400" />
    ) : (
      <ChevronDown className="w-3 h-3 text-emerald-400" />
    );
  };

  const textP = 'text-white';
  const textS = 'text-gray-400';
  const borderC = 'border-gray-700';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className={`text-2xl font-bold ${textP} mb-1`}>Danh sách cổ phiếu</h1>
        <p className={`text-sm ${textS}`}>
          {loading ? 'Đang tải...' : `${stocks.length} cổ phiếu · ${filtered.length} kết quả`}
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
        <input
          type="text"
          placeholder="Tìm theo mã hoặc tên công ty..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors text-sm"
        />
      </div>

      {/* Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
        {loading ? (
          <div className="py-12 text-center">
            <div className="inline-block w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
            <p className={textS}>Đang tải dữ liệu cổ phiếu...</p>
          </div>
        ) : sorted.length === 0 ? (
          <div className="py-12 text-center">
            <p className={textS}>Không tìm thấy cổ phiếu nào.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={`border-b ${borderC} bg-gray-900/50`}>
                  {(
                    [
                      { key: 'symbol', label: 'Mã CP' },
                      { key: 'name', label: 'Tên công ty' },
                      { key: 'price', label: 'Giá (đ)' },
                      { key: 'change_pct', label: 'Thay đổi %' },
                      { key: 'volume', label: 'KL giao dịch' },
                    ] as { key: SortKey; label: string }[]
                  ).map(({ key, label }) => (
                    <th
                      key={key}
                      onClick={() => handleSort(key)}
                      className={`text-left py-3 px-4 font-semibold cursor-pointer select-none hover:text-white transition-colors ${textS} ${
                        key === 'name' ? 'hidden sm:table-cell' : ''
                      } ${key === 'volume' ? 'hidden md:table-cell' : ''}`}
                    >
                      <span className="flex items-center gap-1">
                        {label}
                        <SortIcon col={key} />
                      </span>
                    </th>
                  ))}
                  <th className={`text-center py-3 px-4 font-semibold ${textS}`}>
                    Chi tiết
                  </th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((stock) => {
                  const isUp = stock.change_pct >= 0;
                  return (
                    <tr
                      key={stock.symbol}
                      className={`border-b ${borderC} hover:bg-gray-700/40 transition-colors`}
                    >
                      <td className="py-3 px-4">
                        <div>
                          <Link
                            href={`/stocks/${stock.symbol}`}
                            className={`font-bold hover:text-emerald-400 transition-colors ${textP}`}
                          >
                            {stock.symbol}
                          </Link>
                          <p className={`text-xs ${textS}`}>{stock.exchange}</p>
                        </div>
                      </td>
                      <td className={`py-3 px-4 hidden sm:table-cell ${textS} max-w-[200px] truncate`}>
                        {stock.name}
                      </td>
                      <td className={`py-3 px-4 font-semibold ${textP}`}>
                        {stock.price.toLocaleString('vi-VN')}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 text-sm font-semibold ${
                            isUp ? 'text-emerald-400' : 'text-red-400'
                          }`}
                        >
                          {isUp ? (
                            <TrendingUp className="w-3.5 h-3.5" />
                          ) : (
                            <TrendingDown className="w-3.5 h-3.5" />
                          )}
                          {isUp ? '+' : ''}{stock.change_pct.toFixed(2)}%
                        </span>
                        <p className={`text-xs ${textS}`}>
                          {isUp ? '+' : ''}{stock.change.toLocaleString('vi-VN')}
                        </p>
                      </td>
                      <td className={`py-3 px-4 hidden md:table-cell ${textS}`}>
                        {stock.volume.toLocaleString('vi-VN')}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Link
                          href={`/stocks/${stock.symbol}`}
                          className="inline-flex items-center justify-center p-2 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default function StocksPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <div className="inline-block w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-gray-400">Đang tải...</p>
        </div>
      }
    >
      <StocksContent />
    </Suspense>
  );
}
