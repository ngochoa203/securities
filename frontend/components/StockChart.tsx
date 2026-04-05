'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import { HistoryPoint } from '@/lib/api';

interface StockChartProps {
  history: HistoryPoint[];
  darkMode?: boolean;
}

interface CustomTooltipProps extends TooltipProps<number, string> {
  active?: boolean;
  payload?: Array<{ payload: HistoryPoint }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0]?.payload as HistoryPoint;
  return (
    <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      <p className="text-white font-semibold">
        Đóng cửa:{' '}
        <span className="text-emerald-400">
          {data?.close?.toLocaleString('vi-VN')} đ
        </span>
      </p>
      <p className="text-gray-300">
        Mở cửa: {data?.open?.toLocaleString('vi-VN')} đ
      </p>
      <p className="text-gray-300">
        Cao nhất: {data?.high?.toLocaleString('vi-VN')} đ
      </p>
      <p className="text-gray-300">
        Thấp nhất: {data?.low?.toLocaleString('vi-VN')} đ
      </p>
      <p className="text-gray-300">
        KL: {data?.volume?.toLocaleString('vi-VN')}
      </p>
    </div>
  );
}

export default function StockChart({ history, darkMode = true }: StockChartProps) {
  if (!history || history.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        Không có dữ liệu lịch sử
      </div>
    );
  }

  const first = history[0].close;
  const last = history[history.length - 1].close;
  const isUp = last >= first;
  const strokeColor = isUp ? '#10b981' : '#ef4444';
  const gradientStart = isUp ? '#10b981' : '#ef4444';

  // Format dates for display
  const data = history.map((h) => ({
    ...h,
    dateLabel: new Date(h.date).toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
    }),
  }));

  const prices = history.map((h) => h.close);
  const minPrice = Math.min(...prices) * 0.995;
  const maxPrice = Math.max(...prices) * 1.005;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={gradientStart} stopOpacity={0.3} />
            <stop offset="95%" stopColor={gradientStart} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={darkMode ? '#374151' : '#e5e7eb'}
          vertical={false}
        />
        <XAxis
          dataKey="dateLabel"
          tick={{ fill: darkMode ? '#9ca3af' : '#6b7280', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[minPrice, maxPrice]}
          tick={{ fill: darkMode ? '#9ca3af' : '#6b7280', fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) =>
            v >= 1000
              ? `${(v / 1000).toFixed(0)}k`
              : v.toFixed(0)
          }
          width={50}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="close"
          stroke={strokeColor}
          strokeWidth={2}
          fill="url(#colorClose)"
          dot={false}
          activeDot={{ r: 4, fill: strokeColor, stroke: 'white', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
