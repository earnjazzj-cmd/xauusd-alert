"""
สร้างการ์ด Flex Message สำหรับ LINE (UI สวย)
- alert_bubble: การ์ดตอนข่าวออก (เรียลไทม์)
- brief_bubble: การ์ดสรุปข่าวเช้า
"""
import news

# สีตามความแรง
COLOR_HIGH = "#E53935"     # แดง
COLOR_MED = "#FB8C00"      # ส้ม
COLOR_GOLD = "#C8A415"     # ทอง (header)
GREEN = "#2E7D32"
RED = "#C62828"
GREY = "#888888"


def _impact_color(ev):
    return COLOR_HIGH if ev.get("impact") == "High" else COLOR_MED


def _dir_from_actual(ev):
    """คืน (ข้อความ, สี) ทิศทางต่อทองจาก actual vs forecast"""
    a = news._num(ev.get("actual"))
    f = news._num(ev.get("forecast"))
    if a is None or f is None:
        return ("รอประเมินผลต่อทอง", GREY)
    if abs(a - f) < 1e-9:
        return ("ตรงคาด → ผลต่อทองจำกัด", GREY)
    if a > f:
        return ("สูงกว่าคาด → กดทองลง 🔻", RED)
    return ("ต่ำกว่าคาด → หนุนทองขึ้น 🔺", GREEN)


def _row(label, value, value_color="#333333", bold=False):
    return {
        "type": "box", "layout": "baseline", "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "color": "#999999", "size": "sm", "flex": 4},
            {"type": "text", "text": str(value), "wrap": True, "color": value_color,
             "size": "sm", "flex": 6, "weight": "bold" if bold else "regular"},
        ],
    }


def alert_bubble(ev, time_str):
    """การ์ดตอนข่าวออก"""
    dir_text, dir_color = _dir_from_actual(ev)
    head_color = _impact_color(ev)
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": head_color,
            "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": "⚡ ข่าวออกแล้ว", "color": "#FFFFFF",
                 "weight": "bold", "size": "sm"},
                {"type": "text", "text": ev.get("title", ""), "color": "#FFFFFF",
                 "weight": "bold", "size": "lg", "wrap": True},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md", "paddingAll": "14px",
            "contents": [
                _row("เวลา", f"{time_str} น. ({ev.get('impact','')})"),
                _row("Actual", ev.get("actual") or "-", "#111111", bold=True),
                _row("ตลาดคาด", ev.get("forecast") or "-"),
                _row("ครั้งก่อน", ev.get("previous") or "-"),
                {"type": "separator", "margin": "md"},
                {"type": "box", "layout": "vertical", "margin": "md", "contents": [
                    {"type": "text", "text": dir_text, "color": dir_color,
                     "weight": "bold", "size": "md", "wrap": True},
                ]},
                {"type": "text", "text": "⚠️ ข้อมูลประกอบ ไม่ใช่คำแนะนำลงทุน",
                 "color": "#AAAAAA", "size": "xxs", "margin": "md", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "contents": [
                {"type": "button", "style": "primary", "color": COLOR_GOLD, "height": "sm",
                 "action": {"type": "uri", "label": "ดูกราฟ XAUUSD",
                            "uri": "https://www.tradingview.com/symbols/XAUUSD/"}},
            ],
        },
    }


def brief_bubble(today_str, rows):
    """
    การ์ดสรุปข่าวเช้า
    rows = list ของ (icon, time_str, ev)
    """
    body = [{
        "type": "text", "text": f"ข่าวกระทบทองวันนี้ ({today_str})",
        "weight": "bold", "size": "md", "wrap": True, "color": "#333333",
    }, {"type": "separator", "margin": "md"}]

    if not rows:
        body.append({"type": "text", "text": "วันนี้ไม่มีข่าว USD สำคัญ 🟢",
                     "margin": "md", "size": "sm", "color": "#2E7D32"})
    else:
        for icon, t, ev in rows:
            body.append({
                "type": "box", "layout": "vertical", "margin": "md", "spacing": "xs",
                "contents": [
                    {"type": "text", "size": "sm", "weight": "bold", "wrap": True,
                     "color": _impact_color(ev),
                     "text": f"{icon} {t} น. · {ev.get('title','')}"},
                    {"type": "text", "size": "xs", "color": "#777777", "wrap": True,
                     "text": news.market_view(ev).replace("\n", " ")},
                ],
            })
    body.append({"type": "text", "text": "⚠️ ข้อมูลประกอบ ไม่ใช่คำแนะนำลงทุน",
                 "color": "#AAAAAA", "size": "xxs", "margin": "lg", "wrap": True})

    return {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": COLOR_GOLD,
            "paddingAll": "12px",
            "contents": [{"type": "text", "text": "☀️ สรุปข่าวเช้า XAUUSD",
                          "color": "#FFFFFF", "weight": "bold", "size": "lg"}],
        },
        "body": {"type": "box", "layout": "vertical", "paddingAll": "14px", "contents": body},
    }
