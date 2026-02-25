#--- START OF FILE Bot2.py ---

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
# HEALTH CHECK SERVER
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

BASE = "http://91.232.105.47"
DATA_URL = BASE + "/ints/agent/res/data_smscdr.php"
LOGIN_PAGE = BASE + "/ints/login"
LOGIN_POST = BASE + "/ints/signin"

# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# Bot টোকেন না থাকলে লগিং শুরু হবে না, তাই এখানে try-except ব্যবহার করা ভালো
try:
    bot = Bot(token=BOT_TOKEN)
except Exception as e:
    logging.error(f"Failed to initialize Telegram Bot. Check BOT_TOKEN. Error: {e}")
    bot = None # যদি ইনিশিয়ালাইজ না হয়

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
# COUNTRY DETECTOR
# =====================================================
COUNTRIES = {
"972": "🇮🇱 Israel",
"880": "🇧🇩 Bangladesh",
"91": "🇮🇳 India",
"971": "🇦🇪 UAE",
"974": "🇶🇦 Qatar",
"966": "🇸🇦 Saudi Arabia",
"965": "🇰🇼 Kuwait",
"973": "🇧🇭 Bahrain",
"968": "🇴🇲 Oman",
"964": "🇮🇶 Iraq",
"963": "🇸🇾 Syria",
"962": "🇯🇴 Jordan",
"90": "🇹🇷 Turkey",
"1": "🇺🇸 USA",
"44": "🇬🇧 United Kingdom",
"33": "🇫🇷 France",
"39": "🇮🇹 Italy",
"34": "🇪🇸 Spain",
"1242": "🇧🇸 Bahamas",
"1246": "🇧🇧 Barbados",
"1268": "🇦🇬 Antigua",
"1284": "🇻🇬 British Virgin Islands",
"1345": "🇰🇾 Cayman Islands",
"1441": "🇧🇲 Bermuda",
"1473": "🇬🇩 Grenada",
"1649": "🇹🇨 Turks",
"1664": "🇲🇸 Montserrat",
"1670": "🇲🇵 Northern Mariana Islands",
"1671": "🇬🇺 Guam",
"1684": "🇦🇸 American Samoa",
"1758": "🇱🇨 St. Lucia",
"1767": "🇩🇲 Dominica",
"1784": "🇻🇨 St. Vincent",
"1809": "🇩🇴 Dominican Republic",
"1868": "🇹🇹 Trinidad",
"1876": "🇯🇲 Jamaica",
"20": "🇪🇬 Egypt",
"27": "🇿🇦 South Africa",
"212": "🇲🇦 Morocco",
"213": "🇩🇿 Algeria",
"216": "🇹🇳 Tunisia",
"218": "🇱🇾 Libya",
"220": "🇬🇲 Gambia",
"221": "🇸🇳 Senegal",
"222": "🇲🇷 Mauritania",
"223": "🇲🇱 Mali",
"224": "🇬🇳 Guinea",
"225": "🇨🇮 Côte d'Ivoire",
"226": "🇧🇫 Burkina Faso",
"227": "🇳🇪 Niger",
"228": "🇹🇬 Togo",
"229": "🇧🇯 Benin",
"230": "🇲🇺 Mauritius",
"231": "🇱🇷 Liberia",
"232": "🇸🇱 Sierra Leone",
"233": "🇬🇭 Ghana",
"234": "🇳🇬 Nigeria",
"235": "🇹🇩 Chad",
"236": "🇨🇫 Central African Republic",
"237": "🇨🇲 Cameroon",
"238": "🇨🇻 Cape Verde",
"239": "🇸🇹 São Tomé & Príncipe",
"240": "🇬🇶 Equatorial Guinea",
"241": "🇬🇦 Gabon",
"242": "🇨🇬 Brazzaville",
"243": "🇨🇩 Congo",
"244": "🇦🇴 Angola",
"245": "🇬🇼 Guinea-Bissau",
"246": "🇮🇴 British Indian Ocean Territory",
"247": "🇦🇨 Ascension Island",
"248": "🇸🇨 Seychelles",
"249": "🇸🇩 Sudan",
"250": "🇷🇼 Rwanda",
"251": "🇪🇹 Ethiopia",
"252": "🇸🇴 Somalia",
"253": "🇩🇯 Djibouti",
"254": "🇰🇪 Kenya",
"255": "🇹🇿 Tanzania",
"256": "🇺🇬 Uganda",
"257": "🇧🇮 Burundi",
"258": "🇲🇿 Mozambique",
"260": "🇿🇲 Zambia",
"261": "🇲🇬 Madagascar",
"262": "🇷🇪 Réunion",
"263": "🇿🇼 Zimbabwe",
"264": "🇳🇦 Namibia",
"265": "🇲🇼 Malawi",
"266": "🇱🇸 Lesotho",
"267": "🇧🇼 Botswana",
"268": "🇸🇿 Eswatini",
"269": "🇰🇲 Comoros",
"290": "🇸🇭 St. Helena",
"291": "🇪🇷 Eritrea",
"297": "🇦🇼 Aruba",
"298": "🇫🇴 Faroe Islands",
"299": "🇬🇱 Greenland",
"51": "🇵🇪 Peru",
"52": "🇲🇽 Mexico",
"53": "🇨🇺 Cuba",
"54": "🇦🇷 Argentina",
"55": "🇧🇷 Brazil",
"56": "🇨🇱 Chile",
"57": "🇨🇴 Colombia",
"58": "🇻🇪 Venezuela",
"590": "🇬🇵 Guadeloupe",
"591": "🇧🇴 Bolivia",
"592": "🇬🇾 Guyana",
"593": "🇪🇨 Ecuador",
"594": "🇬🇫 French Guiana",
"595": "🇵🇾 Paraguay",
"597": "🇸🇷 Suriname",
"598": "🇺🇾 Uruguay",
"599": "🇨🇼 Curaçao",
"30": "🇬🇷 Greece",
"31": "🇳🇱 Netherlands",
"32": "🇧🇪 Belgium",
"350": "🇬🇮 Gibraltar",
"351": "🇵🇹 Portugal",
"352": "🇱🇺 Luxembourg",
"353": "🇮🇪 Ireland",
"354": "🇮🇸 Iceland",
"355": "🇦🇱 Albania",
"356": "🇲🇹 Malta",
"357": "🇨🇾 Cyprus",
"358": "🇫🇮 Finland",
"359": "🇧🇬 Bulgaria",
"370": "🇱🇹 Lithuania",
"371": "🇱🇻 Latvia",
"372": "🇪🇪 Estonia",
"373": "🇲🇩 Moldova",
"374": "🇦🇲 Armenia",
"375": "🇧🇾 Belarus",
"376": "🇦🇩 Andorra",
"377": "🇲🇨 Monaco",
"378": "🇸🇲 San Marino",
"380": "🇺🇦 Ukraine",
"381": "🇷🇸 Serbia",
"382": "🇲🇪 Montenegro",
"385": "🇭🇷 Croatia",
"386": "🇸🇮 Slovenia",
"387": "🇧🇦 Bosnia",
"389": "🇲🇰 North Macedonia",
"40": "🇷🇴 Romania",
"41": "🇨🇭 Switzerland",
"43": "🇦🇹 Austria",
"45": "🇩🇰 Denmark",
"46": "🇸🇪 Sweden",
"47": "🇳🇴 Norway",
"48": "🇵🇱 Poland",
"49": "🇩🇪 Germany",
"60": "🇲🇾 Malaysia",
"61": "🇦🇺 Australia",
"62": "🇮🇩 Indonesia",
"63": "🇵🇭 Philippines",
"64": "🇳🇿 New Zealand",
"65": "🇸🇬 Singapore",
"66": "🇹🇭 Thailand",
"81": "🇯🇵 Japan",
"82": "🇰🇷 South Korea",
"84": "🇻🇳 Vietnam",
"850": "🇰🇵 North Korea",
"852": "🇭🇰 Hong Kong",
"853": "🇲🇴 Macau",
"855": "🇰🇭 Cambodia",
"856": "🇱🇦 Laos",
"86": "🇨🇳 China",
"886": "🇹🇼 Taiwan",
"92": "🇵🇰 Pakistan",
"93": "🇦🇫 Afghanistan",
"94": "🇱🇰 Sri Lanka",
"95": "🇲🇲 Myanmar",
"970": "🇵🇸 Palestine",
"975": "🇧🇹 Bhutan",
"976": "🇲🇳 Mongolia",
"977": "🇳🇵 Nepal",
"98": "🇮🇷 Iran",
"670": "🇹🇱 East Timor",
"672": "🇳🇫 Norfolk Island",
"673": "🇧🇳 Brunei",
"674": "🇳🇷 Nauru",
"675": "🇵🇬 Papua New Guinea",
"676": "🇹🇴 Tonga",
"677": "🇸🇧 Solomon Islands",
"678": "🇻🇺 Vanuatu",
"679": "🇫🇯 Fiji",
"680": "🇵🇼 Palau",
"681": "🇼🇫 Wallis",
"682": "🇨🇰 Cook Islands",
"683": "🇳🇺 Niue",
"685": "🇼🇸 Samoa",
"686": "🇰🇮 Kiribati",
"687": "🇳🇨 New Caledonia",
"688": "🇹🇻 Tuvalu",
"689": "🇵🇫 French Polynesia",
"690": "🇹🇰 Tokelau",
"691": "🇫🇲 Micronesia",
"692": "🇲🇭 Marshall Islands",
"7": "🇷🇺 Russia",
"259": "🇰🇲 Comoros",
"293": "🇸🇭 St. Helena",
"295": "🇸🇲 San Marino",
"296": "🇹🇿 Tanzania",
"420": "🇨🇿 Czechia",
"421": "🇸🇰 Slovakia",
"423": "🇱🇮 Liechtenstein",
"499": "🇩🇪 Germany",
"992": "🇹🇯 Tajikistan",
"993": "🇹🇲 Turkmenistan",
"994": "🇦🇿 Azerbaijan",
"995": "🇬🇪 Georgia",
"996": "🇰🇬 Kyrgyzstan",
"998": "🇺🇿 Uzbekistan",
}

