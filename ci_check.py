"""
ตัวรันสำหรับ GitHub Actions (รันครั้งเดียวจบ ทุก ๆ 5 นาที)
- เช็ค actual ใหม่ -> เด้ง LINE
- ถ้าอยู่ในช่วง 09:00-09:09 และยังไม่ส่งบรีฟวันนี้ -> ส่งบรีฟเช้า
สถานะ (กันส่งซ้ำ) เก็บในไฟล์ alerted_state.json และ last_brief.txt
ซึ่ง workflow จะ commit กลับ repo ให้อัตโนมัติ
"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import realtime_alert as rt
import morning_brief

BRIEF_FLAG = os.path.join(os.path.dirname(__file__), "last_brief.txt")


def maybe_brief():
    now = datetime.now(ZoneInfo(config.LOCAL_TZ))
    # ส่งบรีฟช่วง 09:00-09:09 (มี 2 รอบให้โอกาส) วันละครั้ง
    if not (now.hour == 9 and now.minute < 10):
        return
    today = now.date().isoformat()
    if os.path.exists(BRIEF_FLAG) and open(BRIEF_FLAG).read().strip() == today:
        return
    try:
        morning_brief.main()
        with open(BRIEF_FLAG, "w") as f:
            f.write(today)
        print("[ci] ส่งบรีฟเช้าแล้ว", today)
    except Exception as e:
        print("[ci] บรีฟเช้า error:", e)


def main():
    state = rt._load_state()
    try:
        rt.check_once(state)
    except Exception as e:
        print("[ci] realtime error:", e)
    maybe_brief()


if __name__ == "__main__":
    main()
