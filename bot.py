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
# HEALTH CHECK SERVER (For Render/Heroku)
# =====================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT IS ONLINE"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web, daemon=True).start()

# =====================================================
# ENVIRONMENT VARIABLES
# =====================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
USERNAME = os.getenv("PANEL_USER")
PASSWORD = os.getenv("PANEL_PASS")

BASE = "http://91.232.105.47"
DATA_URL = f"{BASE}/ints/agent/res/data_smscdr.php"
LOGIN_PAGE = f"{BASE}/ints/login"
LOGIN_POST = f"{BASE}/ints/signin"

# =====================================================
# LOGGING & BOT INIT
# =====================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
try:
    bot = Bot(token=BOT_TOKEN)
except Exception as e:
    logging.error(f"Bot Token Error: {e}")
    bot = None

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9"
})

OTP_REGEX = re.compile(r"\b\d{4,8}\b")
sent_keys = set()
first_run = True

# =====================================================
# HELPERS
# =====================================================
def get_country(number):
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

def login():
    try:
        page = session.get(LOGIN_PAGE, timeout=10)
        m = re.search(r"What is (\d+)\s*\+\s*(\d+)", page.text)
        payload = {"username": USERNAME, "password": PASSWORD}
        if m: payload["capt"] = int(m.group(1)) + int(m.group(2))
        
        res = session.post(LOGIN_POST, data=payload, timeout=10)
        if "dashboard" in res.text.lower() or res.status_code == 200:
            logging.info("Login Successful ✓")
            return True
        return False
    except Exception as e:
        logging.error(f"Login Failed: {e}")
        return False

# =====================================================
# CORE LOGIC
# =====================================================
async def check_sms():
    global first_run
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        api_url = f"{DATA_URL}?fdate1={today}%2000:00:00&fdate2={today}%2023:59:59&sEcho=1&iDisplayLength=50"
        
        response = session.get(api_url, headers={"X-Requested-With": "XMLHttpRequest"}, timeout=10)
        
        if "login" in response.text.lower():
            login()
            return

        data = response.json()
        if "aaData" not in data: return

        for row in data["aaData"]:
            if len(row) < 6: continue
            
            date, number, service, message = str(row[0]), str(row[2]), str(row[3]), str(row[5])
            if not message: continue

            key = f"{number}|{message}|{date}"
            if first_run:
                sent_keys.add(key)
                continue
            if key in sent_keys: continue

            # New Message Processing
            sent_keys.add(key)
            matches = OTP_REGEX.findall(message)
            otp = matches[0] if matches else "N/A"
            country = get_country(number)
            masked_num = number[:-5] + "**" + number[-3:] if len(number) > 5 else number

            # UI Design: Buttons for each number found in SMS
            buttons = []
            all_numbers = re.findall(r'\d{4,8}', message)
            for n in all_numbers:
                buttons.append([InlineKeyboardButton(f"🔢 Code: {n}", callback_data="none")])
            
            buttons.append([
                InlineKeyboardButton("🧑‍💻 Dev", url="https://t.me/RTX_ABIR_4090"),
                InlineKeyboardButton("📞 Channel", url="https://t.me/GURUBIT")
            ])
            
            text = (
                "🚀 <b>NEW SMS INCOMING</b> 🚀\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"📅 <b>Time:</b> <code>{date}</code>\n"
                f"📞 <b>From:</b> <code>{masked_num}</code>\n"
                f"🌍 <b>Origin:</b> {country}\n"
                f"⚙️ <b>Service:</b> <b>{service}</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"📝 <b>SMS Content:</b>\n<i>{message}</i>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"🔐 <b>Extracted OTP:</b> <code>{otp}</code>"
            )

            if bot:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                logging.info(f"Forwarded: {otp}")

        if first_run:
            first_run = False
            logging.info("Sync complete. Waiting for new SMS...")

    except Exception as e:
        logging.error(f"Error: {e}")

# =====================================================
# MAIN RUNNER
# =====================================================
async def main():
    if login():
        while True:
            await check_sms()
            await asyncio.sleep(5) # Will check every 5 seconds
    else:
        logging.critical("Initial Login Failed! Check Credentials.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
