'use client';

import { useState, useEffect } from 'react';
import { fetchGuide, GuideSection } from '@/lib/api';
import { ChevronDown, BookOpen, TrendingUp, DollarSign, Shield, BarChart2, BookMarked, HelpCircle } from 'lucide-react';

// Static fallback guide content in Vietnamese
const STATIC_GUIDE: GuideSection[] = [
  {
    title: 'Chứng khoán là gì?',
    content: `Chứng khoán là tài sản tài chính đại diện cho quyền sở hữu một phần trong công ty (cổ phiếu) hoặc khoản vay (trái phiếu). Khi mua cổ phiếu của một công ty, bạn trở thành cổ đông và có quyền hưởng lợi nhuận từ hoạt động kinh doanh của công ty đó.

Thị trường chứng khoán Việt Nam bao gồm:
• HOSE (Sở Giao dịch Chứng khoán TP.HCM): Giao dịch cổ phiếu lớn, blue-chip
• HNX (Sở Giao dịch Chứng khoán Hà Nội): Cổ phiếu vừa và nhỏ, trái phiếu
• UPCOM: Thị trường dành cho cổ phiếu chưa niêm yết chính thức

Mã cổ phiếu gồm 3 chữ cái (ví dụ: VNM, FPT, VIC, HPG) và đại diện cho công ty phát hành.`,
  },
  {
    title: 'Cách mở tài khoản chứng khoán',
    content: `Để bắt đầu đầu tư, bạn cần mở tài khoản tại công ty chứng khoán (CTCK). Các bước cơ bản:

1. Chọn công ty chứng khoán: SSI, VPS, VNDirect, VCBS, MBS...
2. Chuẩn bị hồ sơ: CMND/CCCD, tài khoản ngân hàng
3. Đăng ký trực tuyến: Hầu hết CTCK hỗ trợ mở tài khoản online trong 15-30 phút
4. Nạp tiền: Chuyển khoản vào tài khoản chứng khoán
5. Bắt đầu giao dịch: Sử dụng ứng dụng hoặc web của CTCK

Lưu ý: Bạn có thể sở hữu nhiều tài khoản tại các CTCK khác nhau, nhưng mỗi CTCK chỉ được 1 tài khoản.`,
  },
  {
    title: 'Cách đặt lệnh mua/bán',
    content: `Thời gian giao dịch HOSE: 09:00 - 11:30 và 13:00 - 14:45 (Thứ 2 - Thứ 6).

Các loại lệnh phổ biến:
• Lệnh LO (Limit Order): Đặt mua/bán tại một mức giá xác định. Lệnh chỉ khớp khi giá thị trường đạt mức bạn đặt.
• Lệnh MP (Market Price): Mua/bán theo giá thị trường tốt nhất hiện tại. Khớp ngay nhưng giá không cố định.
• Lệnh ATO/ATC: Khớp lệnh tại phiên mở cửa (ATO) hoặc đóng cửa (ATC).

Bước đặt lệnh mua:
1. Chọn mã cổ phiếu
2. Chọn "Mua" → Nhập khối lượng (tối thiểu 100 cổ phiếu trên HOSE)
3. Nhập giá (hoặc chọn lệnh thị trường)
4. Xác nhận lệnh

Đơn vị giao dịch: 100 cổ phiếu/lô trên HOSE; 1 cổ phiếu trên HNX và UPCOM.`,
  },
  {
    title: 'Phân tích kỹ thuật cơ bản',
    content: `Phân tích kỹ thuật sử dụng biểu đồ giá và khối lượng để dự đoán xu hướng tương lai.

Các chỉ số quan trọng:

RSI (Relative Strength Index):
• Dao động từ 0-100
• RSI > 70: Cổ phiếu bị mua quá mức (Overbought) → có thể giảm
• RSI < 30: Cổ phiếu bị bán quá mức (Oversold) → có thể tăng
• RSI 40-60: Vùng trung tính

MACD (Moving Average Convergence Divergence):
• Khi đường MACD cắt đường tín hiệu từ dưới lên → Tín hiệu Mua
• Khi đường MACD cắt đường tín hiệu từ trên xuống → Tín hiệu Bán

Bollinger Bands:
• Dải trên: Ngưỡng kháng cự
• Dải giữa: SMA 20 ngày
• Dải dưới: Ngưỡng hỗ trợ
• Giá chạm dải dưới → có thể bật tăng

Đường trung bình động (MA/SMA):
• SMA 20: Xu hướng ngắn hạn
• SMA 50: Xu hướng trung hạn
• SMA 200: Xu hướng dài hạn
• Giá vượt MA → Tín hiệu tăng`,
  },
  {
    title: 'Quản lý rủi ro khi đầu tư',
    content: `Quản lý rủi ro là yếu tố quan trọng nhất trong đầu tư chứng khoán. Một nhà đầu tư giỏi không phải là người luôn thắng, mà là người biết kiểm soát thua lỗ.

Nguyên tắc cơ bản:

1. Đa dạng hóa danh mục (Diversification):
   • Không bỏ tất cả trứng vào một giỏ
   • Phân bổ vốn vào 5-10 cổ phiếu khác nhau
   • Phân bổ vào nhiều ngành khác nhau

2. Quy tắc 1% - 2%:
   • Không để thua lỗ trên một vị thế vượt quá 1-2% tổng vốn

3. Cắt lỗ (Stop Loss):
   • Đặt mức cắt lỗ trước khi mua (thường 7-10% giá mua)
   • Tuân thủ kế hoạch cắt lỗ, không cố giữ khi thua

4. Quản lý vốn:
   • Chỉ đầu tư số tiền bạn có thể chấp nhận mất
   • Không vay mượn (margin) khi chưa có kinh nghiệm
   • Dự trữ tiền mặt 20-30% để nắm bắt cơ hội

5. Tâm lý đầu tư:
   • Không để cảm xúc chi phối quyết định
   • Tránh FOMO (sợ bỏ lỡ)
   • Kiên nhẫn chờ đúng thời điểm`,
  },
  {
    title: 'Thuật ngữ thường dùng',
    content: `Một số thuật ngữ phổ biến trong thị trường chứng khoán Việt Nam:

Giá tham chiếu (TC): Giá đóng cửa của ngày giao dịch trước, làm cơ sở tính biên độ dao động.

Trần/Sàn: Giới hạn tăng/giảm trong ngày. HOSE: ±7%; HNX: ±10%; UPCOM: ±15%.

Volume (Khối lượng): Số cổ phiếu được giao dịch trong một phiên.

P/E Ratio: Tỷ lệ giá/lợi nhuận. P/E thấp → cổ phiếu rẻ so với lợi nhuận.

P/B Ratio: Tỷ lệ giá/giá trị sổ sách. P/B < 1 → giao dịch dưới giá trị tài sản.

EPS (Earnings Per Share): Lợi nhuận trên mỗi cổ phiếu.

Cổ tức (Dividend): Phần lợi nhuận công ty chia cho cổ đông.

Blue-chip: Cổ phiếu của các công ty lớn, uy tín, vốn hóa cao (VNM, VIC, FPT, VCB...).

Penny stock: Cổ phiếu có giá rất thấp, thường dưới 5.000 đồng, rủi ro cao.

Bid/Ask: Giá mua tốt nhất (Bid) và giá bán tốt nhất (Ask) tại thời điểm hiện tại.

T+2: Thời gian thanh toán. Cổ phiếu mua ngày T sẽ về tài khoản vào ngày T+2.`,
  },
];

