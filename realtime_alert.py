"""
แจ้งเตือนเรียลไทม์: poll feed ทุก ๆ POLL_INTERVAL_SEC วินาที
เมื่อข่าวที่กระทบทองมีค่า actual ออกใหม่ -> ส่งเข้า LINE ทันที
กันส่งซ้ำด้วยไฟล์ state

รันค้างไว้:  python realtime_alert.py
(แนะนำให้รันเป็น service / pm2 / systemd / nohup)
"""
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import config
import news
import line_notify


def _load_state():
    if os.path.exists(config.STATE_FILE):
        try:
            return set(json.load(open(config.STATE_FILE, encoding="utf-8")))
        except Exception:
            return set()
    return set()


def _save_state(state):
    json.dump(sorted(state), open(config.STATE_FILE, "w", encoding="utf-8"))


def _event_key(ev):
    """คีย์เฉพาะของ event เพื่อกันแจ้งซ้ำ"""
    return f"{ev.get('date')}|{ev.get('title')}|{ev.get('country')}"


def _surprise(ev):
    """เทียบ actual กับ forecast เพื่อบอกเซอร์ไพรส์ + ทิศทางต่อทอง"""
    a = news._num(ev.get("actual"))
    f = news._num(ev.get("forecast"))
    if a is None or f is None:
        return ""
    if abs(a - f) < 1e-9:
        return "ตรงคาด → ผลต่อทองจำกัด"
    if a > f:
        return "สูงกว่าคาด → USD แข็ง มักกดทองลง 🔻"
    return "ต่ำกว่าคาด → USD อ่อน มักหนุนทองขึ้น 🔺"


def check_once(state):
    """ตรวจรอบเดียว: หา actual ใหม่แล้วแจ้ง"""
    try:
        events = news.fetch_events()
    except Exception as e:
        print(f"[poll] ดึงข่าวไม่สำเร็จ: {e}")
        return

    for ev in events:
        if not news.is_gold_relevant(ev):
            continue
        actual = ev.get("actual")
        if not actual:  # ยังไม่ออก
            continue
        key = _event_key(ev)
        if key in state:  # แจ้งไปแล้ว
            continue

        ldt = news.to_local(news.parse_dt(ev))
        t = ldt.strftime("%H:%M") if ldt else "-"
        icon = news.impact_icon(ev)
        alt = f"⚡ {ev['title']} ออกแล้ว: {actual} ({_surprise(ev)})"
        print(alt, "\n")
        # ส่งเป็นการ์ด Flex (สวย) ถ้าพลาดค่อย fallback เป็นข้อความธรรมดา
        sent = False
        try:
            import flex
            sent = line_notify.push_flex(alt, flex.alert_bubble(ev, t))
        except Exception as e:
            print("[realtime] flex error:", e)
        if not sent:
            sent = line_notify.push(alt)
        if sent:
            state.add(key)
            _save_state(state)


def _next_interval():
    """ใกล้ข่าว ±10 นาที เช็คทุก 10 วิ (เด้งแทบทันที), นอกนั้นเช็คตามปกติ"""
    try:
        events = news.fetch_events()
    except Exception:
        return config.POLL_INTERVAL_SEC
    now = datetime.now(ZoneInfo(config.LOCAL_TZ))
    for ev in events:
        if not news.is_gold_relevant(ev):
            continue
        m = news.minutes_to_event(ev, now)
        if m is not None and -10 <= m <= 10:
            return 10
    return config.POLL_INTERVAL_SEC


def main():
    print("[realtime] เริ่มเฝ้าข่าว XAUUSD | เช็คเร็วขึ้นช่วงใกล้ข่าว")
    state = _load_state()
    while True:
        check_once(state)
        time.sleep(_next_interval())


if __name__ == "__main__":
    main()
