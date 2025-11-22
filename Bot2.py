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
# ENVIRONMENT VARIABLES (SECURE)
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

# OTP REGEX
OTP_REGEX = re.compile(r"\b\d{4,8}\b")

# =====================================================
# COUNTRY DETECTOR (ADD YOUR FULL DATA HERE)
# =====================================================
COUNTRIES = {
    "880": "🇧🇩 Bangladesh",
    "1": "🇺🇸 USA /🇨🇦Canada",
    "44": "🇬🇧 United Kingdom",
    "91": "🇮🇳 India",
    "7": "🇷🇺 Russia / 🇰🇿Kazakhstan",
}

def get_country(number):
    for code in sorted(COUNTRIES.keys(), key=lambda x: -len(x)):
        if number.startswith(code):
            return COUNTRIES[code]
    return "🌍 Unknown"

# =====================================================
# MEMORY-ONLY SENT KEYS (RENDER SAFE)
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
def get_api_url():
    today = datetime.now().strftime("%Y-%m-%d")
    return (
        f"{DATA_URL}?fdate1={today}%2000:00:00&fdate2={today}%2023:59:59&"
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
# CHECK OTP + SEND MESSAGE
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

        matches = OTP_REGEX.findall(message)
        if not matches:
            continue

        otp = max(matches, key=len)
        key = f"{number}|{otp}|{date}"

        if key in sent_keys:
            continue

        sent_keys.add(key)

        country = get_country(number)

        text = (
            "✨ <b>OTP Received</b> ✨\n\n"
            f"🌍 <b>Country:</b> {country}\n"
            f"⏰ <b>Time:</b> {date}\n"
            f"📞 <b>Number:</b> {number}\n"
            f"🔧 <b>Service:</b> {service}\n"
            f"🔐 <b>OTP:</b> <code>{otp}</code>\n"
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

            logging.info(f"[✓] OTP SENT → {otp}")

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