const ICONS: Record<number, React.ReactNode> = {
  0: <BookOpen className="w-5 h-5" />,
  1: <DollarSign className="w-5 h-5" />,
  2: <TrendingUp className="w-5 h-5" />,
  3: <BarChart2 className="w-5 h-5" />,
  4: <Shield className="w-5 h-5" />,
  5: <BookMarked className="w-5 h-5" />,
};

function AccordionItem({
  section,
  index,
  isOpen,
  onToggle,
}: {
  section: GuideSection;
  index: number;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border border-gray-700 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className={`w-full flex items-center gap-4 p-5 text-left transition-colors ${
          isOpen ? 'bg-gray-700/80' : 'bg-gray-800 hover:bg-gray-700/50'
        }`}
      >
        <div className={`p-2 rounded-lg flex-none transition-colors ${isOpen ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
          {ICONS[index] ?? <HelpCircle className="w-5 h-5" />}
        </div>
        <span className={`font-semibold flex-1 text-left ${isOpen ? 'text-white' : 'text-gray-200'}`}>
          {section.title}
        </span>
        <ChevronDown
          className={`w-5 h-5 flex-none transition-transform duration-200 ${isOpen ? 'rotate-180 text-emerald-400' : 'text-gray-500'}`}
        />
      </button>
      {isOpen && (
        <div className="bg-gray-800/50 border-t border-gray-700 p-5">
          <div className="prose prose-invert max-w-none">
            {section.content.split('\n').map((line, i) => {
              if (!line.trim()) return <br key={i} />;
              if (line.startsWith('•') || line.match(/^\d+\./)) {
                return (
                  <p key={i} className="text-gray-300 text-sm leading-relaxed pl-2 py-0.5">
                    {line}
                  </p>
                );
              }
              if (line.endsWith(':') && line.length < 80) {
                return (
                  <p key={i} className="text-white font-semibold mt-4 mb-1 text-sm">
                    {line}
                  </p>
                );
              }
              return (
                <p key={i} className="text-gray-300 text-sm leading-relaxed">
                  {line}
                </p>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function GuidePage() {
  const [sections, setSections] = useState<GuideSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  useEffect(() => {
    fetchGuide().then((data) => {
      setSections(data && data.length > 0 ? data : STATIC_GUIDE);
      setLoading(false);
    });
  }, []);

  const toggle = (i: number) => setOpenIndex((prev) => (prev === i ? null : i));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-400 px-4 py-1.5 rounded-full text-sm font-medium mb-4 border border-blue-500/20">
          <BookOpen className="w-4 h-4" />
          Kiến thức đầu tư
        </div>
        <h1 className="text-3xl font-extrabold text-white mb-2">
          Hướng dẫn đầu tư chứng khoán
        </h1>
        <p className="text-gray-400 max-w-xl mx-auto">
          Từ kiến thức cơ bản đến kỹ năng phân tích — tất cả những gì bạn cần để bắt đầu đầu tư
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar TOC - desktop */}
        <div className="hidden lg:block">
          <div className="sticky top-24 bg-gray-800 border border-gray-700 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Mục lục
            </h3>
            <nav className="space-y-1">
              {sections.map((s, i) => (
                <button
                  key={i}
                  onClick={() => { setOpenIndex(i); }}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                    openIndex === i
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                  }`}
                >
                  <span className={`flex-none w-5 h-5 ${openIndex === i ? 'text-emerald-400' : 'text-gray-600'}`}>
                    {ICONS[i] ?? <HelpCircle className="w-4 h-4" />}
                  </span>
                  <span className="leading-tight">{s.title}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Accordion */}
        <div className="lg:col-span-3 space-y-3">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-gray-800 border border-gray-700 rounded-xl h-16 animate-pulse" />
            ))
          ) : (
            sections.map((section, i) => (
              <AccordionItem
                key={i}
                section={section}
                index={i}
                isOpen={openIndex === i}
                onToggle={() => toggle(i)}
              />
            ))
          )}
        </div>
      </div>

      {/* Footer note */}
      <div className="mt-8 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
        <p className="text-yellow-400 text-sm text-center">
          ⚠️ Thông tin chỉ mang tính giáo dục, không phải tư vấn đầu tư chuyên nghiệp.
          Hãy tham khảo chuyên gia tài chính trước khi đưa ra quyết định đầu tư.
        </p>
      </div>
    </div>
  );
}
