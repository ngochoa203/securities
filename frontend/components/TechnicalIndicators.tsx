'use client';

import { TechnicalResult } from '@/lib/api';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

interface TechnicalIndicatorsProps {
  data: TechnicalResult;
  darkMode?: boolean;
}

function RSIGauge({ value, darkMode }: { value: number; darkMode: boolean }) {
  const clamped = Math.max(0, Math.min(100, value));
  const color =
    clamped >= 70
      ? '#ef4444'
      : clamped <= 30
      ? '#10b981'
      : '#f59e0b';
  const label =
    clamped >= 70
      ? 'Quá mua'
      : clamped <= 30
      ? 'Quá bán'
      : 'Trung lập';

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className={`text-xs font-medium ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          RSI (14)
        </span>
        <span className="text-xs font-bold" style={{ color }}>
          {clamped.toFixed(1)} — {label}
        </span>
      </div>
      <div className={`relative h-3 rounded-full overflow-hidden ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
        {/* zones */}
        <div className="absolute inset-0 flex">
          <div className="w-[30%] bg-emerald-500/20" />
          <div className="w-[40%] bg-yellow-500/10" />
          <div className="w-[30%] bg-red-500/20" />
        </div>
        {/* indicator */}
        <div
          className="absolute top-0 bottom-0 w-1 rounded-full bg-white shadow"
          style={{ left: `calc(${clamped}% - 2px)` }}
        />
      </div>
      <div className="flex justify-between text-xs mt-0.5">
        <span className="text-emerald-400">0 Quá bán</span>
        <span className={darkMode ? 'text-gray-500' : 'text-gray-400'}>50</span>
        <span className="text-red-400">100 Quá mua</span>
      </div>
    </div>
  );
}

function SignalBadge({
  signal,
  confidence,
}: {
  signal: string;
  confidence: number;
}) {
  const isB = signal.toLowerCase() === 'buy';
  const isS = signal.toLowerCase() === 'sell';
  const bg = isB
    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    : isS
    ? 'bg-red-500/20 text-red-400 border-red-500/30'
    : 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  const Icon = isB ? TrendingUp : isS ? TrendingDown : Minus;
  const label = isB ? 'Mua' : isS ? 'Bán' : 'Giữ';

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl border ${bg}`}>
      <Icon className="w-5 h-5" />
      <span className="font-bold text-lg">{label}</span>
      <span className="text-sm opacity-80">({Math.round(confidence * 100)}%)</span>
    </div>
  );
}

export default function TechnicalIndicators({
  data,
  darkMode = true,
}: TechnicalIndicatorsProps) {
  const { indicators, signal, signal_confidence } = data;
  const { rsi, macd, bollinger, sma, ema } = indicators;

  const cardBg = darkMode ? 'bg-gray-700/50' : 'bg-gray-50';
  const textPrimary = darkMode ? 'text-white' : 'text-gray-900';
  const textSecondary = darkMode ? 'text-gray-400' : 'text-gray-500';
  const borderColor = darkMode ? 'border-gray-600' : 'border-gray-200';

  const macdColor =
    macd.histogram >= 0 ? 'text-emerald-400' : 'text-red-400';

  return (
    <div className="space-y-4">
      {/* Overall signal */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-400" />
          <span className={`font-semibold ${textPrimary}`}>Tín hiệu kỹ thuật</span>
        </div>
        <SignalBadge signal={signal} confidence={signal_confidence} />
      </div>

      {/* RSI */}
      <div className={`rounded-xl p-4 ${cardBg}`}>
        <RSIGauge value={rsi} darkMode={darkMode} />
      </div>

      {/* MACD */}
      <div className={`rounded-xl p-4 ${cardBg}`}>
        <p className={`text-xs font-semibold mb-3 ${textSecondary}`}>MACD</p>
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center">
            <p className={`text-xs ${textSecondary}`}>Đường MACD</p>
            <p className={`font-semibold text-sm mt-1 ${macdColor}`}>
              {macd.line.toFixed(3)}
            </p>
          </div>
          <div className="text-center">
            <p className={`text-xs ${textSecondary}`}>Đường tín hiệu</p>
            <p className={`font-semibold text-sm mt-1 ${textPrimary}`}>
              {macd.signal.toFixed(3)}
            </p>
          </div>
          <div className="text-center">
            <p className={`text-xs ${textSecondary}`}>Histogram</p>
            <p
              className={`font-semibold text-sm mt-1 ${
                macd.histogram >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {macd.histogram >= 0 ? '+' : ''}{macd.histogram.toFixed(3)}
            </p>
          </div>
        </div>
      </div>

      {/* Bollinger Bands */}
      <div className={`rounded-xl p-4 ${cardBg}`}>
        <p className={`text-xs font-semibold mb-3 ${textSecondary}`}>
          Dải Bollinger
        </p>
        <div className="space-y-2">
          {[
            { label: 'Dải trên', value: bollinger.upper, color: 'text-red-400' },
            { label: 'Dải giữa', value: bollinger.middle, color: textPrimary },
            { label: 'Dải dưới', value: bollinger.lower, color: 'text-emerald-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className={`flex justify-between border-b ${borderColor} pb-1 last:border-0 last:pb-0`}>
              <span className={`text-xs ${textSecondary}`}>{label}</span>
              <span className={`text-xs font-medium ${color}`}>
                {value.toLocaleString('vi-VN')}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* SMA / EMA */}
      <div className={`rounded-xl p-4 ${cardBg}`}>
        <p className={`text-xs font-semibold mb-3 ${textSecondary}`}>
          Đường trung bình động
        </p>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'SMA 20', value: sma?.sma_20 },
            { label: 'SMA 50', value: sma?.sma_50 },
            { label: 'SMA 200', value: sma?.sma_200 },
            ...(ema
              ? Object.entries(ema)
                  .filter(([, v]) => v !== undefined)
                  .map(([k, v]) => ({ label: k.toUpperCase().replace('_', ' '), value: v as number }))
              : []),
          ]
            .filter((item) => item.value !== undefined && item.value !== null)
            .map(({ label, value }) => (
              <div key={label} className="flex justify-between">
                <span className={`text-xs ${textSecondary}`}>{label}</span>
                <span className={`text-xs font-medium ${textPrimary}`}>
                  {(value as number).toLocaleString('vi-VN')}
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
