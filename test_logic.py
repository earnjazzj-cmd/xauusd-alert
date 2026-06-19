"""
ทดสอบ logic การกรอง/ฟอร์แมต ด้วยข้อมูลตัวอย่าง (ไม่ต้องต่อเน็ต/LINE)
รัน: python test_logic.py
"""
import news

SAMPLE = [
    {"title": "Core CPI m/m", "country": "USD", "date": "2026-06-18T08:30:00-04:00",
     "impact": "High", "forecast": "0.3%", "previous": "0.2%", "actual": ""},
    {"title": "Non-Farm Employment Change", "country": "USD", "date": "2026-06-18T08:30:00-04:00",
     "impact": "High", "forecast": "185K", "previous": "175K", "actual": "210K"},
    {"title": "Retail Sales m/m", "country": "USD", "date": "2026-06-18T08:30:00-04:00",
     "impact": "Medium", "forecast": "0.4%", "previous": "0.6%", "actual": ""},
    {"title": "German Bund Auction", "country": "EUR", "date": "2026-06-18T05:00:00-04:00",
     "impact": "Low", "forecast": "", "previous": "", "actual": ""},
    {"title": "Some Minor Speech", "country": "USD", "date": "2026-06-18T12:00:00-04:00",
     "impact": "Low", "forecast": "", "previous": "", "actual": ""},
]


def run():
    rel = [e for e in SAMPLE if news.is_gold_relevant(e)]
    assert len(rel) == 3, f"ควรกรองได้ 3 ข่าว (USD High/Medium) แต่ได้ {len(rel)}"

    titles = [e["title"] for e in rel]
    assert "German Bund Auction" not in titles, "ต้องตัดข่าว EUR ออก"
    assert "Some Minor Speech" not in titles, "ต้องตัด Low impact ออก"

    nfp = next(e for e in SAMPLE if "Non-Farm" in e["title"])
    assert news.is_top_tier(nfp), "NFP ต้องเป็น top tier"
    assert news.impact_icon(nfp) == "🔥"

    cpi = next(e for e in SAMPLE if e["title"] == "Core CPI m/m")
    assert news.impact_icon(cpi) == "🔥"  # CPI = top tier keyword

    # forecast trend: forecast(0.3) > previous(0.2) -> USD แข็ง กดทอง
    assert "กดทอง" in news.forecast_trend(cpi)
    # retail: forecast(0.4) < previous(0.6) -> หนุนทอง
    retail = next(e for e in SAMPLE if e["title"] == "Retail Sales m/m")
    assert "หนุนทอง" in news.forecast_trend(retail)

    # local time conversion: 08:30 EDT(-04:00) -> 19:30 Asia/Bangkok
    ldt = news.to_local(news.parse_dt(cpi))
    assert ldt.strftime("%H:%M") == "19:30", ldt.strftime("%H:%M")

    # events_for_day
    day = ldt.date()
    todays = news.events_for_day(SAMPLE, day)
    assert len(todays) == 3
    # เรียงตามเวลา
    times = [t.strftime("%H:%M") for t, _ in todays]
    assert times == sorted(times)

    print("✅ ผ่านทุกเทสต์")
    print("ตัวอย่างไอคอน:", [news.impact_icon(e) for e in rel])
    print("เวลาท้องถิ่น CPI:", ldt.strftime("%Y-%m-%d %H:%M %Z"))


if __name__ == "__main__":
    run()
