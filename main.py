import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. CONNECTION & BOT SETUP ---
# Render pulls the token from your Environment Variables
API_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN, threaded=False)

# --- 2. THE WEB SERVER (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Baron AI Engine: Running 24/7"

def run():
    # Render uses port 10000 or the PORT env variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 3. THE MATHEMATICAL ENGINE (4-Deck American Rules) ---
user_data = {}

def get_best_move(player_hand, dealer_card):
    total = sum(player_hand)
    has_ace = 11 in player_hand
    is_pair = len(player_hand) == 2 and player_hand[0] == player_hand[1]

    # --- SPLIT LOGIC ---
    if is_pair:
        val = player_hand[0]
        if val in [8, 11]: return "🔥 SPLIT (Always split Aces & 8s)"
        if val in [2, 3, 7] and dealer_card <= 7: return "🔥 SPLIT"
        if val == 6 and dealer_card <= 6: return "🔥 SPLIT"
        if val == 4 and dealer_card in [5, 6]: return "🔥 SPLIT"
        if val == 9 and dealer_card not in [7, 10, 11]: return "🔥 SPLIT"

    # --- SOFT TOTALS (With Ace) ---
    if has_ace:
        if total >= 19: return "✋ STAND"
        if total == 18: 
            return "✋ STAND" if dealer_card <= 8 else "🃏 HIT"
        if total == 17 and dealer_card in [3, 4, 5, 6]: return "💰 DOUBLE"
        if total in [15, 16] and dealer_card in [4, 5, 6]: return "💰 DOUBLE"
        if total in [13, 14] and dealer_card in [5, 6]: return "💰 DOUBLE"
        return "🃏 HIT"

    # --- HARD TOTALS ---
    if total >= 17: return "✋ STAND"
    if total <= 8: return "🃏 HIT"
    if total == 11: return "💰 DOUBLE"
    if total == 10 and dealer_card <= 9: return "💰 DOUBLE"
    if total == 9 and dealer_card in [3, 4, 5, 6]: return "💰 DOUBLE"
    
    if 12 <= total <= 16:
        if dealer_card <= 6:
            if total == 12 and dealer_card in [2, 3]: return "🃏 HIT"
            return "✋ STAND"
        else:
            return "🃏 HIT"
            
    return "🃏 HIT"

# --- 4. TELEGRAM INTERFACE ---
@bot.message_handler(commands=['start', 'blackjack'])
def start(message):
    user_data[message.chat.id] = {'player': [], 'dealer': None}
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    btns = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    markup.add(*[types.KeyboardButton(b) for b in btns])
    bot.send_message(message.chat.id, "🦅 **BARON AI ENGINE: ONLINE**\nSelect your 1st card:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_input(message):
    chat_id = message.chat.id
    val = 11 if message.text == 'A' else (10 if message.text in ['J', 'Q', 'K'] else int(message.text))
    
    # Reset if a new game starts accidentally
    if chat_id not in user_data or (len(user_data[chat_id]['player']) >= 2 and user_data[chat_id]['dealer'] is not None):
        user_data[chat_id] = {'player': [], 'dealer': None}

    data = user_data[chat_id]
    if len(data['player']) < 2:
        data['player'].append(val)
        msg = "Select your 2nd card:" if len(data['player']) == 1 else "Select DEALER'S up-card:"
        bot.send_message(chat_id, msg)
    elif data['dealer'] is None:
        data['dealer'] = val
        move = get_best_move(data['player'], data['dealer'])
        res = (f"📊 **BARON ANALYSIS**\n"
               f"━━━━━━━━━━━━━\n"
               f"Your Total: {sum(data['player'])}\n"
               f"Dealer Card: {message.text}\n"
               f"━━━━━━━━━━━━━\n"
               f"👉 **{move}**")
        bot.send_message(chat_id, res, parse_mode="Markdown")
        user_data[chat_id] = {'player': [], 'dealer': None}
        bot.send_message(chat_id, "Ready for next round! Select 1st card:")

# --- 5. RUN ---
if __name__ == "__main__":
    keep_alive()
    print("Baron Bot is now hunting...")
    bot.infinity_polling()
