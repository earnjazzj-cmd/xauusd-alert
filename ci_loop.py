"""
ตัวรันแบบ "ค้างวนเช็ค" สำหรับ GitHub Actions
แต่ละรอบ workflow จะรันไฟล์นี้ค้างไว้ ~28 นาที วนเช็คทุก ~60 วินาที
แล้ว GitHub เปิดรอบใหม่ต่อ -> ได้ความเร็ว ~1 นาที แบบต่อเนื่อง โดยปิดคอมได้

- เช็ค actual ใหม่ -> เด้ง LINE (เร็วระดับ ~1 นาที)
- ช่วง 09:00-09:09 ส่งบรีฟเช้าวันละครั้ง
สถานะกันส่งซ้ำเก็บใน alerted_state.json / last_brief.txt (workflow commit กลับให้)
"""
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import realtime_alert as rt
import morning_brief

LOOP_SECONDS = int(os.environ.get("LOOP_SECONDS", "1700"))   # ~28 นาที/รอบ
POLL_SEC = int(os.environ.get("LOOP_POLL_SEC", "60"))         # เช็คทุก 60 วิ
BRIEF_FLAG = os.path.join(os.path.dirname(__file__), "last_brief.txt")


def maybe_brief():
    now = datetime.now(ZoneInfo(config.LOCAL_TZ))
    if not (now.hour == 9 and now.minute < 10):
        return
    today = now.date().isoformat()
    if os.path.exists(BRIEF_FLAG) and open(BRIEF_FLAG).read().strip() == today:
        return
    try:
        morning_brief.main()
        with open(BRIEF_FLAG, "w") as f:
            f.write(today)
        print("[ci_loop] ส่งบรีฟเช้าแล้ว", today)
    except Exception as e:
        print("[ci_loop] บรีฟเช้า error:", e)


def main():
    print(f"[ci_loop] เริ่มรอบ ~{LOOP_SECONDS}s เช็คทุก {POLL_SEC}s")
    state = rt._load_state()
    end = time.time() + LOOP_SECONDS
    while time.time() < end:
        try:
            rt.check_once(state)
        except Exception as e:
            print("[ci_loop] realtime error:", e)
        maybe_brief()
        time.sleep(POLL_SEC)
    print("[ci_loop] จบรอบ — GitHub จะเปิดรอบใหม่ต่อ")


if __name__ == "__main__":
    main()
