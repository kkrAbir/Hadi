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
"1": "🇺🇸 USA / Canada",
"44": "🇬🇧 United Kingdom",
"33": "🇫🇷 France",
"39": "🇮🇹 Italy",
"34": "🇪🇸 Spain",
# --- অতিরিক্ত দেশসমূহ ---
# North America (Area Code 1 - shared with USA/Canada)
"1242": "🇧🇸 Bahamas",
"1246": "🇧🇧 Barbados",
"1268": "🇦🇬 Antigua & Barbuda",
"1284": "🇻🇬 British Virgin Islands",
"1345": "🇰🇾 Cayman Islands",
"1441": "🇧🇲 Bermuda",
"1473": "🇬🇩 Grenada",
"1649": "🇹🇨 Turks & Caicos Islands",
"1664": "🇲🇸 Montserrat",
"1670": "🇲🇵 Northern Mariana Islands",
"1671": "🇬🇺 Guam",
"1684": "🇦🇸 American Samoa",
"1758": "🇱🇨 St. Lucia",
"1767": "🇩🇲 Dominica",
"1784": "🇻🇨 St. Vincent & Grenadines",
"1809": "🇩🇴 Dominican Republic",
"1868": "🇹🇹 Trinidad & Tobago",
"1876": "🇯🇲 Jamaica",
# Africa
"20": "🇪🇬 Egypt",
"27": "🇿🇦 South Africa",
"212": "🇲🇦 Morocco / 🇪🇭 Western Sahara",
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
"242": "🇨🇬 Congo - Brazzaville",
"243": "🇨🇩 Congo - Kinshasa (DRC)",
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
"262": "🇷🇪 Réunion / 🇾🇹 Mayotte",
"263": "🇿🇼 Zimbabwe",
"264": "🇳🇦 Namibia",
"265": "🇲🇼 Malawi",
"266": "🇱🇸 Lesotho",
"267": "🇧🇼 Botswana",
"268": "🇸🇿 Eswatini",
"269": "🇰🇲 Comoros",
"290": "🇸🇭 St. Helena / 🇹🇦 Tristan da Cunha",
"291": "🇪🇷 Eritrea",
"297": "🇦🇼 Aruba",
"298": "🇫🇴 Faroe Islands",
"299": "🇬🇱 Greenland",
# South America
"51": "🇵🇪 Peru",
"52": "🇲🇽 Mexico",
"53": "🇨🇺 Cuba",
"54": "🇦🇷 Argentina",
"55": "🇧🇷 Brazil",
"56": "🇨🇱 Chile",
"57": "🇨🇴 Colombia",
"58": "🇻🇪 Venezuela",
"590": "🇬🇵 Guadeloupe / 🇲🇫 St. Martin / 🇧🇱 St. Barthélemy",
"591": "🇧🇴 Bolivia",
"592": "🇬🇾 Guyana",
"593": "🇪🇨 Ecuador",
"594": "🇬🇫 French Guiana",
"595": "🇵🇾 Paraguay",
"597": "🇸🇷 Suriname",
"598": "🇺🇾 Uruguay",
"599": "🇨🇼 Curaçao / 🇸🇽 Sint Maarten / 🇧🇶 Caribbean Netherlands",
# Europe
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
"358": "🇫🇮 Finland / 🇦🇽 Åland Islands",
"359": "🇧🇬 Bulgaria",
"370": "🇱🇹 Lithuania",
"371": "🇱🇻 Latvia",
"372": "🇪🇪 Estonia",
"373": "🇲🇩 Moldova / 🇹🇱 East Timor",
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
"387": "🇧🇦 Bosnia & Herzegovina",
"389": "🇲🇰 North Macedonia",
"40": "🇷🇴 Romania",
"41": "🇨🇭 Switzerland",
"43": "🇦🇹 Austria",
"45": "🇩🇰 Denmark",
"46": "🇸🇪 Sweden",
"47": "🇳🇴 Norway",
"48": "🇵🇱 Poland",
"49": "🇩🇪 Germany",
# Asia
"60": "🇲🇾 Malaysia",
"61": "🇦🇺 Australia / 🇨🇽 Christmas Island / 🇨🇨 Cocos Islands",
"62": "🇮🇩 Indonesia",
"63": "🇵🇭 Philippines",
"64": "🇳🇿 New Zealand / 🇵🇳 Pitcairn",
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
# Oceania
"670": "🇹🇱 East Timor",
"672": "🇳🇫 Norfolk Island / 🇦🇶 Antarctica",
"673": "🇧🇳 Brunei",
"674": "🇳🇷 Nauru",
"675": "🇵🇬 Papua New Guinea",
"676": "🇹🇴 Tonga",
"677": "🇸🇧 Solomon Islands",
"678": "🇻🇺 Vanuatu",
"679": "🇫🇯 Fiji",
"680": "🇵🇼 Palau",
"681": "🇼🇫 Wallis & Futuna",
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
# Russia & Central Asia
"7": "🇷🇺 Russia / 🇰🇿 Kazakhstan",
# Other
"259": "🇰🇲 Comoros (deprecated)",
"293": "🇸🇭 St. Helena (deprecated)",
"295": "🇸🇲 San Marino (deprecated)",
"296": "🇹🇿 Tanzania (deprecated)",
"420": "🇨🇿 Czechia",
"421": "🇸🇰 Slovakia",
"423": "🇱🇮 Liechtenstein",
"499": "🇩🇪 Germany (deprecated)",
"992": "🇹🇯 Tajikistan",
"993": "🇹🇲 Turkmenistan",
"994": "🇦🇿 Azerbaijan",
"995": "🇬🇪 Georgia",
"996": "🇰🇬 Kyrgyzstan",
"998": "🇺🇿 Uzbekistan",
# Special Codes
"800": "🌐 International Toll-Free",
"882": "🌐 International Networks",
"883": "🌐 International Networks",
"888": "🌐 International Networks"
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
            f"⏰ <b>Time:</b> {date}\n"
            f"📞 <b>Number:</b> {number}\n"
            f"🌍 <b>Country:</b> {country}\n"
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
