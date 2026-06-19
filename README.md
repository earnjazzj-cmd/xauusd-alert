# ระบบแจ้งเตือนข่าว XAUUSD (ทองคำ) เข้า LINE

แจ้งเตือน 2 แบบ:
1. **บรีฟเช้า 9 โมง** — สรุปข่าววันนี้ที่กระทบทอง: เวลา / ความแรง / ค่าคาดการณ์ / แนวโน้ม
2. **เรียลไทม์** — พอตัวเลข actual ออก ส่งเข้า LINE ทันที พร้อมบอกว่าสูง/ต่ำกว่าคาดและทิศทางต่อทอง

ข่าวที่กรอง: เน้นข่าว **USD** ระดับ **High/Medium** (NFP, CPI, PCE, FOMC, ดอกเบี้ย, GDP ฯลฯ) เพราะกระทบทองมากที่สุด

---

## โครงสร้างไฟล์
- `config.py` — ตั้งค่ากลาง (อ่านจาก `.env`)
- `line_notify.py` — ส่งข้อความเข้า LINE
- `news.py` — ดึง + กรองข่าว ForexFactory
- `morning_brief.py` — บรีฟเช้า (รันด้วย cron 9 โมง)
- `realtime_alert.py` — เฝ้าข่าวเรียลไทม์ (รันค้างไว้)
- `test_logic.py` — ทดสอบ logic แบบไม่ต้องต่อเน็ต

---

## ขั้นตอนติดตั้ง

### 1) ตั้งค่า LINE Messaging API
> หมายเหตุ: LINE Notify ปิดบริการแล้ว (31 มี.ค. 2025) จึงต้องใช้ Messaging API

1. ไปที่ https://developers.line.biz/console/ ล็อกอินด้วยบัญชี LINE
2. สร้าง **Provider** → สร้าง **Messaging API channel** (ได้ LINE Official Account ฟรี)
3. แท็บ **Messaging API** → คัดลอก **Channel access token (long-lived)** (กด Issue ถ้ายังไม่มี)
4. หา **userId ของคุณ**:
   - เพิ่มเพื่อน OA ตัวนี้ใน LINE ของคุณ
   - วิธีง่าย: ในแท็บ Basic settings จะมี **Your user ID** (ของเจ้าของ) — ใช้ตัวนั้นได้เลย
   - หรือส่งเข้า **กลุ่ม**: เชิญบอทเข้ากลุ่มแล้วใช้ `groupId` (ต้องตั้ง webhook อ่าน event มาดู)
5. ปิด "Auto-reply messages" ใน LINE Official Account Manager ได้ตามชอบ

### 2) ตั้งค่าโปรเจกต์
```bash
cp .env.example .env
# แก้ .env ใส่ LINE_CHANNEL_ACCESS_TOKEN และ LINE_TO
```
ใช้ Python 3.9+ (ใช้แต่ standard library ไม่ต้องลงแพ็กเกจเพิ่ม)

### 3) ทดสอบ
```bash
python test_logic.py        # ตรวจ logic การกรอง/ฟอร์แมต
python line_notify.py       # ทดสอบส่งข้อความเข้า LINE จริง
python morning_brief.py     # ลองสร้าง+ส่งบรีฟเช้า
```

---

## รันอัตโนมัติ

### บรีฟเช้า 9 โมง (Linux/Mac — cron)
```bash
crontab -e
# รันทุกวันจันทร์–ศุกร์ เวลา 09:00
0 9 * * 1-5 cd /path/to/xauusd_alert && /usr/bin/python3 morning_brief.py >> brief.log 2>&1
```

### เรียลไทม์ (รันค้าง)
```bash
nohup python3 realtime_alert.py >> realtime.log 2>&1 &
```
หรือทำเป็น systemd service / pm2 เพื่อให้รีสตาร์ตอัตโนมัติ

### Windows (Task Scheduler)
- บรีฟเช้า: สร้าง Task รัน `python morning_brief.py` ทุกวัน 09:00
- เรียลไทม์: สร้าง Task รัน `python realtime_alert.py` ตอน log on (ตั้ง restart on failure)

> เคล็ดลับเรียลไทม์: ถ้าอยากประหยัด ให้รัน `realtime_alert.py` เฉพาะช่วงข่าวออก
> (ข่าวสหรัฐส่วนใหญ่ออก 19:30–21:00 น. เวลาไทย) แทนการรันทั้งวัน

---

## ปรับแต่ง (ใน .env)
- `WATCH_IMPACTS=High` — เอาเฉพาะข่าวแดง ไม่เอา Medium
- `POLL_INTERVAL_SEC=30` — เช็คถี่ขึ้น (อย่าต่ำกว่า 20–30 วิ เพื่อไม่ยิง feed ถี่เกิน)
- `LOCAL_TZ=Asia/Bangkok` — เขตเวลาที่แสดง

## ข้อควรรู้
- การวิเคราะห์ "แนวโน้มต่อทอง" เป็นกฎหยาบ ๆ (ตัวเลขสหรัฐแข็ง → USD แข็ง → กดทอง) ใช้ประกอบการตัดสินใจเท่านั้น **ไม่ใช่คำแนะนำการลงทุน**
- feed เป็นของ ForexFactory (faireconomy.media) อย่ายิงถี่เกินไป
- ทอง XAUUSD ยังถูกกระทบจากภูมิรัฐศาสตร์/ความเสี่ยงตลาด ซึ่งไม่อยู่ในปฏิทินข่าว
