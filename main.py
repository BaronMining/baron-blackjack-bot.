import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. CONNECTION ---
TOKEN = '8320085836:AAGUv9vJOLGGGt4X-vOX7bLIgGZoBziyzSY'
bot = telebot.TeleBot(TOKEN, threaded=False)

# --- 2. WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Baron Multi-Hit Engine: ACTIVE"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 3. ADVANCED MULTI-HIT LOGIC ---
user_states = {}

def get_decision(player_cards, dealer_card):
    total = sum(player_cards)
    has_ace = 11 in player_cards
    is_pair = len(player_cards) == 2 and player_cards[0] == player_cards[1]

    if total > 21: return "💥 BUST (You Lose)"
    if total == 21: return "✋ STAND (21!)"

    # Split Logic (Only on first 2 cards)
    if is_pair:
        val = player_cards[0]
        if val in [8, 11]: return "🔥 SPLIT"
        if val in [2, 3, 7] and dealer_card <= 7: return "🔥 SPLIT"
        if val == 6 and dealer_card <= 6: return "🔥 SPLIT"
        if val == 9 and dealer_card not in [7, 10, 11]: return "🔥 SPLIT"

    # Soft Totals
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

# --- 4. TELEGRAM INTERFACE ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user_states[message.chat.id] = {'hand': [], 'dealer': None, 'status': 'PLAYER_CARDS'}
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    markup.add(*[types.KeyboardButton(c) for c in cards])
    bot.send_message(message.chat.id, "🦅 **BARON MULTI-HIT ENGINE**\nSelect your 1st card:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_game(message):
    cid = message.chat.id
    if cid not in user_states: welcome(message); return
    
    text = message.text
    if text not in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']: return
    val = 11 if text == 'A' else (10 if text in ['J', 'Q', 'K'] else int(text))
    
    state = user_states[cid]

    # Step 1: Get Player's first two cards
    if state['status'] == 'PLAYER_CARDS':
        state['hand'].append(val)
        if len(state['hand']) == 1:
            bot.send_message(cid, "Select your 2nd card:")
        else:
            state['status'] = 'DEALER_CARD'
            bot.send_message(cid, "Select DEALER'S up-card:")

    # Step 2: Get Dealer card and give first decision
    elif state['status'] == 'DEALER_CARD':
        state['dealer'] = val
        move = get_decision(state['hand'], state['dealer'])
        
        if "HIT" in move:
            state['status'] = 'WAITING_FOR_HIT'
            bot.send_message(cid, f"📊 **DECISION: {move}**\n\nWhat was the next card you received?")
        else:
            bot.send_message(cid, f"📊 **DECISION: {move}**\n\n--- ROUND OVER ---\nSelect 1st card for next round:")
            user_states[cid] = {'hand': [], 'dealer': None, 'status': 'PLAYER_CARDS'}

    # Step 3: Handle Hit results (3rd, 4th, 5th cards)
    elif state['status'] == 'WAITING_FOR_HIT':
        state['hand'].append(val)
        move = get_decision(state['hand'], state['dealer'])
        
        if "HIT" in move:
            bot.send_message(cid, f"📊 **NEW TOTAL: {sum(state['hand'])}\nDECISION: {move}**\n\nSelect your NEXT card:")
        else:
            bot.send_message(cid, f"📊 **FINAL TOTAL: {sum(state['hand'])}\nDECISION: {move}**\n\n--- ROUND OVER ---\nSelect 1st card:")
            user_states[cid] = {'hand': [], 'dealer': None, 'status': 'PLAYER_CARDS'}

# --- 5. START ---
if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
