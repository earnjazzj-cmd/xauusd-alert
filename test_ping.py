"""
ทดสอบส่ง LINE จาก cloud — รันผ่านปุ่ม Run workflow ของ Test LINE
ส่งข้อความทดสอบ 1 ข้อความเข้า LINE
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import config
import line_notify

now = datetime.now(ZoneInfo(config.LOCAL_TZ)).strftime("%d/%m/%Y %H:%M:%S")
ok = line_notify.push(f"✅ ทดสอบจาก GitHub Cloud สำเร็จ!\nระบบแจ้งเตือน XAUUSD พร้อมทำงาน\nเวลา {now} (ไทย)")
print("ส่ง LINE:", "สำเร็จ" if ok else "ไม่สำเร็จ — เช็ค token/secret")
