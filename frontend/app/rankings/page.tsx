'use client';

import { useState, useEffect } from 'react';
import { fetchRankings, RankingStock } from '@/lib/api';
import RankingTable from '@/components/RankingTable';
import { TrendingUp, TrendingDown, Star, Award } from 'lucide-react';

type TabKey = 'top-buy' | 'top-decline' | 'trustworthy' | 'top-invest';

const TABS: { key: TabKey; label: string; icon: React.ReactNode; desc: string }[] = [
  {
    key: 'top-buy',
    label: 'Top Mua',
    icon: <TrendingUp className="w-4 h-4" />,
    desc: 'Cổ phiếu được AI khuyến nghị mua mạnh nhất',
  },
  {
    key: 'top-decline',
    label: 'Top Giảm Giá',
    icon: <TrendingDown className="w-4 h-4" />,
    desc: 'Cổ phiếu giảm mạnh nhất trong phiên',
  },
  {
    key: 'trustworthy',
    label: 'Uy Tín',
    icon: <Star className="w-4 h-4" />,
    desc: 'Cổ phiếu có lịch sử ổn định và đáng tin cậy',
  },
  {
    key: 'top-invest',
    label: 'Nên Đầu Tư',
    icon: <Award className="w-4 h-4" />,
    desc: 'Cổ phiếu tiềm năng nhất cho đầu tư dài hạn',
  },
];

export default function RankingsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('top-buy');
  const [data, setData] = useState<Record<TabKey, RankingStock[] | null>>({
    'top-buy': null,
    'top-decline': null,
    'trustworthy': null,
    'top-invest': null,
  });
  const [loading, setLoading] = useState<Record<TabKey, boolean>>({
    'top-buy': false,
    'top-decline': false,
    'trustworthy': false,
    'top-invest': false,
  });

  const loadTab = async (tab: TabKey) => {
    if (data[tab] !== null) return; // already loaded
    setLoading((l) => ({ ...l, [tab]: true }));
    const result = await fetchRankings(tab);
    setData((d) => ({ ...d, [tab]: result ?? [] }));
    setLoading((l) => ({ ...l, [tab]: false }));
  };

  useEffect(() => {
    loadTab(activeTab);
  }, [activeTab]);

  const currentTab = TABS.find((t) => t.key === activeTab)!;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">Bảng xếp hạng</h1>
        <p className="text-gray-400 text-sm">
          Xếp hạng cổ phiếu theo phân tích AI và chỉ số kỹ thuật
        </p>
      </div>

      {/* Tab navigation */}
      <div className="flex flex-wrap gap-2 mb-6">
        {TABS.map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === key
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                : 'bg-gray-800 text-gray-400 border border-gray-700 hover:text-white hover:border-gray-600'
            }`}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>

      {/* Tab description */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-6 flex items-center gap-3">
        <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
          {currentTab.icon}
        </div>
        <div>
          <p className="text-white font-semibold text-sm">{currentTab.label}</p>
          <p className="text-gray-400 text-xs">{currentTab.desc}</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
        {loading[activeTab] ? (
          <div className="py-16 flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-400 text-sm">Đang tải bảng xếp hạng...</p>
          </div>
        ) : (
          <RankingTable stocks={data[activeTab] ?? []} darkMode />
        )}
      </div>

      {/* Disclaimer */}
      <p className="text-gray-600 text-xs mt-4 text-center">
        * Xếp hạng chỉ mang tính tham khảo. Không phải khuyến nghị đầu tư. Hãy tự nghiên cứu trước khi đầu tư.
      </p>
    </div>
  );
}
