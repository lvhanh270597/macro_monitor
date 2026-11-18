import requests
import yfinance as yf
from datetime import datetime

# Cấu hình Telegram Bot của bạn
TELEGRAM_BOT_TOKEN = "8701670197:AAHBSXDGU-zfwL9UTt6vyfJThRxgEviYQRw"
TELEGRAM_CHAT_ID = "-5582192881"

# Các ngưỡng cảnh báo theo Báo cáo Chiến lược 2026
TGA_BULLISH_THRESHOLD = 300_000  # Đơn vị trong API là triệu USD (300.000 triệu = 300 tỷ USD)
US30Y_CRISIS_THRESHOLD = 5.50    # Ngưỡng 5.5%

def get_tga_data():
    base_url = "https://treasury.gov"
    params = {
        "filter": "account_type:eq:Treasury General Account (TGA) Closing Balance",
        "sort": "-record_date",
        "page[size]": 5
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    resp = requests.get(base_url, params=params, headers=headers, timeout=15)
    
    # In ra status và 200 ký tự đầu tiên nếu API không trả về JSON để dễ debug
    if resp.status_code != 200 or not resp.text.strip():
        print(f"Lỗi API TGA - Status: {resp.status_code}, Nội dung: {resp.text[:200]}")
        return None, None, None

    try:
        records = resp.json().get("data", [])
    except ValueError:
        print(f"Phản hồi không phải JSON: {resp.text[:200]}")
        return None, None, None

    if not records:
        return None, None, None
    
    # Chú ý: records[0] là bản ghi mới nhất
    latest_record = records[0]
    oldest_record = records[-1]
    
    latest_date = latest_record["record_date"]
    latest_bal = float(latest_record["open_today_bal"])
    prev_5d_bal = float(oldest_record["open_today_bal"])
    diff_5d = latest_bal - prev_5d_bal
    
    return latest_date, latest_bal, diff_5d


def get_us30y_yield():
    # ^TYX trên Yahoo Finance đại diện cho lợi suất trái phiếu Mỹ 30 năm
    ticker = yf.Ticker("^TYX")
    hist = ticker.history(period="2d")
    if hist.empty:
        return None
    return round(float(hist["Close"].iloc[-1]), 3)

def send_telegram_alert(message):
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

def main():
    tga_date, tga_bal, tga_diff = get_tga_data()
    us30y = get_us30y_yield()
    
    alerts = []
    if tga_bal is not None:
        if tga_bal < TGA_BULLISH_THRESHOLD:
            alerts.append(f"🟢 *BULLISH TGA:* Số dư TGA đã giảm dưới 300 tỷ USD (${tga_bal/1000:,.2f}B).")
        elif tga_diff <= -50_000:
            alerts.append(f"🟡 *BƠM THANH KHOẢN:* TGA giảm mạnh ${abs(tga_diff)/1000:,.2f}B trong 5 phiên qua.")
            
    if us30y is not None and us30y >= US30Y_CRISIS_THRESHOLD:
        alerts.append(f"🔴 *CẢNH BÁO KỊCH BẢN 2:* Lợi suất US30Y chạm *{us30y}%* (vượt ngưỡng 5.5%).")

    # Luôn gửi báo cáo định kỳ hoặc chỉ gửi khi có cảnh báo (bỏ điều kiện if alerts nếu muốn nhận mỗi ngày)
    status_header = "🚨 *CẢNH BÁO VĨ MÔ QUAN TRỌNG*" if alerts else "📊 *BÁO CÁO THANH KHOẢN KHO BẠC MỸ*"
    alert_text = "\n".join(alerts) if alerts else "✅ Các chỉ số chưa chạm ngưỡng kích hoạt cực đoan."

    tga_date_text = tga_date if tga_date is not None else "Không có dữ liệu"
    tga_bal_text = (
        f"${tga_bal/1000:,.2f} tỷ USD"
        if tga_bal is not None
        else "Không có dữ liệu"
    )
    tga_diff_text = (
        f"{tga_diff/1000:+.2f}B"
        if tga_diff is not None
        else "Không có dữ liệu"
    )
    us30y_text = f"{us30y}%" if us30y is not None else "Không có dữ liệu"
    
    msg = (
        f"{status_header}\n"
        f"📅 Dữ liệu ngày: `{tga_date_text}`\n\n"
        f"• *Số dư TGA:* `{tga_bal_text}` (Thay đổi 5 phiên: `{tga_diff_text}`)\n"
        f"• *Lợi suất US30Y:* `{us30y_text}`\n\n"
        f"{alert_text}"
    )
    send_telegram_alert(msg)

if __name__ == "__main__":
    main()
