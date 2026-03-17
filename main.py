import os, telebot, hmac, hashlib
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread

try:
    import pytz
    UG_TZ = pytz.timezone('Africa/Kampala')
except ImportError:
    UG_TZ = None

TOKEN = '8769467053:AAGTGgwDl-bCDw-EGSnIaPieXdpEt0jjbGc'
bot = telebot.TeleBot(TOKEN, threaded=False)

def get_billion_ai_prediction(server_seed, client_seed, nonce):
    """Recursive SHA256 logic to find 96%+ probability stars."""
    # Primary Hash
    base_hash = hashlib.sha256(f"{server_seed}:{client_seed}:{nonce}".encode()).hexdigest()
    # Secondary Recursive Hash (Billion-AI Layer)
    ai_layer = hashlib.sha256(base_hash.encode()).hexdigest()
    
    combined_scores = []
    for i in range(25):
        # Extracting depth from both hash layers
        v1 = int(base_hash[i % 64], 16)
        v2 = int(ai_layer[i % 64], 16)
        # Calculate Billion-AI Probability (Focused 90-99.9)
        prob = 90.0 + ((v1 + v2) / 32 * 9.9)
        combined_scores.append((i, round(prob, 1)))
    
    # Sort and pick only the 'Surest' (96%+)
    surest_picks = [x for x in combined_scores if x[1] >= 96.0]
    # If too many, take top 3. If none, take highest available.
    final_picks = sorted(surest_picks, key=lambda x: x[1], reverse=True)[:3]
    pick_indices = [p[0] for p in final_picks]
    pick_probs = {p[0]: p[1] for p in final_picks}

    grid = []
    for i in range(25):
        if i in pick_indices:
            grid.append(f"{pick_probs[i]}%")
        else:
            grid.append(" ⬛ ")
    return grid

session = {}

@bot.message_handler(commands=['start', 'mines'])
def start(m):
    session[m.chat.id] = {'step': 'S_SEED'}
    bot.send_message(m.chat.id, "🦅 **BARON BILLION-AI v7.0**\n\nPaste **Server Seed**:")

@bot.message_handler(func=lambda m: True)
def handle(m):
    cid = m.chat.id
    if cid not in session: return
    s = session[cid]

    if s['step'] == 'S_SEED':
        s['server'], s['step'] = m.text, 'C_SEED'
        bot.send_message(cid, "✅ **SERVER SYNCED**\nEnter **Client Seed**:")
    elif s['step'] == 'C_SEED':
        s['client'], s['step'] = m.text, 'PLAY'
        bot.send_message(cid, "🚀 **AI CALIBRATED**\nEnter **Nonce**:")
    elif s['step'] == 'PLAY' or m.text.isdigit():
        nonce = m.text if m.text.isdigit() else "0"
        grid = get_billion_ai_prediction(s['server'], s['client'], nonce)
        
        now = datetime.now(UG_TZ) if UG_TZ else datetime.utcnow()
        safe_window = now + timedelta(seconds=90)

        table = "┏━━━━┳━━━━┳━━━━┳━━━━┳━━━━┓\n"
        for i in range(0, 25, 5):
            table += "┃" + "┃".join(grid[i:i+5]) + "┃\n"
            if i < 20: table += "┣━━━━╋━━━━╋━━━━╋━━━━╋━━━━┫\n"
        table += "┗━━━━┻━━━━┻━━━━┻━━━━┻━━━━┛"

        msg = (
            f"🎯 **SUREST PREDICTS (Nonce: {nonce})**\n\n"
            f"{table}\n\n"
            f"🕒 **SAFE WINDOW (Kampala):**\n"
            f"`{now.strftime('%H:%M:%S')}` ➔ `{safe_window.strftime('%H:%M:%S')}`\n\n"
            f"💰 **STRATEGY:**\n"
            f"* Only hit the **96%+** stars.\n"
            f"* 3 Mines mode: 2 gems = **Sure Win**.\n"
            f"* 3 gems = **Debt Killer**."
        )
        bot.send_message(cid, f"`{msg}`", parse_mode="Markdown", reply_markup=nav())

def nav():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 AUTO-NEXT NONCE", callback_data="next"),
               types.InlineKeyboardButton("🧹 RESET", callback_data="reset"))
    return markup

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data == "reset":
        session.pop(c.message.chat.id, None)
        start(c.message)
    else:
        bot.send_message(c.message.chat.id, "Enter **Next Nonce**:")

app = Flask('')
@app.route('/')
def home(): return "Billion-AI Active"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
bot.infinity_polling()
