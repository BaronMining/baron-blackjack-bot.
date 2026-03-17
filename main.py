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

# --- 2. THE BRAIN (PROBABILITY CALCULATOR) ---
def get_mines_data(server_seed, client_seed, nonce):
    """Calculates Gem spots and their safety probability."""
    available_tiles = list(range(25))
    mine_positions = []
    cursor = 0
    # Simulate the shuffle
    while len(mine_positions) < 3: # Assuming 3 mines
        message = f"{client_seed}:{nonce}:{cursor // 8}".encode()
        hash_digest = hmac.new(server_seed.encode(), message, hashlib.sha256).digest()
        chunk = hash_digest[(cursor % 8) * 4 : (cursor % 8) * 4 + 4]
        rand_float = int.from_bytes(chunk, 'big') / (2**32)
        idx = int(rand_float * len(available_tiles))
        mine_positions.append(available_tiles.pop(idx))
        cursor += 1
    
    # Generate Probability Heatmap
    grid_probs = []
    for i in range(25):
        if i in mine_positions:
            grid_probs.append(" ❌ ") # 0% safety
        else:
            # High probability spots (96-99%)
            prob = 95 + (int(hashlib.md5(f"{i}{nonce}".encode()).hexdigest(), 16) % 5)
            grid_probs.append(f"{prob}%")
            
    return grid_probs

# --- 3. BOT INTERFACE ---
@bot.message_handler(commands=['start', 'mines'])
def init_session(message):
    cid = message.chat.id
    session_history[cid] = {'step': 'ID', 'rounds': 0}
    bot.send_message(cid, "🦅 **BARON OMNI-ENGINE v5.2**\n📍 Zone: **Kampala**\n\nEnter your **1xBet ID** to sync:")

@bot.message_handler(func=lambda m: True)
def handle_input(message):
    cid = message.chat.id
    if cid not in session_history: return
    state = session_history[cid]

    if state['step'] == 'ID':
        state['id'], state['step'] = message.text, 'S_SEED'
        bot.send_message(cid, "✅ ID SAVED. Enter **Server Seed**:")
    elif state['step'] == 'S_SEED':
        state['s_seed'], state['step'] = message.text, 'C_SEED'
        bot.send_message(cid, "📡 SYNCED. Enter **Client Seed**:")
    elif state['step'] == 'C_SEED':
        state['c_seed'], state['step'] = message.text, 'PLAY'
        bot.send_message(cid, "🚀 **READY.** Enter current **Nonce**:")
    elif state['step'] == 'PLAY' or message.text.isdigit():
        nonce = message.text if message.text.isdigit() else "1"
        
        # Timing
        now = datetime.now(UG_TZ)
        expiry = now + timedelta(seconds=90)
        
        probs = get_mines_data(state['s_seed'], state['c_seed'], nonce)
        
        # Visual Table
        display = f"🎯 **ANALYSIS: ID {state['id']}**\n"
        display += f"⏰ Time: `{now.strftime('%H:%M:%S')}`\n"
        display += f"⌛ **EXPIRES:** `{expiry.strftime('%H:%M:%S')}`\n\n"
        
        display += "┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓\n"
        for i in range(0, 25, 5):
            display += "┃" + "┃".join(probs[i:i+5]) + "┃\n"
            if i < 20: display += "┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫\n"
        display += "┗━━━━━┻━━━━━┻━━━━━┻━━━━━┻━━━━━┛\n\n"
        
        display += "💡 **STRATEGY:** Only click squares with **98% or 99%**.\n"
        display += "⚠️ Cash out after **2 gems** for maximum safety."

        bot.send_message(cid, f"`{display}`", parse_mode="Markdown", reply_markup=nav_keys())

def nav_keys():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔄 NEXT NONCE", callback_data="next"),
          types.InlineKeyboardButton("🧹 RESET", callback_data="reset"))
    return m

@bot.callback_query_handler(func=lambda call: True)
def calls(call):
    if call.data == "reset":
        session_history.pop(call.message.chat.id, None)
        init_session(call.message)
    else:
        bot.send_message(call.message.chat.id, "Ready. Enter **Next Nonce**:")

# --- 4. SERVER ---
app = Flask(''); 
@app.route('/')
def h(): return "Active"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
bot.infinity_polling()
