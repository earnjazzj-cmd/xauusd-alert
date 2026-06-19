#!/usr/bin/env bash
# สคริปต์ติดตั้งบน Oracle Free VM (Ubuntu)
# รันครั้งเดียว:  bash deploy_setup.sh
# ก่อนรัน: ต้องมีไฟล์โปรเจกต์ทั้งหมด + ไฟล์ .env (ใส่ token แล้ว) อยู่ในโฟลเดอร์นี้
set -e

APPDIR="$HOME/xauusd_alert"
echo "==> ใช้โฟลเดอร์: $APPDIR"
cd "$APPDIR"

# 1) ติดตั้ง python3 (ปกติ Ubuntu มีอยู่แล้ว)
echo "==> ตรวจ python3"
sudo apt-get update -y >/dev/null 2>&1 || true
sudo apt-get install -y python3 tzdata >/dev/null 2>&1 || true
python3 --version

# 2) ตรวจว่ามี .env
if [ ! -f "$APPDIR/.env" ]; then
  echo "!! ไม่พบไฟล์ .env — สร้างก่อนแล้วใส่ LINE_CHANNEL_ACCESS_TOKEN กับ LINE_TO"
  exit 1
fi

# 3) สร้าง systemd service ให้รันค้าง + รีสตาร์ตเองอัตโนมัติ
SERVICE=/etc/systemd/system/xauusd.service
echo "==> สร้าง service: $SERVICE"
sudo tee "$SERVICE" >/dev/null <<EOF
[Unit]
Description=XAUUSD Gold News LINE Alert
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$APPDIR
ExecStart=/usr/bin/python3 $APPDIR/run_all.py
Restart=always
RestartSec=10
User=$USER

[Install]
WantedBy=multi-user.target
EOF

# 4) เปิดใช้งาน
echo "==> เปิดใช้งาน service"
sudo systemctl daemon-reload
sudo systemctl enable xauusd.service
sudo systemctl restart xauusd.service

echo ""
echo "==================================================="
echo " ติดตั้งเสร็จ! ระบบกำลังรันค้าง 24 ชม. แล้ว"
echo " เช็คสถานะ:   sudo systemctl status xauusd"
echo " ดู log สด:   journalctl -u xauusd -f"
echo "==================================================="
