"""
สร้างไฟล์ข้อมูลสำหรับหน้าเว็บ Dashboard -> docs/data.json
ดึงข่าวทั้งสัปดาห์ กรองเฉพาะที่กระทบทอง แล้วเขียนเป็น JSON ให้หน้าเว็บอ่าน
เรียกจาก ci_loop เป็นระยะ (commit ขึ้น GitHub Pages)
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import news

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
OUT = os.path.join(DOCS_DIR, "data.json")


def _direction(ev):
    a = news._num(ev.get("actual"))
    f = news._num(ev.get("forecast"))
    if not ev.get("actual") or a is None or f is None:
        return ""
    if abs(a - f) < 1e-9:
        return "flat"
    return "down" if a > f else "up"   # actual สูง = กดทอง(down)


def build():
    events = news.fetch_events()
    out = []
    for ev in events:
        if not news.is_gold_relevant(ev):
            continue
        ldt = news.to_local(news.parse_dt(ev))
        if ldt is None:
            continue
        out.append({
            "title": ev.get("title", ""),
            "datetime": ldt.isoformat(),
            "date": ldt.strftime("%Y-%m-%d"),
            "time": ldt.strftime("%H:%M"),
            "impact": ev.get("impact", ""),
            "top": news.is_top_tier(ev),
            "forecast": ev.get("forecast") or "",
            "previous": ev.get("previous") or "",
            "actual": ev.get("actual") or "",
            "market_view": news.market_view(ev).replace("\n", " "),
            "direction": _direction(ev),
        })
    out.sort(key=lambda x: x["datetime"])
    # มุมมองนักลงทุน (พาดหัวข่าว) — best effort
    heads = []
    try:
        import headlines
        heads = headlines.fetch_headlines(6)
    except Exception as e:
        print("[dashboard] headlines error:", e)
    data = {
        "updated": datetime.now(ZoneInfo(config.LOCAL_TZ)).isoformat(),
        "tz": config.LOCAL_TZ,
        "count": len(out),
        "events": out,
        "headlines": heads,
    }
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


if __name__ == "__main__":
    d = build()
    print(f"เขียน {OUT} | {d['count']} ข่าว")
