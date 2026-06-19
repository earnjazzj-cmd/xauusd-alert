"""
การตั้งค่าระบบแจ้งเตือนข่าว XAUUSD เข้า LINE
อ่านค่าจาก environment variables (.env)
"""
import os
from pathlib import Path

# โหลด .env แบบง่าย (ไม่ต้องลง python-dotenv ก็ได้)
def _load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env()

# ===== LINE Messaging API =====
# สร้าง LINE Official Account แล้วเอา Channel access token (long-lived) มาใส่
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
# userId ของคุณ (หรือ groupId) ที่จะรับข้อความ -- ดูวิธีหาใน README
LINE_TO = os.environ.get("LINE_TO", "")

# ===== แหล่งข่าว =====
# ForexFactory weekly calendar (JSON) - อัปเดต actual เมื่อข่าวออก
FF_FEED_URL = os.environ.get(
    "FF_FEED_URL",
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
)

# ===== ตัวกรองข่าวที่กระทบทอง XAUUSD =====
# ทองอ่อนไหวกับข่าว USD เป็นหลัก (DXY, ดอกเบี้ย, เงินเฟ้อ, การจ้างงาน)
WATCH_CURRENCIES = [c.strip() for c in os.environ.get("WATCH_CURRENCIES", "USD").split(",")]
# ระดับ impact ที่สนใจ: High, Medium (ตัดข่าวเล็กออก)
WATCH_IMPACTS = [c.strip() for c in os.environ.get("WATCH_IMPACTS", "High,Medium").split(",")]

# คีย์เวิร์ดข่าวสำคัญที่กระทบทองแรงเป็นพิเศษ (ใช้ติดป้าย 🔥)
HIGH_IMPACT_KEYWORDS = [
    "Non-Farm", "Nonfarm", "NFP", "CPI", "PCE", "FOMC", "Federal Funds",
    "Interest Rate", "Fed Chair", "Powell", "Unemployment", "GDP",
    "PPI", "Retail Sales", "ISM",
]

# ===== เขตเวลา =====
# เวลาที่จะแสดงในข้อความ (ของคุณ)
LOCAL_TZ = os.environ.get("LOCAL_TZ", "Asia/Bangkok")

# ===== เรียลไทม์ =====
# ช่วงเวลา (วินาที) ที่ poll หา actual ใหม่
POLL_INTERVAL_SEC = int(os.environ.get("POLL_INTERVAL_SEC", "60"))
# ไฟล์เก็บสถานะว่าแจ้งข่าวไหนไปแล้ว (กันส่งซ้ำ)
STATE_FILE = str(Path(__file__).parent / "alerted_state.json")
