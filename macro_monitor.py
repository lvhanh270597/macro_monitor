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
    url = (
        "https://treasury.gov"
        "v1/accounting/dts/operating_cash_balance"
        "?filter=account_type:eq:Treasury General Account (TGA) Closing Balance"
        "&sort=-record_date&page[size]=5"
    )
    resp = requests.get(url, timeout=15).json()
    records = resp.get("data", [])
    if not records:
        return None, None, None
    
    latest_date = records[0]["record_date"]
    latest_bal = float(records[0]["open_today_bal"]) # Triệu USD
    prev_5d_bal = float(records[-1]["open_today_bal"])
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
    
    msg = (
        f"{status_header}\n"
        f"📅 Dữ liệu ngày: `{tga_date}`\n\n"
        f"• *Số dư TGA:* `${tga_bal/1000:,.2f} tỷ USD` (Thay đổi 5 phiên: `{tga_diff/1000:+.2f}B`)\n"
        f"• *Lợi suất US30Y:* `{us30y}%`\n\n"
        f"{alert_text}"
    )
    send_telegram_alert(msg)

if __name__ == "__main__":
    main()
