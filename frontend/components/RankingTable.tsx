'use client';

import Link from 'next/link';
import { TrendingUp, TrendingDown, Minus, Eye } from 'lucide-react';
import { RankingStock } from '@/lib/api';

interface RankingTableProps {
  stocks: RankingStock[];
  darkMode?: boolean;
}

function SignalBadge({ signal }: { signal: string }) {
  const normalized = signal.toLowerCase();
  if (normalized.includes('buy') || normalized.includes('mua')) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-semibold">
        <TrendingUp className="w-3 h-3" /> Mua
      </span>
    );
  }
  if (normalized.includes('sell') || normalized.includes('bán')) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-xs font-semibold">
        <TrendingDown className="w-3 h-3" /> Bán
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-500/20 text-gray-400 text-xs font-semibold">
      <Minus className="w-3 h-3" /> Giữ
    </span>
  );
}

export default function RankingTable({ stocks, darkMode = true }: RankingTableProps) {
  if (!stocks || stocks.length === 0) {
    return (
      <div className={`text-center py-12 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
        Không có dữ liệu
      </div>
    );
  }

  const textPrimary = darkMode ? 'text-white' : 'text-gray-900';
  const textSecondary = darkMode ? 'text-gray-400' : 'text-gray-500';
  const borderColor = darkMode ? 'border-gray-700' : 'border-gray-200';
  const hoverBg = darkMode ? 'hover:bg-gray-700/50' : 'hover:bg-gray-50';

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className={`border-b ${borderColor}`}>
            <th className={`text-left py-3 px-4 font-semibold ${textSecondary} w-10`}>#</th>
            <th className={`text-left py-3 px-4 font-semibold ${textSecondary}`}>Mã CP</th>
            <th className={`text-left py-3 px-4 font-semibold ${textSecondary} hidden sm:table-cell`}>
              Tên công ty
            </th>
            <th className={`text-right py-3 px-4 font-semibold ${textSecondary}`}>Giá</th>
            <th className={`text-right py-3 px-4 font-semibold ${textSecondary}`}>Thay đổi %</th>
            <th className={`text-center py-3 px-4 font-semibold ${textSecondary} hidden md:table-cell`}>
              Tín hiệu
            </th>
            <th className={`text-left py-3 px-4 font-semibold ${textSecondary} hidden lg:table-cell`}>
              Lý do
            </th>
            <th className={`text-center py-3 px-4 font-semibold ${textSecondary}`}>Chi tiết</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, i) => {
            const isUp = stock.change_pct >= 0;
            return (
              <tr
                key={stock.symbol}
                className={`border-b ${borderColor} ${hoverBg} transition-colors`}
              >
                <td className={`py-3 px-4 ${textSecondary}`}>
                  <span
                    className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${
                      i === 0
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : i === 1
                        ? 'bg-gray-400/20 text-gray-300'
                        : i === 2
                        ? 'bg-orange-500/20 text-orange-400'
                        : darkMode
                        ? 'text-gray-500'
                        : 'text-gray-400'
                    }`}
                  >
                    {i + 1}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <Link
                    href={`/stocks/${stock.symbol}`}
                    className={`font-bold hover:text-emerald-400 transition-colors ${textPrimary}`}
                  >
                    {stock.symbol}
                  </Link>
                </td>
                <td className={`py-3 px-4 hidden sm:table-cell ${textSecondary} max-w-[180px] truncate`}>
                  {stock.name}
                </td>
                <td className={`py-3 px-4 text-right font-medium ${textPrimary}`}>
                  {stock.price.toLocaleString('vi-VN')}
                </td>
                <td className={`py-3 px-4 text-right font-semibold ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isUp ? '+' : ''}{stock.change_pct.toFixed(2)}%
                </td>
                <td className="py-3 px-4 text-center hidden md:table-cell">
                  <SignalBadge signal={stock.signal} />
                </td>
                <td className={`py-3 px-4 hidden lg:table-cell ${textSecondary} text-xs max-w-[200px] truncate`}>
                  {stock.reason}
                </td>
                <td className="py-3 px-4 text-center">
                  <Link
                    href={`/stocks/${stock.symbol}`}
                    className="inline-flex items-center justify-center p-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
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
  );
}
