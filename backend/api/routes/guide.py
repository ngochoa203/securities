"""
Trading Guide Route
===================
GET /api/guide – Returns a comprehensive Vietnamese stock trading
                 guide for beginner investors.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/guide", tags=["guide"])

# ---------------------------------------------------------------------------
# Guide content (Vietnamese, detailed)
# ---------------------------------------------------------------------------

_GUIDE = {
    "title":       "Hướng Dẫn Đầu Tư Chứng Khoán Dành Cho Người Mới Bắt Đầu",
    "description": "Tất cả những gì bạn cần biết để bắt đầu hành trình đầu tư chứng khoán tại Việt Nam một cách an toàn và hiệu quả.",
    "sections": [
        {
            "id":    "what-is-stock",
            "title": "Chứng khoán là gì?",
            "icon":  "📈",
            "content": (
                "**Chứng khoán** là các giấy tờ có giá trị tài chính, đại diện cho quyền sở hữu "
                "hoặc quyền đòi nợ đối với một tổ chức phát hành. Có hai loại chứng khoán phổ biến "
                "nhất tại Việt Nam:\n\n"
                "**1. Cổ phiếu (Stock/Share):**\n"
                "Khi bạn mua cổ phiếu của một công ty, bạn trở thành cổ đông – tức là đồng sở hữu "
                "công ty đó. Lợi nhuận đến từ hai nguồn: (a) giá cổ phiếu tăng (lãi vốn) và "
                "(b) cổ tức được chia hàng năm.\n\n"
                "**2. Trái phiếu (Bond):**\n"
                "Là giấy chứng nhận vay nợ. Bạn cho công ty hoặc chính phủ vay tiền và nhận lãi "
                "suất cố định hàng kỳ. Rủi ro thấp hơn cổ phiếu nhưng lợi nhuận cũng thấp hơn.\n\n"
                "**Tại sao nên đầu tư chứng khoán?**\n"
                "- Lợi nhuận tiềm năng cao hơn gửi ngân hàng (trung bình 12–18%/năm tại TTCK VN)\n"
                "- Tính thanh khoản cao – mua bán dễ dàng mỗi ngày\n"
                "- Tham gia vào sự tăng trưởng của nền kinh tế Việt Nam\n"
                "- Bảo vệ tài sản khỏi lạm phát\n\n"
                "**Rủi ro cần biết:**\n"
                "- Giá cổ phiếu có thể giảm dưới giá mua\n"
                "- Không có bảo đảm lợi nhuận như gửi tiết kiệm\n"
                "- Cần kiên nhẫn và học hỏi liên tục"
            ),
        },
        {
            "id":    "open-account",
            "title": "Cách mở tài khoản chứng khoán",
            "icon":  "🏦",
            "content": (
                "Để đầu tư chứng khoán tại Việt Nam, bạn cần mở tài khoản tại một **Công ty "
                "Chứng khoán (CTCK)**. Quy trình rất đơn giản:\n\n"
                "**Bước 1: Chọn công ty chứng khoán phù hợp**\n"
                "Các CTCK uy tín tại Việt Nam:\n"
                "- **SSI** – Công ty chứng khoán lớn nhất, ứng dụng iSSI tiện lợi\n"
                "- **VNDirect** – Công nghệ tốt, phù hợp người mới\n"
                "- **TCBS (Techcombank Securities)** – Miễn phí giao dịch, tích hợp ngân hàng\n"
                "- **VPS** – Phí thấp, khớp lệnh nhanh\n"
                "- **FPTS** – Nghiên cứu chuyên sâu, phù hợp nhà đầu tư có kinh nghiệm\n\n"
                "**Bước 2: Chuẩn bị hồ sơ**\n"
                "- CCCD/CMND còn hiệu lực\n"
                "- Số tài khoản ngân hàng (để nạp/rút tiền)\n"
                "- Số điện thoại và email cá nhân\n\n"
                "**Bước 3: Đăng ký mở tài khoản**\n"
                "- Trực tuyến: Tải app, chụp ảnh CCCD, selfie xác minh (eKYC) → mở tài khoản trong 15 phút\n"
                "- Tại quầy: Mang hồ sơ đến chi nhánh CTCK, ký hợp đồng\n\n"
                "**Bước 4: Nạp tiền và kích hoạt**\n"
                "- Chuyển tiền từ ngân hàng vào tài khoản chứng khoán\n"
                "- Số tiền tối thiểu thường từ 1–5 triệu đồng\n"
                "- Kích hoạt giao dịch trực tuyến\n\n"
                "**Lưu ý quan trọng:**\n"
                "- Mỗi nhà đầu tư chỉ có một mã số nhà đầu tư (investor ID) do VSD cấp\n"
                "- Có thể mở nhiều tài khoản ở nhiều CTCK khác nhau\n"
                "- Kiểm tra phí giao dịch trước khi chọn CTCK (thường 0.1–0.35%/lệnh)"
            ),
        },
        {
            "id":    "how-to-trade",
            "title": "Cách đặt lệnh mua/bán",
            "icon":  "💹",
            "content": (
                "Thị trường chứng khoán Việt Nam giao dịch từ **Thứ 2 đến Thứ 6** "
                "(trừ ngày lễ, Tết):\n"
                "- **9:00–11:30**: Phiên giao dịch sáng (khớp lệnh liên tục)\n"
                "- **13:00–14:45**: Phiên giao dịch chiều (khớp lệnh liên tục)\n"
                "- **14:45–15:00**: Phiên ATC (khớp lệnh định kỳ đóng cửa)\n\n"
                "**Các loại lệnh phổ biến:**\n\n"
                "**1. Lệnh LO (Limit Order – Lệnh giới hạn):**\n"
                "Đặt mua/bán ở một mức giá xác định. Lệnh chỉ khớp khi thị trường đạt đúng "
                "mức giá đó. Phù hợp khi bạn có mục tiêu giá cụ thể.\n\n"
                "**2. Lệnh MP (Market Price – Lệnh thị trường):**\n"
                "Mua/bán ngay lập tức theo giá tốt nhất hiện có. Khớp lệnh nhanh nhưng có "
                "thể không được giá như kỳ vọng.\n\n"
                "**3. Lệnh ATO/ATC:**\n"
                "- ATO (At The Opening): Khớp lệnh mở cửa lúc 9:00\n"
                "- ATC (At The Close): Khớp lệnh đóng cửa lúc 14:45–15:00\n\n"
                "**Quy trình đặt lệnh mua:**\n"
                "1. Chọn mã cổ phiếu (VD: FPT)\n"
                "2. Chọn Mua (Buy)\n"
                "3. Nhập số lượng (tối thiểu 10 cổ phiếu tại HOSE, 1 cổ tại HNX)\n"
                "4. Nhập giá mong muốn (lệnh LO) hoặc chọn MP\n"
                "5. Xác nhận và đặt lệnh\n\n"
                "**Biên độ giá và giới hạn dao động:**\n"
                "- HOSE: ±7% so với giá tham chiếu\n"
                "- HNX: ±10% so với giá tham chiếu\n"
                "- UPCoM: ±15% so với giá tham chiếu\n\n"
                "**Thanh toán (T+2):**\n"
                "Sau khi mua, tiền được trừ ngay nhưng cổ phiếu về tài khoản sau 2 ngày "
                "làm việc (T+2). Bán xong, tiền về sau T+2."
            ),
        },
        {
            "id":    "technical-analysis",
            "title": "Phân tích kỹ thuật cơ bản",
            "icon":  "📊",
            "content": (
                "**Phân tích kỹ thuật (Technical Analysis)** là phương pháp nghiên cứu biểu đồ "
                "giá và khối lượng giao dịch để dự báo xu hướng giá trong tương lai.\n\n"
                "**1. Đường xu hướng (Trend Lines):**\n"
                "- **Xu hướng tăng (Uptrend)**: Giá tạo các đỉnh cao hơn và đáy cao hơn. "
                "Nên mua khi giá pullback về đường xu hướng.\n"
                "- **Xu hướng giảm (Downtrend)**: Giá tạo các đỉnh thấp hơn và đáy thấp hơn. "
                "Tránh mua, chờ tín hiệu đảo chiều.\n\n"
                "**2. Đường trung bình động (Moving Averages):**\n"
                "- **SMA20** (20 ngày): Phản ánh xu hướng ngắn hạn\n"
                "- **SMA50** (50 ngày): Phản ánh xu hướng trung hạn\n"
                "- **SMA200** (200 ngày): Phản ánh xu hướng dài hạn\n"
                "- **Golden Cross**: SMA20 cắt lên SMA50 → Tín hiệu tăng mạnh\n"
                "- **Death Cross**: SMA20 cắt xuống SMA50 → Tín hiệu giảm\n\n"
                "**3. RSI (Relative Strength Index):**\n"
                "Chỉ số dao động từ 0–100:\n"
                "- RSI < 30: Cổ phiếu bị bán quá mức (**quá bán**) → Cơ hội mua\n"
                "- RSI > 70: Cổ phiếu bị mua quá mức (**quá mua**) → Cân nhắc bán\n"
                "- RSI 40–60: Trung tính, chờ tín hiệu rõ hơn\n\n"
                "**4. MACD (Moving Average Convergence/Divergence):**\n"
                "- Khi đường MACD cắt lên đường Signal → Tín hiệu mua\n"
                "- Khi đường MACD cắt xuống đường Signal → Tín hiệu bán\n"
                "- Biểu đồ histogram dương và tăng → Đà tăng mạnh\n\n"
                "**5. Bollinger Bands:**\n"
                "- Gồm 3 dải: Upper (trên), Middle (trung bình), Lower (dưới)\n"
                "- Giá chạm dải dưới → Có thể quá bán, cơ hội mua\n"
                "- Giá chạm dải trên → Có thể quá mua, cân nhắc bán\n"
                "- Dải thắt lại → Sắp có biến động lớn\n\n"
                "**6. Khối lượng giao dịch (Volume):**\n"
                "- Giá tăng + khối lượng tăng → Xu hướng tăng mạnh, đáng tin cậy\n"
                "- Giá tăng + khối lượng giảm → Xu hướng tăng yếu, cẩn thận\n"
                "- Khối lượng đột biến → Tín hiệu đảo chiều có thể xảy ra"
            ),
        },
        {
            "id":    "risk-management",
            "title": "Quản lý rủi ro",
            "icon":  "🛡️",
            "content": (
                "Quản lý rủi ro là kỹ năng quan trọng nhất của nhà đầu tư thành công. "
                "Dù phân tích tốt đến đâu, thị trường vẫn có thể biến động bất ngờ.\n\n"
                "**Nguyên tắc vàng trong đầu tư:**\n\n"
                "**1. Đa dạng hóa danh mục (Diversification):**\n"
                "- Không bỏ tất cả trứng vào một giỏ\n"
                "- Mỗi cổ phiếu không vượt quá 20% tổng danh mục\n"
                "- Đầu tư vào nhiều ngành khác nhau: ngân hàng, bất động sản, công nghệ, tiêu dùng\n"
                "- Kết hợp cổ phiếu tăng trưởng và cổ phiếu cổ tức\n\n"
                "**2. Quy tắc cắt lỗ (Stop Loss):**\n"
                "- Đặt ngưỡng cắt lỗ từ 7–10% dưới giá mua\n"
                "- Ví dụ: Mua FPT giá 100,000 → Cắt lỗ tại 90,000–93,000\n"
                "- Tuyệt đối tuân thủ, không để cảm xúc chi phối\n"
                "- 'Đừng bao giờ để khoản lỗ nhỏ thành lỗ lớn'\n\n"
                "**3. Tỷ lệ Risk/Reward:**\n"
                "- Chỉ vào lệnh khi tỷ lệ lợi nhuận kỳ vọng ít nhất gấp 2 lần rủi ro\n"
                "- Ví dụ: Cắt lỗ -7% → Mục tiêu lợi nhuận tối thiểu +14%\n\n"
                "**4. Không dùng đòn bẩy khi mới bắt đầu:**\n"
                "- Tuyệt đối không vay margin khi chưa có kinh nghiệm\n"
                "- Margin có thể khuếch đại lỗ lên nhiều lần\n"
                "- Chỉ dùng margin khi đã có ít nhất 1–2 năm kinh nghiệm\n\n"
                "**5. Phân bổ vốn hợp lý:**\n"
                "- Chỉ đầu tư tiền nhàn rỗi, không dùng tiền sinh hoạt\n"
                "- Quy tắc 50/30/20: 50% chi tiêu cần thiết, 30% chi tiêu cá nhân, 20% tiết kiệm/đầu tư\n"
                "- Giữ ít nhất 20–30% danh mục là tiền mặt để tận dụng cơ hội\n\n"
                "**6. Kiểm soát cảm xúc:**\n"
                "- Tránh FOMO (Fear Of Missing Out) – mua khi giá đã tăng mạnh\n"
                "- Tránh Panic Sell – bán hoảng loạn khi giá giảm\n"
                "- Lập kế hoạch đầu tư và tuân thủ nghiêm ngặt\n"
                "- Nhật ký đầu tư: Ghi lại lý do mua/bán để rút kinh nghiệm"
            ),
        },
        {
            "id":    "glossary",
            "title": "Thuật ngữ thường dùng",
            "icon":  "📚",
            "content": (
                "Danh sách các thuật ngữ quan trọng trong thị trường chứng khoán Việt Nam:\n\n"
                "**A–C:**\n"
                "- **ATC** (At The Close): Lệnh khớp tại giá đóng cửa\n"
                "- **ATO** (At The Opening): Lệnh khớp tại giá mở cửa\n"
                "- **Bear Market (Thị trường gấu)**: Thị trường giảm kéo dài >20%\n"
                "- **Blue-chip**: Cổ phiếu của công ty lớn, uy tín, vốn hóa cao\n"
                "- **Bull Market (Thị trường bò)**: Thị trường tăng kéo dài >20%\n"
                "- **Cổ tức (Dividend)**: Phần lợi nhuận chia cho cổ đông\n"
                "- **Cổ phần (Share)**: Đơn vị sở hữu nhỏ nhất của một công ty\n\n"
                "**D–G:**\n"
                "- **EPS** (Earnings Per Share): Lợi nhuận trên mỗi cổ phiếu\n"
                "- **Giá tham chiếu**: Giá đóng cửa phiên trước, làm cơ sở tính biên độ\n"
                "- **Giá trần/sàn**: Mức giá cao/thấp nhất được phép giao dịch trong ngày\n\n"
                "**H–M:**\n"
                "- **HNX**: Sàn giao dịch chứng khoán Hà Nội\n"
                "- **HOSE**: Sàn giao dịch chứng khoán TP.HCM\n"
                "- **IPO** (Initial Public Offering): Phát hành cổ phiếu lần đầu ra công chúng\n"
                "- **Khớp lệnh liên tục**: Phương thức khớp lệnh ngay khi có lệnh đối ứng\n"
                "- **Lệnh MP (Market Price)**: Lệnh mua/bán theo giá thị trường tốt nhất\n"
                "- **Lệnh LO (Limit Order)**: Lệnh mua/bán với giá giới hạn xác định\n"
                "- **Margin (Ký quỹ)**: Vay tiền từ CTCK để mua cổ phiếu với đòn bẩy\n"
                "- **Market Cap (Vốn hóa thị trường)**: Giá CP × Số CP đang lưu hành\n\n"
                "**N–P:**\n"
                "- **NAV** (Net Asset Value): Giá trị tài sản ròng\n"
                "- **P/E** (Price to Earnings): Tỷ số giá trên thu nhập; P/E thấp thường rẻ hơn\n"
                "- **P/B** (Price to Book): Tỷ số giá trên giá trị sổ sách\n"
                "- **Phiên ATC**: Phiên khớp lệnh định kỳ cuối ngày (14:45–15:00)\n\n"
                "**R–V:**\n"
                "- **ROE** (Return on Equity): Tỷ suất lợi nhuận trên vốn chủ sở hữu\n"
                "- **Room nước ngoài**: Tỷ lệ sở hữu tối đa của nhà đầu tư nước ngoài\n"
                "- **T+2**: Thời gian thanh toán 2 ngày làm việc sau giao dịch\n"
                "- **Thanh khoản**: Khả năng mua/bán nhanh không ảnh hưởng giá\n"
                "- **UPCoM**: Sàn giao dịch cổ phiếu chưa niêm yết\n"
                "- **VN-Index**: Chỉ số thị trường chứng khoán sàn HOSE\n"
                "- **VSD**: Trung tâm Lưu ký Chứng khoán Việt Nam\n"
                "- **Volume (Khối lượng)**: Số cổ phiếu được giao dịch trong một kỳ"
            ),
        },
        {
            "id":    "investment-strategies",
            "title": "Chiến lược đầu tư phổ biến",
            "icon":  "🎯",
            "content": (
                "**1. Đầu tư giá trị (Value Investing):**\n"
                "Tìm kiếm cổ phiếu đang bị định giá thấp hơn giá trị thực. "
                "Tư tưởng của Warren Buffett – mua cổ phiếu tốt khi giá rẻ và nắm giữ dài hạn.\n"
                "- Tiêu chí: P/E thấp, P/B < 1, ROE > 15%, nợ vay thấp\n"
                "- Phù hợp: Nhà đầu tư kiên nhẫn, thời gian nắm giữ 3–10 năm\n\n"
                "**2. Đầu tư tăng trưởng (Growth Investing):**\n"
                "Tập trung vào các công ty có doanh thu và lợi nhuận tăng trưởng mạnh.\n"
                "- Tiêu chí: Doanh thu tăng >20%/năm, thị phần mở rộng, sản phẩm sáng tạo\n"
                "- Ví dụ tại VN: FPT, MWG, VHM giai đoạn đầu\n\n"
                "**3. Đầu tư cổ tức (Dividend Investing):**\n"
                "Mua cổ phiếu trả cổ tức đều đặn, tạo dòng thu nhập thụ động.\n"
                "- Tiêu chí: Cổ tức yield > 5%, lịch sử chia cổ tức ổn định\n"
                "- Ví dụ tại VN: VNM, GAS, SAB\n\n"
                "**4. DCA (Dollar Cost Averaging – Đầu tư định kỳ):**\n"
                "Mua đều đặn một khoản cố định mỗi tháng bất kể giá thị trường.\n"
                "- Ưu điểm: Giảm rủi ro mua đỉnh, phù hợp người bận rộn\n"
                "- Thực hiện: Mua 1–2 triệu VND/tháng vào các cổ phiếu blue-chip\n\n"
                "**5. Giao dịch theo xu hướng (Trend Following):**\n"
                "Mua khi xu hướng tăng xác nhận, bán khi đảo chiều.\n"
                "- Công cụ: Đường MA, MACD, Volume\n"
                "- Phù hợp: Người theo dõi thị trường hàng ngày"
            ),
        },
        {
            "id":    "tax-and-law",
            "title": "Thuế và pháp lý",
            "icon":  "⚖️",
            "content": (
                "**Thuế thu nhập cá nhân từ chứng khoán:**\n\n"
                "**1. Thuế từ chuyển nhượng chứng khoán:**\n"
                "- Mức thuế: **0.1%** trên giá chuyển nhượng (không phụ thuộc lãi/lỗ)\n"
                "- Khấu trừ tự động tại CTCK khi bán\n"
                "- Ví dụ: Bán 1,000 cổ FPT giá 100,000 = 100,000,000 đồng "
                "→ Thuế = 100,000 đồng\n\n"
                "**2. Thuế từ cổ tức tiền mặt:**\n"
                "- Mức thuế: **5%** trên số cổ tức nhận được\n"
                "- Khấu trừ tự động tại nguồn khi công ty chia cổ tức\n\n"
                "**3. Cổ tức bằng cổ phiếu:**\n"
                "- Không phải nộp thuế ngay khi nhận\n"
                "- Chỉ nộp thuế 0.1% khi bán những cổ phiếu thưởng đó\n\n"
                "**Quyền lợi của cổ đông:**\n"
                "- Quyền biểu quyết tại Đại hội cổ đông (ĐHCĐ)\n"
                "- Quyền nhận cổ tức\n"
                "- Quyền mua cổ phiếu phát hành thêm (quyền mua ưu đãi)\n"
                "- Quyền được thông tin minh bạch từ công ty niêm yết\n\n"
                "**Bảo vệ nhà đầu tư:**\n"
                "- Ủy ban Chứng khoán Nhà nước (SSC) giám sát thị trường\n"
                "- Tiền và chứng khoán được lưu ký tách biệt tại VSD\n"
                "- Quỹ bảo vệ nhà đầu tư tại các CTCK\n"
                "- Đường dây hỗ trợ nhà đầu tư: 1900 545 469"
            ),
        },
    ],
    "quick_tips": [
        "Luôn nghiên cứu kỹ trước khi mua – đọc báo cáo tài chính hàng quý",
        "Không đầu tư theo tin đồn hoặc khuyến nghị từ mạng xã hội thiếu căn cứ",
        "Bắt đầu với vốn nhỏ để học và tích lũy kinh nghiệm thực tế",
        "Kiên nhẫn là đức tính quan trọng nhất – thị trường cần thời gian",
        "Theo dõi vĩ mô: lãi suất, lạm phát, GDP ảnh hưởng lớn đến TTCK",
        "Đọc báo cáo thường niên và BCTC của các công ty trong danh mục",
        "Tham gia các cộng đồng nhà đầu tư uy tín để học hỏi kinh nghiệm",
        "Không để cảm xúc chi phối quyết định đầu tư – tuân thủ kế hoạch",
    ],
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", summary="Vietnamese stock trading guide for beginners")
async def get_guide() -> dict:
    """
    Returns a comprehensive Vietnamese language trading guide covering:
    - What stocks are
    - How to open a brokerage account
    - How to place buy/sell orders
    - Basic technical analysis
    - Risk management principles
    - Common terminology glossary
    - Investment strategies
    - Tax and legal information
    """
    return _GUIDE
