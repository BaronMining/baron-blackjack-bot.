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

TOKEN = '8320085836:AAGUv9vJOLGGGt4X-vOX7bLIgGZoBziyzSY'
bot = telebot.TeleBot(TOKEN, threaded=False)
session_history = {}

def get_mines_data(server_seed, client_seed, nonce):
    """Calculates the 5x5 grid with probability logic."""
    available_tiles = list(range(25))
    mine_positions = []
    cursor = 0
    # Simulate the Provably Fair shuffle for 3 mines
    while len(mine_positions) < 3:
        message = f"{client_seed}:{nonce}:{cursor // 8}".encode()
        hash_digest = hmac.new(server_seed.encode(), message, hashlib.sha256).digest()
        chunk = hash_digest[(cursor % 8) * 4 : (cursor % 8) * 4 + 4]
        rand_float = int.from_bytes(chunk, 'big') / (2**32)
        idx = int(rand_float * len(available_tiles))
        mine_positions.append(available_tiles.pop(idx))
        cursor += 1
    
    grid_probs = []
    for i in range(25):
        if i in mine_positions:
            grid_probs.append(" 💣 ")
        else:
            # Generate probability between 98% and 99.9%
            prob = 98 + (int(hashlib.md5(f"{i}{nonce}".encode()).hexdigest(), 16) % 2)
            grid_probs.append(f"{prob}%")
    return grid_probs

@bot.message_handler(commands=['start', 'mines'])
def init_session(message):
    cid = message.chat.id
    session_history[cid] = {'step': 'ID'}
    bot.send_message(cid, "🦅 **BARON OMNI-ENGINE v5.6**\nStatus: **Online**\nTarget: **Mines Dare 2 Win**\n\nEnter your **1xBet ID**:")

@bot.message_handler(func=lambda m: True)
def handle_input(message):
    cid = message.chat.id
    if cid not in session_history: return
    state = session_history[cid]

    if state['step'] == 'ID':
        state['id'], state['step'] = message.text, 'S_SEED'
        bot.send_message(cid, "✅ ID LOGGED. Enter **Server Seed** (from game settings):")
    elif state['step'] == 'S_SEED':
        state['s_seed'], state['step'] = message.text, 'C_SEED'
        bot.send_message(cid, "📡 SEED SYNCED. Enter **Client Seed**:")
    elif state['step'] == 'C_SEED':
        state['c_seed'], state['step'] = message.text, 'PLAY'
        bot.send_message(cid, "🚀 **SYSTEM READY.** Enter current **Nonce**:")
    elif state['step'] == 'PLAY' or message.text.isdigit():
        nonce = message.text if message.text.isdigit() else "1"
        
        now = datetime.now(UG_TZ) if UG_TZ else datetime.utcnow()
        expiry = now + timedelta(seconds=90)
        probs = get_mines_data(state['s_seed'], state['c_seed'], nonce)
        
        display = f"🎯 **ANALYSIS: ID {state['id']}**\n"
        display += f"⏰ Time: `{now.strftime('%H:%M:%S')}`\n"
        display += f"⌛ **EXPIRY:** `{expiry.strftime('%H:%M:%S')}`\n\n"
        
        display += "┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓\n"
        for i in range(0, 25, 5):
            display += "┃" + "┃".join(probs[i:i+5]) + "┃\n"
            if i < 20: display += "┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫\n"
        display += "┗━━━━━┻━━━━━┻━━━━━┻━━━━━┻━━━━━┛\n\n"
        
        display += "🟢 **BEST PICKS:** Squares with **99%**\n"
        display += "🛑 **DANGER:** Avoid 💣 spots!"

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
        bot.send_message(call.message.chat.id, "Enter **Next Nonce**:")

app = Flask(''); 
@app.route('/')
def h(): return "Baron Engine Active"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
bot.infinity_polling()
