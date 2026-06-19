"""
ตัวรันรวมสำหรับเซิร์ฟเวอร์ (Oracle Free VM ฯลฯ)
ทำงาน 2 อย่างในโปรเซสเดียว รันค้างตลอด 24 ชม.:
  1) เฝ้าข่าวเรียลไทม์ -> เด้ง LINE เมื่อ actual ออก (เช็คถี่ช่วงใกล้ข่าว)
  2) บรีฟเช้าอัตโนมัติเวลา 09:00 (ตาม LOCAL_TZ) วันละครั้ง

รัน:  python3 run_all.py
(บน VM ใช้ systemd ให้รันค้าง+รีสตาร์ตเอง — ดู deploy_setup.sh)
"""
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import news
import realtime_alert as rt
import morning_brief

BRIEF_HOUR = int(__import__("os").environ.get("BRIEF_HOUR", "9"))
BRIEF_MINUTE = int(__import__("os").environ.get("BRIEF_MINUTE", "0"))


def _now():
    return datetime.now(ZoneInfo(config.LOCAL_TZ))


def main():
    print(f"[run_all] เริ่มทำงาน | บรีฟเช้า {BRIEF_HOUR:02d}:{BRIEF_MINUTE:02d} | เฝ้าเรียลไทม์")
    state = rt._load_state()
    last_brief_date = None

    while True:
        now = _now()

        # --- บรีฟเช้า: ส่งครั้งเดียวต่อวัน เมื่อถึงเวลา ---
        if (now.hour == BRIEF_HOUR and now.minute >= BRIEF_MINUTE
                and last_brief_date != now.date()):
            try:
                morning_brief.main()
                last_brief_date = now.date()
                print(f"[run_all] ส่งบรีฟเช้าแล้ว {now.date()}")
            except Exception as e:
                print(f"[run_all] บรีฟเช้า error: {e}")

        # --- เรียลไทม์: เช็ค actual ใหม่ ---
        try:
            rt.check_once(state)
        except Exception as e:
            print(f"[run_all] realtime error: {e}")

        time.sleep(rt._next_interval())


if __name__ == "__main__":
    main()
