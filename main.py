import telebot
from telebot import types

# --- THE BRAIN (New Token) ---
TOKEN = '8320085836:AAGUv9vJOLGGGt4X-vOX7bLIgGZoBziyzSY'
bot = telebot.TeleBot(TOKEN)

# --- BLACKJACK MATHEMATICAL ENGINE ---
user_states = {}

def get_decision(player_cards, dealer_card):
    total = sum(player_cards)
    has_ace = 11 in player_cards
    is_pair = len(player_cards) == 2 and player_cards[0] == player_cards[1]

    # 1. SPLIT LOGIC
    if is_pair:
        val = player_cards[0]
        if val in [8, 11]: return "🔥 SPLIT"
        if val in [2, 3, 7] and dealer_card <= 7: return "🔥 SPLIT"
        if val == 6 and dealer_card <= 6: return "🔥 SPLIT"
        if val == 9 and dealer_card not in [7, 10, 11]: return "🔥 SPLIT"

    # 2. SOFT TOTALS (With Ace)
    if has_ace:
        if total >= 19: return "✋ STAND"
        if total == 18: return "✋ STAND" if dealer_card <= 8 else "🃏 HIT"
        return "🃏 HIT"

    # 3. HARD TOTALS
    if total >= 17: return "✋ STAND"
    if total <= 8: return "🃏 HIT"
    if total == 11: return "💰 DOUBLE"
    if total == 10 and dealer_card <= 9: return "💰 DOUBLE"
    if 12 <= total <= 16:
        return "✋ STAND" if dealer_card <= 6 else "🃏 HIT"
            
    return "🃏 HIT"

# --- TELEGRAM INTERFACE ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user_states[message.chat.id] = {'hand': [], 'dealer': None}
    markup = types.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    markup.add(*[types.KeyboardButton(c) for c in cards])
    bot.send_message(message.chat.id, "🦅 **BARON AI ENGINE: ONLINE**\nSelect your 1st card:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_cards(message):
    cid = message.chat.id
    if cid not in user_states:
        user_states[cid] = {'hand': [], 'dealer': None}
    
    # Simple check to see if input is a card
    text = message.text
    if text not in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']:
        return

    val = 11 if text == 'A' else (10 if text in ['J', 'Q', 'K'] else int(text))
    state = user_states[cid]

    if len(state['hand']) < 2:
        state['hand'].append(val)
        msg = "Select your 2nd card:" if len(state['hand']) == 1 else "Select DEALER'S up-card:"
        bot.send_message(cid, msg)
    elif state['dealer'] is None:
        state['dealer'] = val
        move = get_decision(state['hand'], state['dealer'])
        
        # Result Output
        bot.send_message(cid, f"📊 **DECISION**\n👉 **{move}**", parse_mode="Markdown")
        
        # Immediate Reset for Fast Play
        user_states[cid] = {'hand': [], 'dealer': None}
        bot.send_message(cid, "--- NEXT ROUND ---\nSelect 1st card:")

# --- START UP ---
if __name__ == "__main__":
    print("Baron is starting up...")
    bot.infinity_polling()
