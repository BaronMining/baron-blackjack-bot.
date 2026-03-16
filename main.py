import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. THE BRAIN (Your Token) ---
TOKEN = '8320085836:AAGUv9vJOLGGGt4X-vOX7bLIgGZoBziyzSY'
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- 2. THE WEB SERVER (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Baron AI Status: ACTIVE"

def run_server():
    # This line automatically finds the port Render wants
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 3. THE MATHEMATICAL ENGINE ---
user_states = {}

def get_decision(player_cards, dealer_card):
    total = sum(player_cards)
    has_ace = 11 in player_cards
    is_pair = len(player_cards) == 2 and player_cards[0] == player_cards[1]

    if is_pair:
        val = player_cards[0]
        if val in [8, 11]: return "🔥 SPLIT"
        if val in [2, 3, 7] and dealer_card <= 7: return "🔥 SPLIT"
        if val == 6 and dealer_card <= 6: return "🔥 SPLIT"
        if val == 9 and dealer_card not in [7, 10, 11]: return "🔥 SPLIT"

    if has_ace:
        if total >= 19: return "✋ STAND"
        if total == 18: return "✋ STAND" if dealer_card <= 8 else "🃏 HIT"
        return "🃏 HIT"

    if total >= 17: return "✋ STAND"
    if total <= 8: return "🃏 HIT"
    if total == 11: return "💰 DOUBLE"
    if total == 10 and dealer_card <= 9: return "💰 DOUBLE"
    if 12 <= total <= 16:
        return "✋ STAND" if dealer_card <= 6 else "🃏 HIT"
    return "🃏 HIT"

# --- 4. TELEGRAM COMMANDS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user_states[message.chat.id] = {'hand': [], 'dealer': None}
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    markup.add(*[types.KeyboardButton(c) for c in cards])
    bot.send_message(message.chat.id, "🦅 **BARON ENGINE READY**\nSelect your 1st card:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    cid = message.chat.id
    if cid not in user_states:
        user_states[cid] = {'hand': [], 'dealer': None}
    
    if message.text not in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']:
        return

    val = 11 if message.text == 'A' else (10 if message.text in ['J', 'Q', 'K'] else int(message.text))
    state = user_states[cid]

    if len(state['hand']) < 2:
        state['hand'].append(val)
        msg = "Select 2nd card:" if len(state['hand']) == 1 else "Select DEALER card:"
        bot.send_message(cid, msg)
    elif state['dealer'] is None:
        state['dealer'] = val
        move = get_decision(state['hand'], state['dealer'])
        bot.send_message(cid, f"📊 **DECISION**\n👉 **{move}**", parse_mode="Markdown")
        user_states[cid] = {'hand': [], 'dealer': None} 
        bot.send_message(cid, "--- NEXT ROUND ---\nSelect 1st card:")

# --- 5. EXECUTION ---
if __name__ == "__main__":
    # Start the web server so Render stays happy
    Thread(target=run_server).start()
    print("Baron is starting...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
