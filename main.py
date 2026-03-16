import telebot
from telebot import types
import os
from flask import Flask
from threading import Thread

# --- 1. THE BRAIN (Your Token) ---
TOKEN = '8668197678:AcbXX3KgvqD7B8Y4WjCu6yNx1Prfu5cNHz'
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- 2. THE SIMPLIFIED WEB SERVER ---
# This part is ONLY to keep Render happy. 
# It runs on a separate thread so it doesn't touch the bot.
server = Flask('')

@server.route('/')
def health_check():
    return "Baron AI is Online"

def run_server():
    # Render looks for port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port)

# --- 3. BLACKJACK MATHEMATICAL ENGINE ---
user_states = {}

def get_decision(player_cards, dealer_card):
    total = sum(player_cards)
    has_ace = 11 in player_cards
    is_pair = len(player_cards) == 2 and player_cards[0] == player_cards[1]

    # Split Logic
    if is_pair:
        val = player_cards[0]
        if val in [8, 11]: return "🔥 SPLIT"
        if val in [2, 3, 7] and dealer_card <= 7: return "🔥 SPLIT"
        if val == 6 and dealer_card <= 6: return "🔥 SPLIT"
        if val == 9 and dealer_card not in [7, 10, 11]: return "🔥 SPLIT"

    # Soft Totals (Aces)
    if has_ace:
        if total >= 19: return "✋ STAND"
        if total == 18: return "✋ STAND" if dealer_card <= 8 else "🃏 HIT"
        return "🃏 HIT"

    # Hard Totals
    if total >= 17: return "✋ STAND"
    if total <= 8: return "🃏 HIT"
    if total == 11: return "💰 DOUBLE"
    if total == 10 and dealer_card <= 9: return "💰 DOUBLE"
    if 12 <= total <= 16:
        return "✋ STAND" if dealer_card <= 6 else "🃏 HIT"
            
    return "🃏 HIT"

# --- 4. TELEGRAM COMMANDS ---
@bot.message_handler(commands=['start', 'blackjack'])
def welcome(message):
    user_states[message.chat.id] = {'hand': [], 'dealer': None}
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    markup.add(*[types.KeyboardButton(c) for c in cards])
    bot.send_message(message.chat.id, "🦅 **BARON AI ENGINE ACTIVE**\nSelect your FIRST card:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    cid = message.chat.id
    if cid not in user_states:
        user_states[cid] = {'hand': [], 'dealer': None}
    
    # Card value conversion
    val = 11 if message.text == 'A' else (10 if message.text in ['J', 'Q', 'K'] else int(message.text))
    state = user_states[cid]

    if len(state['hand']) < 2:
        state['hand'].append(val)
        if len(state['hand']) == 1:
            bot.send_message(cid, "Select your SECOND card:")
        else:
            bot.send_message(cid, "Select DEALER'S up-card:")
    elif state['dealer'] is None:
        state['dealer'] = val
        move = get_decision(state['hand'], state['dealer'])
        
        # Format Result
        output = f"📊 **STRATEGY**\nTotal: {sum(state['hand'])}\nDealer: {message.text}\n\n👉 **{move}**"
        bot.send_message(cid, output, parse_mode="Markdown")
        
        # Instant Reset for Next Round
        user_states[cid] = {'hand': [], 'dealer': None}
        bot.send_message(cid, "--- NEW ROUND ---\nSelect 1st card:")

# --- 5. START UP ---
if __name__ == "__main__":
    # Start server in background
    Thread(target=run_server).start()
    print("Baron Bot is starting...")
    # Start bot in foreground
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
