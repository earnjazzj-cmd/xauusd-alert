"""
ส่งข้อความเข้า LINE ผ่าน Messaging API (push message)
LINE Notify ถูกปิดไปแล้ว (31 มี.ค. 2025) จึงใช้ Messaging API แทน
"""
import json
import urllib.request
import config

PUSH_URL = "https://api.line.me/v2/bot/message/push"


def push(text: str) -> bool:
    """ส่งข้อความ text เข้า LINE. คืน True ถ้าสำเร็จ"""
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not config.LINE_TO:
        print("[LINE] ยังไม่ได้ตั้งค่า LINE_CHANNEL_ACCESS_TOKEN หรือ LINE_TO")
        return False

    payload = {
        "to": config.LINE_TO,
        "messages": [{"type": "text", "text": text[:4900]}],  # ลิมิต 5000 ตัวอักษร
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        PUSH_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            ok = resp.status == 200
            if ok:
                print("[LINE] ส่งสำเร็จ")
            return ok
    except urllib.error.HTTPError as e:
        print(f"[LINE] HTTP error {e.code}: {e.read().decode('utf-8', 'ignore')}")
    except Exception as e:
        print(f"[LINE] error: {e}")
    return False


if __name__ == "__main__":
    # ทดสอบส่งข้อความ: python line_notify.py
    push("✅ ทดสอบระบบแจ้งเตือน XAUUSD เชื่อมต่อ LINE สำเร็จ")
