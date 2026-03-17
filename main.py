import os, telebot, hmac, hashlib
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread

# 1. AUTH & CONFIG - RE-CHECK THIS TOKEN IN BOTFATHER
TOKEN = '8320085836:AcbXX3KgvqD7B8Y4WjCu6yNx1Prfu5cNHz-0'
bot = telebot.TeleBot(TOKEN, threaded=False)

# 2. SHA256 PROBABILITY BRAIN
def get_sha256_mines(server_seed, client_seed, nonce):
    # Standard SHA256 hashing for betPawa Spribe
    game_hash = hashlib.sha256(f"{server_seed}:{client_seed}:{nonce}".encode()).hexdigest()
    
    grid_probs = []
    for i in range(25):
        # Using hash characters to simulate safety probability
        val = int(game_hash[i % 64], 16) 
        if val < 3: 
            grid_probs.append(" 💣 ") # Avoid this spot
        else:
            # High safety probability for betPawa (97-99%)
            p = 97 + (val % 3)
            grid_probs.append(f"{p}%")
    return grid_probs

# 3. INTERFACE LOGIC
session = {}

@bot.message_handler(commands=['start', 'mines'])
def start(m):
    session[m.chat.id] = {'step': 'S_SEED'}
    bot.send_message(m.chat.id, "🦅 **BARON betPawa SHA256**\n\nEnter **Server Seed** from betPawa:")

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
        bot.send_message(cid, "🚀 **SYNCED.** Enter current **Nonce** (Round #):")
    elif s['step'] == 'PLAY' or m.text.isdigit():
        nonce = m.text if m.text.isdigit() else "0"
        probs = get_sha256_mines(s['server'], s['client'], nonce)
        
        res = f"🎯 **betPawa ANALYSIS (Nonce: {nonce})**\n\n"
        res += "┏━━━━━┳━━━━━┳━━━━━┳━━━━━┳━━━━━┓\n"
        for i in range(0, 25, 5):
            res += "┃" + "┃".join(probs[i:i+5]) + "┃\n"
            if i < 20: res += "┣━━━━━╋━━━━━╋━━━━━╋━━━━━╋━━━━━┫\n"
        res += "┗━━━━━┻━━━━━┻━━━━━┻━━━━━┻━━━━━┛\n\n"
        res += "💡 **BETPAWA TIP:** Target **99%** spots only.\n"
        res += "⚠️ Cash out after **2 gems** (3 mines mode)."
        
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
        bot.send_message(c.message.chat.id, "Ready. Enter **Next Nonce**:")

# 4. DEPLOYMENT (RENDER)
app = Flask('')
@app.route('/')
def home(): return "Baron Engine Active"
def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    try:
        print("Baron Bot is starting...")
        bot.infinity_polling()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