def get_country(number):
    for code in sorted(COUNTRIES.keys(), key=lambda x: -len(x)):
        if number.startswith(code):
            return COUNTRIES[code]
    return "🌍 Unknown Country"
    
# =====================================================
# MEMORY-ONLY SENT KEYS (RENDER SAFE)
# =====================================================
sent_keys = set()

first_run = True 

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

        logging.error(f"Login failed ✗. Response text snippet: {res.text[:100]}")
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
        
        if response.status_code != 200:
            logging.warning(f"Panel data fetch failed. Status Code: {response.status_code}")
            return None

        if "login" in response.text.lower():
            logging.warning("Session expired. Re-logging in.")
            login()
            return None

        return response.json()

    except Exception as e:
        logging.error(f"Data Fetch Error: {e}")
        return None

# =====================================================
# CHECK OTP + SEND MESSAGE
# =====================================================
async def check_sms():
    global first_run
    data = fetch_data()
    
    if not data or "aaData" not in data:
        logging.info("No data received or 'aaData' missing in API response.")
        return

    for row in data["aaData"]:
        if len(row) < 6:
            continue

        date = str(row[0]).strip()
        number = str(row[2]).strip()
        service = str(row[3]).strip()
        message = str(row[5]).strip()

        # Check if message is empty or just whitespace
        if not message:
            continue

        # Unique key
        key = f"{number}|{message}|{date}"
        
        if first_run:
            sent_keys.add(key)
            continue

        if key in sent_keys:
            continue

        # Find OTP code (if any)
        matches = OTP_REGEX.findall(message)
        if matches:
            otp = max(matches, key=len)
        else:
            otp = "No Code Found"

        sent_keys.add(key)
        country = get_country(number)

        # -------------------------------------------------
        # NUMBER MASKING LOGIC
        # -------------------------------------------------
        # Keeps last 3 digits visible.
        # Masks the 2 digits before that with '**'.
        if len(number) >= 5:
            masked_number = number[:-5] + "**" + number[-3:]
        else:
            masked_number = number  
        # -------------------------------------------------

        text = (
            "✨ <b>SMS Received</b> ✨\n\n"
            f"⏰ <b>Time:</b> {date}\n"
            f"📞 <b>Number:</b> {masked_number}\n"
            f"🌍 <b>Country:</b> {country}\n"
            f"🔧 <b>Service:</b> {service}\n"
            f"🔐 <b>OTP/Code:</b> <code>{otp}</code>\n"
            f"📝 <b>Message:</b> <i>{message}</i>\n\n"
            "<b>POWERED BY</b> @RTX_ABIR_4090"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧑‍💻Dev", url="https://t.me/RTX_ABIR_4090")],
            [InlineKeyboardButton("📞Number", url="https://t.me/GURUBIT")]
        ])
        
        # --- DEBUG LOGGING ADDED ---
        logging.info(f"NEW MESSAGE DETECTED! Key: {key} | OTP: {otp} | Country: {country}")
        # ---------------------------

        try:
            if bot and CHAT_ID:
                # AWAIT ADDED: Telegram Bot send_message is an awaitable method
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                logging.info(f"[✓] SMS SENT to {CHAT_ID} -> OTP: {otp}") # ডিবাগিং লগ
            else:
                logging.error("Cannot send message: bot object or CHAT_ID is missing.")

        except Exception as e:
            # টেলিগ্রামের ক্ষেত্রে এটি সবচেয়ে সাধারণ ব্যর্থতা
            logging.error(f"Telegram error sending message to {CHAT_ID}: {e}")

    if first_run:
        first_run = False
        logging.info("--- History Synced. Waiting for NEW messages... ---")

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

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.critical(f"Fatal error in main loop: {e}")

#--- END OF FILE Bot2.py ---
