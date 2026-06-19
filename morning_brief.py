"""
บรีฟตอนเช้า: สรุปข่าววันนี้ที่กระทบทอง XAUUSD
รันตอน 9 โมงเช้าผ่าน cron / Task Scheduler
  python morning_brief.py
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import config
import news
import line_notify


def build_message():
    today = datetime.now(ZoneInfo(config.LOCAL_TZ)).date()
    events = news.fetch_events()
    todays = news.events_for_day(events, today)

    header = f"☀️ ข่าวกระทบทอง XAUUSD วันนี้ ({today.strftime('%d/%m/%Y')})"

    if not todays:
        return f"{header}\n\nวันนี้ไม่มีข่าวสำคัญ (USD, ระดับ High/Medium) ที่กระทบทอง 🟢"

    lines = [header, ""]
    for ldt, ev in todays:
        icon = news.impact_icon(ev)
        t = ldt.strftime("%H:%M")
        lines.append(f"{icon} {t} น. | {ev['title']} ({ev.get('impact','')})")
        lines.append(f"    {news.market_view(ev)}")
        lines.append("")

    lines.append("🔥=ข่าวแรงพิเศษ 🔴=High 🟠=Medium")
    lines.append("⚠️ เป็นข้อมูลประกอบ ไม่ใช่คำแนะนำลงทุน")
    return "\n".join(lines)


def main():
    msg = build_message()
    print(msg)
    line_notify.push(msg)


if __name__ == "__main__":
    main()
