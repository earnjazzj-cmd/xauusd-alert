"""
สร้างการ์ด Flex Message สำหรับ LINE (UI สวย)
- alert_bubble: การ์ดตอนข่าวออก (เรียลไทม์)
- brief_bubble: การ์ดสรุปข่าวเช้า
"""
import news

# ลิงก์กราฟ XAUUSD (กดการ์ด/ปุ่มแล้วเปิดอันนี้)
CHART_URL = "https://th.tradingview.com/chart/?symbol=FOREXCOM%3AXAUUSD"

# สีตามความแรง
COLOR_TOP = "#B71C1C"      # แดงเข้ม = แรงมาก (NFP/CPI/FOMC)
COLOR_HIGH = "#E53935"     # แดง = แรง
COLOR_MED = "#F9A825"      # เหลืองอำพัน = ปานกลาง
COLOR_GOLD = "#C8A415"     # ทอง (header)
GREEN = "#2E7D32"
RED = "#C62828"
GREY = "#888888"


def _intensity(ev):
    """คืน (ป้ายความแรง, อิโมจิ, สี)"""
    if news.is_top_tier(ev):
        return ("แรงมาก", "⚡", COLOR_TOP)
    if ev.get("impact") == "High":
        return ("แรง", "🔴", COLOR_HIGH)
    return ("ปานกลาง", "🟠", COLOR_MED)


def _impact_color(ev):
    return _intensity(ev)[2]


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
    label, emoji, head_color = _intensity(ev)
    return {
        "type": "bubble",
        "action": {"type": "uri", "label": "ดูกราฟ", "uri": CHART_URL},  # กดทั้งใบ -> เปิดกราฟ
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": head_color,
            "paddingAll": "12px", "spacing": "xs",
            "contents": [
                {"type": "box", "layout": "horizontal", "contents": [
                    {"type": "text", "text": "⚡ ข่าวออกแล้ว", "color": "#FFFFFF",
                     "weight": "bold", "size": "sm", "flex": 0},
                    {"type": "text", "text": f"{emoji} {label}", "color": "#FFFFFF",
                     "size": "sm", "align": "end", "weight": "bold"},
                ]},
                {"type": "text", "text": ev.get("title", ""), "color": "#FFFFFF",
                 "weight": "bold", "size": "lg", "wrap": True},
                {"type": "text", "text": "แตะที่การ์ดเพื่อดูกราฟ", "color": "#FFFFFFCC",
                 "size": "xxs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md", "paddingAll": "14px",
            "contents": [
                _row("เวลา", f"{time_str} น."),
                _row("Actual", ev.get("actual") or "-", "#111111", bold=True),
                _row("ตลาดคาด", ev.get("forecast") or "-"),
                _row("ครั้งก่อน", ev.get("previous") or "-"),
                {"type": "separator", "margin": "md"},
                {"type": "box", "layout": "vertical", "margin": "md",
                 "backgroundColor": "#F6F6F8", "cornerRadius": "8px", "paddingAll": "10px",
                 "contents": [
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
                 "action": {"type": "uri", "label": "📈 ดูกราฟ XAUUSD", "uri": CHART_URL}},
            ],
        },
    }


def _chip(label, color):
    return {"type": "text", "text": label, "color": "#FFFFFF", "size": "xxs",
            "align": "center", "weight": "bold", "backgroundColor": color,
            "cornerRadius": "10px", "flex": 0, "offsetTop": "1px",
            "paddingAll": "2px", "paddingStart": "8px", "paddingEnd": "8px"}


def brief_bubble(today_str, rows, headlines=None):
    """
    การ์ดสรุปข่าวเช้า
    rows = list ของ (icon, time_str, ev)
    headlines = list ของ dict {title} มุมมองนักลงทุน (ออปชัน)
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
            label, emoji, color = _intensity(ev)
            body.append({
                "type": "box", "layout": "vertical", "margin": "md", "spacing": "xs",
                "contents": [
                    {"type": "box", "layout": "baseline", "spacing": "sm", "contents": [
                        {"type": "text", "text": f"{t} น.", "size": "sm", "weight": "bold",
                         "color": "#222222", "flex": 0},
                        _chip(f"{emoji} {label}", color),
                    ]},
                    {"type": "text", "size": "sm", "weight": "bold", "wrap": True,
                     "color": "#333333", "text": ev.get("title", "")},
                    {"type": "text", "size": "xs", "color": "#777777", "wrap": True,
                     "text": news.market_view(ev).replace("\n", " ")},
                ],
            })

    # มุมมองนักลงทุน (พาดหัวข่าวล่าสุด)
    if headlines:
        body.append({"type": "separator", "margin": "lg"})
        body.append({"type": "text", "text": "📰 นักลงทุนกำลังพูดถึง",
                     "weight": "bold", "size": "sm", "color": "#C8A415", "margin": "md"})
        for h in headlines[:4]:
            body.append({"type": "text", "text": "• " + h.get("title", ""),
                         "size": "xs", "color": "#555555", "wrap": True, "margin": "sm"})

    body.append({"type": "text", "text": "⚠️ ข้อมูลประกอบ ไม่ใช่คำแนะนำลงทุน",
                 "color": "#AAAAAA", "size": "xxs", "margin": "lg", "wrap": True})

    return {
        "type": "bubble", "size": "mega",
        "action": {"type": "uri", "label": "ดูกราฟ", "uri": CHART_URL},
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": COLOR_GOLD,
            "paddingAll": "12px",
            "contents": [{"type": "text", "text": "☀️ สรุปข่าวเช้า XAUUSD · แตะดูกราฟ",
                          "color": "#FFFFFF", "weight": "bold", "size": "lg"}],
        },
        "body": {"type": "box", "layout": "vertical", "paddingAll": "14px", "contents": body},
    }
