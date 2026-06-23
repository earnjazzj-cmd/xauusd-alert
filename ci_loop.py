"""
ตัวรันแบบ "จำตารางข่าว + เร่งเช็คเฉพาะช่วงข่าว" สำหรับ GitHub Actions
แนวคิด (กัน HTTP 429):
  - ช่วงปกติ: แทบไม่ดึงข่าว ใช้ปฏิทินที่จำไว้ (ดึงปฏิทินใหม่นาน ๆ ครั้ง)
  - ใกล้เวลาข่าว (ก่อน 2 นาที ถึงหลัง 15 นาที): ดึงสด + เช็คทุก 60 วิ เพื่อจับ actual ทันที
  - 09:00-09:09 ส่งบรีฟเช้าวันละครั้ง
สถานะกันส่งซ้ำเก็บใน alerted_state.json / last_brief.txt (workflow commit กลับให้)
"""
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import news
import realtime_alert as rt
import morning_brief
import gen_dashboard_data

LOOP_SECONDS = int(os.environ.get("LOOP_SECONDS", "18000"))      # ความยาวรอบ (วิ)
NEAR_BEFORE = float(os.environ.get("NEAR_BEFORE_MIN", "2"))       # เริ่มเร่งก่อนข่าว (นาที)
NEAR_AFTER = float(os.environ.get("NEAR_AFTER_MIN", "15"))        # เร่งต่อหลังข่าว (นาที)
FAST_POLL = int(os.environ.get("FAST_POLL_SEC", "60"))           # ใกล้ข่าว: เช็คทุก (วิ)
IDLE_POLL = int(os.environ.get("IDLE_POLL_SEC", "300"))          # ปกติ: เช็คทุก (วิ)
BRIEF_FLAG = os.path.join(os.path.dirname(__file__), "last_brief.txt")


def _now():
    return datetime.now(ZoneInfo(config.LOCAL_TZ))


def maybe_brief():
    now = _now()
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


def _near_event(events, now):
    """อยู่ในช่วงใกล้ข่าวไหม (ก่อน NEAR_BEFORE ถึงหลัง NEAR_AFTER นาที)"""
    for ev in events:
        if not news.is_gold_relevant(ev):
            continue
        m = news.minutes_to_event(ev, now)   # บวก=ยังไม่ถึง
        if m is not None and -NEAR_AFTER <= m <= NEAR_BEFORE:
            return True
    return False


def _idle_sleep(events, now):
    """ช่วงปกติ: นอนยาวจนใกล้ข่าวถัดไป (แต่ไม่เกิน IDLE_POLL เพื่อให้ตื่นทันบรีฟ 9 โมง)"""
    upcoming = []
    for ev in events:
        if not news.is_gold_relevant(ev):
            continue
        m = news.minutes_to_event(ev, now)
        if m is not None and m > NEAR_BEFORE:
            upcoming.append(m)
    if not upcoming:
        return IDLE_POLL
    secs = int((min(upcoming) - NEAR_BEFORE) * 60)
    return max(60, min(IDLE_POLL, secs))


def main():
    print("[ci_loop] เริ่มทำงาน: จำตารางข่าว + เร่งเช็คเฉพาะช่วงข่าว")
    # --- เช็คตอนเริ่ม: ดึงปฏิทินให้เห็นชัดว่าใช้ได้ไหม ---
    try:
        ev0 = news.fetch_events(force=True)
        gold = [e for e in ev0 if news.is_gold_relevant(e)]
        print(f"[ci_loop] ✅ ดึงปฏิทินสำเร็จ: ทั้งสัปดาห์มี {len(gold)} ข่าว USD High/Medium")
        now0 = _now()
        todays = [e for e in gold
                  if (d := news.to_local(news.parse_dt(e))) and d.date() == now0.date()]
        if todays:
            print(f"[ci_loop] วันนี้มี {len(todays)} ข่าว:")
            for e in todays:
                d = news.to_local(news.parse_dt(e))
                print(f"   - {d.strftime('%H:%M')} {e.get('title')} ({e.get('impact')})")
        else:
            print("[ci_loop] วันนี้ไม่มีข่าว USD High/Medium")
    except Exception as e:
        print("[ci_loop] ❌ ดึงปฏิทินไม่สำเร็จ:", e)
    state = rt._load_state()
    end = time.time() + LOOP_SECONDS

    while time.time() < end:
        now = _now()
        # ดึงปฏิทิน (cache จัดการให้ ไม่ดึงถี่เกิน) เพื่อรู้ว่ามีข่าวใกล้ไหม
        try:
            events = news.fetch_events()
        except Exception as e:
            print(f"[ci_loop] ดึงปฏิทินไม่สำเร็จ: {e}")
            events = []

        near = _near_event(events, now) if events else False

        if near:
            # ใกล้ข่าว/ถึงเวลาประกาศ -> ดึงสด (ข้าม cache) แล้วจับ actual ทันที
            try:
                fresh = news.fetch_events(force=True)
            except Exception as e:
                print(f"[ci_loop] ดึงสดไม่สำเร็จ: {e}")
                fresh = events
            rt.check_once(state, fresh)
        # ช่วงปกติ: ไม่จับข่าว แค่ดูตารางที่จำไว้ (ไม่ดึงเน็ต) แล้วนอนรอ

        maybe_brief()   # ส่งรายการข่าววันนี้ทีเดียวตอน 9 โมง

        # อัปเดตหน้าเว็บ Dashboard (ใช้ cache อยู่แล้ว)
        try:
            gen_dashboard_data.build()
        except Exception as e:
            print("[ci_loop] dashboard error:", e)

        time.sleep(FAST_POLL if near else _idle_sleep(events, now))

    print("[ci_loop] จบรอบ — GitHub จะเปิดรอบใหม่ต่อ")


if __name__ == "__main__":
    main()
