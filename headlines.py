"""
ดึง "มุมมองนักลงทุน" จากพาดหัวข่าวล่าสุด (RSS ฟรี)
เน้นข่าวที่เกี่ยวกับ ทอง/Fed/ดอลลาร์/เงินเฟ้อ — สะท้อนว่าตลาดกำลังมองอะไร
ออกแบบให้ทนทาน: ลองหลายฟีด ถ้าล่มทั้งหมดก็คืน [] (ระบบไม่พัง)
"""
import urllib.request
import xml.etree.ElementTree as ET

# ฟีดข่าวการเงิน/ทอง (ลองทีละอันจนกว่าจะได้)
FEEDS = [
    "https://www.investing.com/rss/commodities_Gold.rss",
    "https://www.fxstreet.com/rss/news",
    "https://www.investing.com/rss/news_285.rss",   # Economy
    "https://feeds.marketwatch.com/marketwatch/marketpulse/",
]

KEYWORDS = ["gold", "xau", "fed", "fomc", "powell", "dollar", "rate",
            "inflation", "cpi", "treasury", "yield", "bullion", "ทอง"]


def _parse(xml_bytes, limit):
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not title:
            continue
        items.append({"title": title, "link": link})
        if len(items) >= limit * 3:
            break
    return items


def fetch_headlines(limit=5):
    """คืน list ของ {title, link} ข่าวที่เกี่ยวกับทอง/Fed ล่าสุด"""
    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
            items = _parse(raw, limit)
            # กรองเฉพาะที่เกี่ยวข้อง
            rel = [i for i in items
                   if any(k in i["title"].lower() for k in KEYWORDS)]
            picked = rel or items   # ถ้าฟีดเป็นข่าวทองอยู่แล้วก็เอาทั้งหมด
            if picked:
                return picked[:limit]
        except Exception as e:
            print(f"[headlines] {url} ใช้ไม่ได้: {e}")
            continue
    return []


if __name__ == "__main__":
    for h in fetch_headlines():
        print("-", h["title"])
