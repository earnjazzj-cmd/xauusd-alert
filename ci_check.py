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
import news
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
    now = datetime.now(ZoneInfo(config.LOCAL_TZ))
    # ดึงข่าวรอบเดียว แล้วใช้ซ้ำทุกที่ (กัน 429)
    try:
        events = news.fetch_events(force=True)
        gold = [e for e in events if news.is_gold_relevant(e)]
        todays = [e for e in gold
                  if (d := news.to_local(news.parse_dt(e))) and d.date() == now.date()]
        print(f"[ci] ✅ ดึงข่าวสำเร็จ: สัปดาห์นี้ {len(gold)} ข่าว | วันนี้ {len(todays)} ข่าว")
        for e in todays:
            d = news.to_local(news.parse_dt(e))
            act = e.get("actual") or "-"
            print(f"   {d.strftime('%H:%M')} {e.get('title')} ({e.get('impact')}) actual={act}")
    except Exception as e:
        print("[ci] ❌ ดึงข่าวไม่สำเร็จ:", e)
        events = None

    state = rt._load_state()
    try:
        rt.check_once(state, events)
    except Exception as e:
        print("[ci] realtime error:", e)
    maybe_brief()

    # อัปเดตหน้าเว็บ Dashboard
    try:
        import gen_dashboard_data
        gen_dashboard_data.build()
    except Exception as e:
        print("[ci] dashboard error:", e)


if __name__ == "__main__":
    main()
