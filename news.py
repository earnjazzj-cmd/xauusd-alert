"""
ดึงและกรองข่าวจาก ForexFactory weekly calendar (JSON)
โครงสร้างแต่ละ event:
  {
    "title": "Core CPI m/m",
    "country": "USD",
    "date": "2026-06-18T08:30:00-04:00",   # ISO 8601 พร้อม offset
    "impact": "High",                        # High | Medium | Low | Holiday
    "forecast": "0.3%",
    "previous": "0.2%",
    "actual": ""                             # ว่างถ้ายังไม่ออก, มีค่าเมื่อออกแล้ว
  }
"""
import json
import os
import time
import urllib.request
from datetime import datetime, date
from zoneinfo import ZoneInfo
import config

# ===== cache: ดึง feed ครั้งเดียวแล้วใช้ซ้ำ กัน HTTP 429 (Too Many Requests) =====
_CACHE = {"t": 0.0, "data": None}
_CACHE_TTL = int(os.environ.get("FEED_CACHE_TTL", "1800"))   # จำตารางข่าวได้นาน 30 นาที (ลดการดึง)

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _http_get(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_events(force=False):
    """
    ดึง event ทั้งสัปดาห์จาก feed (มี cache + ลองใหม่เมื่อโดน 429)
    คืน cache เดิมถ้ายังไม่หมดอายุ -> ลดจำนวน request ลงมาก
    """
    now = time.time()
    if not force and _CACHE["data"] is not None and (now - _CACHE["t"]) < _CACHE_TTL:
        return _CACHE["data"]

    last_err = None
    for attempt in range(3):
        try:
            data = _http_get(config.FF_FEED_URL)
            _CACHE["data"] = data
            _CACHE["t"] = time.time()
            return data
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429:
                time.sleep(20 * (attempt + 1))   # โดน rate limit -> หน่วงแล้วลองใหม่
                continue
            raise
        except Exception as e:
            last_err = e
            time.sleep(5)
    # ถ้ายังล้มเหลว แต่มี cache เก่าอยู่ ใช้ของเก่าไปก่อน (ดีกว่าไม่มีเลย)
    if _CACHE["data"] is not None:
        return _CACHE["data"]
    raise last_err


def parse_dt(ev):
    """แปลง field date เป็น datetime (timezone-aware)"""
    try:
        return datetime.fromisoformat(ev["date"])
    except Exception:
        return None


def to_local(dt):
    """แปลงเป็นเขตเวลาท้องถิ่นของผู้ใช้"""
    if dt is None:
        return None
    return dt.astimezone(ZoneInfo(config.LOCAL_TZ))


def is_gold_relevant(ev):
    """กรองเฉพาะข่าวที่กระทบทอง: สกุลเงิน + ระดับ impact ที่สนใจ"""
    if ev.get("country") not in config.WATCH_CURRENCIES:
        return False
    if ev.get("impact") not in config.WATCH_IMPACTS:
        return False
    return True


def is_top_tier(ev):
    """ข่าวแรงพิเศษ (NFP/CPI/FOMC ...) -> ติดป้าย 🔥"""
    title = ev.get("title", "")
    return any(kw.lower() in title.lower() for kw in config.HIGH_IMPACT_KEYWORDS)


def impact_icon(ev):
    imp = ev.get("impact", "")
    if is_top_tier(ev):
        return "🔥"
    return {"High": "🔴", "Medium": "🟠", "Low": "🟡"}.get(imp, "⚪")


def events_for_day(events, day: date):
    """คืนข่าวที่กระทบทองของวันที่ระบุ (ตามเขตเวลาท้องถิ่น) เรียงตามเวลา"""
    out = []
    for ev in events:
        if not is_gold_relevant(ev):
            continue
        ldt = to_local(parse_dt(ev))
        if ldt and ldt.date() == day:
            out.append((ldt, ev))
    out.sort(key=lambda x: x[0])
    return out


def forecast_trend(ev):
    """
    แนวโน้มคาดการณ์ต่อทอง แบบหยาบ ๆ จาก forecast เทียบ previous
    หลักการ: ตัวเลขเศรษฐกิจสหรัฐแข็งแกร่ง/เงินเฟ้อสูง -> USD แข็ง -> มักกดทองลง
    (เป็นแนวทางคร่าว ๆ ไม่ใช่คำแนะนำการลงทุน)
    """
    f = _num(ev.get("forecast"))
    p = _num(ev.get("previous"))
    if f is None or p is None:
        return "—"
    if abs(f - p) < 1e-9:
        return "ทรงตัว → ผลต่อทองจำกัด"
    stronger = f > p
    # ข่าวจ้างงาน/เงินเฟ้อ/GDP: ตัวเลขสูง = USD แข็ง = กดทอง
    return (
        "คาดตัวเลขสูงขึ้น → USD แข็ง อาจกดทองลง" if stronger
        else "คาดตัวเลขลดลง → USD อ่อน อาจหนุนทองขึ้น"
    )


def market_view(ev):
    """มุมมองตลาดก่อนข่าวออก (forecast = ฉันทามติตลาด)"""
    fc = ev.get("forecast")
    pv = ev.get("previous")
    if not fc:
        return "🔮 ตลาดยังไม่มีตัวเลขคาดการณ์ชัดเจน"
    line = f"🔮 ตลาดคาด: {fc}"
    if pv:
        line += f" (ครั้งก่อน {pv})"
    f, p = _num(fc), _num(pv)
    if f is not None and p is not None and abs(f - p) > 1e-9:
        if f > p:
            line += " — ตลาดมองตัวเลขแข็งขึ้น เอนไป USD แข็ง/กดทอง"
        else:
            line += " — ตลาดมองตัวเลขอ่อนลง เอนไป USD อ่อน/หนุนทอง"
    else:
        line += " — ตลาดมองทรงตัว"
    line += "\n   ↳ ถ้า actual สูงกว่าคาด = กดทอง🔻 / ต่ำกว่าคาด = หนุนทอง🔺"
    return line


def minutes_to_event(ev, now_local):
    """นาทีที่เหลือก่อนข่าวออก (บวก=ยังไม่ถึง, ลบ=ผ่านมาแล้ว)"""
    ldt = to_local(parse_dt(ev))
    if ldt is None:
        return None
    return (ldt - now_local).total_seconds() / 60.0


def _num(s):
    if not s:
        return None
    try:
        return float(str(s).replace("%", "").replace("K", "").replace("M", "").replace(",", "").strip())
    except ValueError:
        return None
