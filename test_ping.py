"""
ทดสอบส่ง LINE จาก cloud — รันผ่านปุ่ม Run workflow ของ Test LINE
ส่งการ์ด Flex ตัวอย่าง 1 ใบ เพื่อดูหน้าตา UI จริง
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import config
import line_notify
import flex

now = datetime.now(ZoneInfo(config.LOCAL_TZ)).strftime("%H:%M")
sample = {
    "title": "ทดสอบระบบ (ตัวอย่าง Core CPI)",
    "country": "USD", "impact": "High",
    "forecast": "0.3%", "previous": "0.2%", "actual": "0.5%",
}
ok = line_notify.push_flex("✅ ทดสอบจาก GitHub Cloud", flex.alert_bubble(sample, now))
if not ok:
    ok = line_notify.push("✅ ทดสอบจาก GitHub Cloud (ส่งการ์ดไม่ได้ ลองข้อความธรรมดา)")
print("ส่ง LINE:", "สำเร็จ" if ok else "ไม่สำเร็จ — เช็ค token/secret")
