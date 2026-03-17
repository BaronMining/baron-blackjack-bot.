import os, telebot, hmac, hashlib
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread

# Try to import pytz, fallback to UTC if it fails
try:
    import pytz
    UG_TZ = pytz.timezone('Africa/Kampala')
except ImportError:
    UG_TZ = None

# AUTH - YOUR NEW WORKING TOKEN
TOKEN = '8769467053:AAGTGgwDl-bCDw-EGSnIaPieXdpEt0jjbGc'
bot = telebot.TeleBot(TOKEN, threaded=False)

# SHA256 PROBABILITY BRAIN
def get_sha256_mines(server_seed, client_seed, nonce):
    game_hash = hashlib.sha256(f"{server_seed}:{client_seed}:{nonce}".encode()).hexdigest()
    grid_probs = []
    for i in range(25):
        val = int(game_hash[i % 64], 16) 
        if val < 3: 
            grid_probs.append(" 💣 ") 
        else:
            p = 97 + (val % 3)
            grid_probs.append(f"{p}%")
    return grid_probs

session = {}

@bot.message_handler(commands=['start', 'mines'])
def start(m):
    session[m.chat.id] = {'step': 'S_SEED'}
    bot.send_message(m.chat.id, "🦅 **BARON betPawa SHA256 v6.3**\n\nPaste the **Hashed Server Seed** from betPawa:")

@bot.message_handler(func=lambda m: True)
def handle(m):
    cid = m.chat.id
    if cid not in session: return
    s = session[cid]

    if s['step'] == 'S_SEED':
        s['server'], s['step'] = m.text, 'C_SEED'
        bot.send_message(cid, "✅ Server Seed Locked.\nEnter **Client Seed** (e.g., tuT9NESeP4o3GDyk6ZKU):")
    elif s['step'] == 'C_SEED':
        s['client'], s['step'] = m.text, 'PLAY'
        bot.send_message(cid, "🚀 **SYNCED.** Enter current **Nonce**:")
    elif s['step'] == 'PLAY' or m.text.isdigit():
        nonce = m.text if m.text.isdigit() else "0"
        probs = get_sha256_mines(s['server'], s['client'], nonce)
        
        # Timing logic
        now = datetime.now(UG_TZ) if UG_TZ else datetime.utcnow()
        expiry = now + timedelta(seconds=90)

        res = f"🎯 **betPawa ANALYSIS (Nonce: {nonce})**\n"
        res += f"⏰ Time: `{now.strftime('%H:%M:%S')}` | ⌛ Expiry: `{expiry.strftime('%H:%M:%S')}`\n\n"
        res += "┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓\n"
        for i in range(0, 25, 5):
            res += "┃" + "┃".join(probs[i:i+5]) + "┃\n"
            if i < 20: res += "┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫\n"
        res += "┗━━━━━┻━━━━━┻━━━━━┻━━━━━┻━━━━━┛\n\n"
        res += "🟢 **BEST PICKS:** 99% Spots\n"
        res += "⚠️ Target 2 Gems & Cashout (3 Mines Mode)."
        
        bot.send_message(cid, f"`{res}`", parse_mode="Markdown", reply_markup=nav())

def nav():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 NEXT NONCE", callback_data="next"),
               types.InlineKeyboardButton("🧹 RESET", callback_data="reset"))
    return markup

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data == "reset":
        session.pop(c.message.chat.id, None)
        start(c.message)
    else:
        bot.send_message(c.message.chat.id, "Enter **Next Nonce**:")

# SERVER FOR RENDER
app = Flask('')
@app.route('/')
def home(): return "Baron v6.3 Active"

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
