import os, telebot, pytz, hmac, hashlib
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. CONFIGURATION ---
TOKEN = '8320085836:AAGUv9vJOLGGGt4X-vOX7bLIgGZoBziyzSY'
bot = telebot.TeleBot(TOKEN, threaded=False)
UG_TZ = pytz.timezone('Africa/Kampala')
session_history = {} 

# --- 2. ANALYTICS & TIMING ---
def get_safe_status():
    """Determines if the current Kampala time is good for betting."""
    now = datetime.now(UG_TZ)
    hour = now.hour
    # Statistically best: Late night (1AM-5AM) or Mid-Morning (9AM-11AM)
    if (1 <= hour <= 5) or (9 <= hour <= 11):
        return "🟢 EXCELLENT (Low Traffic)", True
    elif (18 <= hour <= 21):
        return "🔴 DANGEROUS (Peak Traffic)", False
    else:
        return "🟡 STABLE (Caution)", True

def get_mines_prediction(server_seed, client_seed, nonce, mines=3):
    """HMAC-SHA256 Grid Generation Logic"""
    available_tiles = list(range(25))
    mine_positions = []
    cursor = 0
    while len(mine_positions) < mines:
        message = f"{client_seed}:{nonce}:{cursor // 8}".encode()
        hash_digest = hmac.new(server_seed.encode(), message, hashlib.sha256).digest()
        chunk = hash_digest[(cursor % 8) * 4 : (cursor % 8) * 4 + 4]
        rand_float = int.from_bytes(chunk, 'big') / (2**32)
        idx = int(rand_float * len(available_tiles))
        mine_positions.append(available_tiles.pop(idx))
        cursor += 1
    
    grid = ["⭐"] * 25
    for m in mine_positions: grid[m] = "·"
    return grid

# --- 3. BOT COMMANDS ---
@bot.message_handler(commands=['start', 'mines'])
def init_session(message):
    cid = message.chat.id
    session_history[cid] = {'step': 'ID', 'rounds': 0}
    status_text, _ = get_safe_status()
    bot.send_message(cid, f"🦅 **BARON OMNI-ENGINE v5.0**\n📍 Zone: **Kampala, Uganda**\n🚦 Server: {status_text}\n\nTo begin, enter your **1xBet ID**:")

@bot.message_handler(func=lambda m: True)
def process_logic(message):
    cid = message.chat.id
    if cid not in session_history: return
    state = session_history[cid]

    if state['step'] == 'ID':
        state['id'], state['step'] = message.text, 'S_SEED'
        bot.send_message(cid, "✅ ID SAVED. Enter **Server Seed** (Hashed):")
    elif state['step'] == 'S_SEED':
        state['s_seed'], state['step'] = message.text, 'C_SEED'
        bot.send_message(cid, "📡 SYNCED. Enter **Client Seed** (e.g. 'Baron'):")
    elif state['step'] == 'C_SEED':
        state['c_seed'], state['step'] = message.text, 'PLAY'
        bot.send_message(cid, "🚀 **READY.** Enter current **Nonce** (Round #):")
    elif state['step'] == 'PLAY' or message.text.isdigit():
        nonce = message.text if message.text.isdigit() else "0"
        state['rounds'] += 1
        
        # Timing Calculations
        now = datetime.now(UG_TZ)
        expiry = now + timedelta(minutes=1, seconds=30)
        status_text, is_safe = get_safe_status()
        
        grid = get_mines_prediction(state['s_seed'], state['c_seed'], nonce)
        
        # Visual Grid Construction
        display = f"🎯 **PREDICTION: ID {state['id']}**\n"
        display += f"⏰ Time (EAT): `{now.strftime('%H:%M:%S')}`\n"
        display += f"⌛ **EXPIRES:** `{expiry.strftime('%H:%M:%S')}`\n"
        display += f"🚦 Server: {status_text}\n\n"
        display += "┏━━━┳━━━┳━━━┳━━━┳━━━┓\n"
        for i in range(0, 25, 5):
            display += "┃ " + " ┃ ".join(grid[i:i+5]) + " ┃\n"
            if i < 20: display += "┣━━━╋━━━╋━━━╋━━━╋━━━┫\n"
        display += "┗━━━┻━━━┻━━━┻━━━┻━━━┛\n\n"
        
        # Rotator Alert
        if state['rounds'] >= 5:
            display += "⚠️ **SECURITY ALERT:** You've played 5 rounds. Use 'RESET' to change your Client Seed now!\n"
        
        if not is_safe:
            display += "❌ **WAIT:** High server traffic. Risk of pattern drift is high."
        else:
            display += "🟢 **PLAY NOW:** Pattern is synchronized."

        bot.send_message(cid, f"`{display}`", parse_mode="Markdown", reply_markup=nav_keys())

def nav_keys():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔄 NEXT NONCE", callback_data="next"))
    m.add(types.InlineKeyboardButton("🧹 RESET SESSION", callback_data="reset"))
    return m

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "reset":
        session_history.pop(call.message.chat.id, None)
        init_session(call.message)
    else:
        bot.send_message(call.message.chat.id, "Enter the **Next Nonce**:")

# --- 4. DEPLOY ---
app = Flask(''); 
@app.route('/')
def h(): return "Baron 5.0 Timed Active"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
bot.infinity_polling()
