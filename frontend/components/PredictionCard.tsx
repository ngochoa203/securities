'use client';

import Link from 'next/link';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { PredictionResult } from '@/lib/api';

interface PredictionCardProps {
  prediction: PredictionResult;
  stockName?: string;
  darkMode?: boolean;
  compact?: boolean;
}

function ConfidenceBar({
  value,
  darkMode,
}: {
  value: number;
  darkMode: boolean;
}) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? 'bg-emerald-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>
          Độ tin cậy
        </span>
        <span className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          {pct}%
        </span>
      </div>
      <div className={`h-2 rounded-full ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
        <div
          className={`h-2 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function PredictionCard({
  prediction,
  stockName,
  darkMode = true,
  compact = false,
}: PredictionCardProps) {
  const isUp = prediction.direction === 'up';
  const pctChange =
    ((prediction.predictions['30'] - prediction.current_price) /
      prediction.current_price) *
    100;

  const cardBg = darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200';
  const textPrimary = darkMode ? 'text-white' : 'text-gray-900';
  const textSecondary = darkMode ? 'text-gray-400' : 'text-gray-500';

  return (
    <Link href={`/stocks/${prediction.symbol}`} className="block group">
      <div
        className={`border rounded-xl p-5 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 ${cardBg} ${
          isUp
            ? 'hover:border-emerald-500/50'
            : 'hover:border-red-500/50'
        }`}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${textPrimary}`}>
                {prediction.symbol}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  isUp
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'bg-red-500/20 text-red-400'
                }`}
              >
                {isUp ? '▲ Tăng' : '▼ Giảm'}
              </span>
            </div>
            {stockName && (
              <p className={`text-xs mt-0.5 ${textSecondary}`}>{stockName}</p>
            )}
          </div>
          <div
            className={`p-2 rounded-lg ${
              isUp ? 'bg-emerald-500/20' : 'bg-red-500/20'
            }`}
          >
            {isUp ? (
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-400" />
            )}
          </div>
        </div>

        {/* Current price */}
        <div className="mb-4">
          <p className={`text-xs ${textSecondary}`}>Giá hiện tại</p>
          <p className={`text-xl font-bold ${textPrimary}`}>
            {prediction.current_price.toLocaleString('vi-VN')}
            <span className={`text-sm font-normal ${textSecondary} ml-1`}>đ</span>
          </p>
        </div>

        {/* Predictions grid */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {(['1', '7', '30'] as const).map((days) => {
            const pred = prediction.predictions[days];
            const diff = pred - prediction.current_price;
            const pct = (diff / prediction.current_price) * 100;
            const positive = diff >= 0;
            return (
              <div
                key={days}
                className={`rounded-lg p-2 text-center ${
                  darkMode ? 'bg-gray-700/50' : 'bg-gray-50'
                }`}
              >
                <p className={`text-xs ${textSecondary}`}>{days} ngày</p>
                <p
                  className={`text-sm font-semibold mt-0.5 ${
                    positive ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {pred.toLocaleString('vi-VN')}
                </p>
                <p
                  className={`text-xs ${
                    positive ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {positive ? '+' : ''}{pct.toFixed(1)}%
                </p>
              </div>
            );
          })}
        </div>

        {/* Confidence */}
        <ConfidenceBar value={prediction.confidence} darkMode={darkMode} />

        {/* Model details */}
        {!compact && prediction.model_details && Object.keys(prediction.model_details).length > 0 && (
          <div className={`mt-3 pt-3 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <p className={`text-xs mb-2 ${textSecondary}`}>Dự đoán mô hình</p>
            <div className="space-y-1">
              {Object.entries(prediction.model_details).map(([model, price]) => {
                if (price === undefined) return null;
                return (
                  <div key={model} className="flex justify-between text-xs">
                    <span className={textSecondary}>{model.toUpperCase()}</span>
                    <span className={textPrimary}>
                      {price.toLocaleString('vi-VN')} đ
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
