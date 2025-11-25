import os
import re
import json
import time
import asyncio
import logging
import requests
from datetime import datetime
from flask import Flask
import threading
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# =====================================================
# HEALTH CHECK SERVER (REQUIRED FOR RENDER + UPTIMEROBOT)
# =====================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT RUNNING OK"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# =====================================================
# ENVIRONMENT VARIABLES
# =====================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

USERNAME = os.getenv("PANEL_USER")
PASSWORD = os.getenv("PANEL_PASS")

BASE = "http://185.2.83.39"
DATA_URL = BASE + "/ints/agent/res/data_smscdr.php"
LOGIN_PAGE = BASE + "/ints/login"
LOGIN_POST = BASE + "/ints/signin"


# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
bot = Bot(token=BOT_TOKEN)

# =====================================================
# REQUESTS SESSION
# =====================================================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
})

# =====================================================
# COUNTRY DETECTOR
# =====================================================
COUNTRIES = {
"972": "🇮🇱 Israel", "880": "🇧🇩 Bangladesh", "91": "🇮🇳 India", "971": "🇦🇪 UAE", 
"974": "🇶🇦 Qatar", "966": "🇸🇦 Saudi Arabia", "965": "🇰🇼 Kuwait", "973": "🇧🇭 Bahrain", 
"968": "🇴🇲 Oman", "964": "🇮🇶 Iraq", "963": "🇸🇾 Syria", "962": "🇯🇴 Jordan", 
"90": "🇹🇷 Turkey", "1": "🇺🇸 USA / 🇨🇦Canada", "44": "🇬🇧 United Kingdom", 
"33": "🇫🇷 France", "39": "🇮🇹 Italy", "34": "🇪🇸 Spain", "60": "🇲🇾 Malaysia", 
"61": "🇦🇺 Australia", "62": "🇮🇩 Indonesia", "63": "🇵🇭 Philippines", 
"86": "🇨🇳 China", "92": "🇵🇰 Pakistan", "94": "🇱🇰 Sri Lanka", "84": "🇻🇳 Vietnam",
"7": "🇷🇺 Russia / 🇰🇿 Kazakhstan", "20": "🇪🇬 Egypt", "27": "🇿🇦 South Africa",
# ... (এখানে আপনার পুরো দেশের লিস্ট থাকবে) ...
}

def get_country(number):
    for code in sorted(COUNTRIES.keys(), key=lambda x: -len(x)):
        if number.startswith(code):
            return COUNTRIES[code]
    return "🌍 Unknown Country"
    
# =====================================================
# MEMORY-ONLY SENT KEYS
# =====================================================
sent_keys = set()

# =====================================================
# LOGIN FUNCTION
# =====================================================
def login():
    try:
        page = session.get(LOGIN_PAGE, timeout=10)
        m = re.search(r"What is (\d+)\s*\+\s*(\d+)", page.text)
        captcha = int(m.group(1)) + int(m.group(2)) if m else None

        payload = {"username": USERNAME, "password": PASSWORD}
        if captcha:
            payload["capt"] = captcha

        res = session.post(LOGIN_POST, data=payload, timeout=10)

        if "dashboard" in res.text.lower():
            logging.info("Login success ✓")
            return True

        if res.status_code == 200 and "login" not in res.text.lower():
            logging.info("Login success ✓")
            return True

        logging.error("Login failed ✗")
        return False

    except Exception as e:
        logging.error(f"Login Error: {e}")
        return False

# =====================================================
# API URL GENERATOR
# =====================================================
from datetime import datetime, timedelta

def get_api_url():
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)

    fdate1 = two_hours_ago.strftime("%Y-%m-%d%%20%H:%M:%S")
    fdate2 = now.strftime("%Y-%m-%d%%20%H:%M:%S")

    return (
        f"{DATA_URL}?fdate1={fdate1}&fdate2={fdate2}&"
        "sEcho=1&iColumns=7&iDisplayStart=0&iDisplayLength=50"
    )

# =====================================================
# FETCH PANEL DATA
# =====================================================
def fetch_data():
    try:
        response = session.get(
            get_api_url(),
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=10
        )

        if "login" in response.text.lower():
            login()
            return None

        return response.json()

    except Exception:
        return None

# =====================================================
# CHECK SMS (NO SKIP LOGIC)
# =====================================================
async def check_sms():
    data = fetch_data()
    if not data or "aaData" not in data:
        return

    for row in data["aaData"]:
        if len(row) < 6:
            continue

        date = str(row[0]).strip()
        number = str(row[2]).strip()
        service = str(row[3]).strip()
        message = str(row[5]).strip()

        # ==========================================
        # ডুপ্লিকেট চেকিং (OTP না থাকলে মেসেজ দিয়ে চেক হবে)
        # ==========================================
        key = f"{number}|{message}|{date}"
        if key in sent_keys:
            continue

        sent_keys.add(key)

        # ==========================================
        # OTP খোঁজার চেষ্টা (ডিসপ্লের জন্য)
        # ==========================================
        otp_display = "⚠️ Check Message" # ডিফল্ট যদি কোড না পায়

        # ১. সাধারণ ৪-৮ সংখ্যার কোড খোঁজা
        numbers = re.findall(r"\d{4,8}", message)
        if numbers:
            otp_display = max(numbers, key=len)
        else:
            # ২. স্পেস বা হাইফেন সরিয়ে খোঁজা (যেমন 123 456)
            clean_msg = message.replace(" ", "").replace("-", "")
            clean_numbers = re.findall(r"\d{4,8}", clean_msg)
            if clean_numbers:
                otp_display = max(clean_numbers, key=len)
        
        # এখানে কোনো 'continue' বা 'return' নেই, তাই সব মেসেজ নিচে যাবে
        
        country = get_country(number)

        text = (
            "✨ <b>SMS Received</b> ✨\n\n"
            f"⏰ <b>Time:</b> {date}\n"
            f"📞 <b>Number:</b> {number}\n"
            f"🌍 <b>Country:</b> {country}\n"
            f"🔧 <b>Service:</b> {service}\n"
            f"🔐 <b>Code:</b> <code>{otp_display}</code>\n"
            f"📝 <b>Message:</b> <i>{message}</i>\n\n"
            "<b>POWERED BY</b> @RTX_ABIR_4090"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧑‍💻Dev", url="https://t.me/RTX_ABIR_4090")],
            [InlineKeyboardButton("📞Number", url="https://t.me/+iooisG0X4oNmODdl")]
        ])

        try:
            bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logging.info(f"[✓] SENT: {service} -> {otp_display}")

        except Exception as e:
            logging.error(f"Telegram error: {e}")

# =====================================================
# MAIN LOOP
# =====================================================
async def main():
    if not login():
        logging.error("Login failed. Bot stopping.")
        return

    while True:
        await check_sms()
        await asyncio.sleep(3)

asyncio.run(main())
