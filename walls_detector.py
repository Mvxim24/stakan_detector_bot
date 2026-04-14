import ccxt
import time
import telebot
import json
import os

# --- НАСТРОЙКИ ---
TOKEN = '8726753006:AAGI8F1B63zi0UyqtMHN3nYg4UwJh6owFaY'
SYMBOLS = ['BTC/USDT', 'ETH/USDT']
WALL_MULTIPLIER = 15
USERS_FILE = 'users.json'

bot = telebot.TeleBot(TOKEN)
exchange = ccxt.binance()


# --- ФУНКЦИИ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ---

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_user(chat_id):
    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
        return True
    return False


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    if save_user(chat_id):
        bot.reply_to(message, "Вы подписались на сигналы по стакану! 🐋")
    else:
        bot.reply_to(message, "Вы уже в списке подписчиков.")


# --- ЛОГИКА СКАНЕРА ---

def check_order_book():
    users = load_users()
    if not users:
        print("Подписчиков пока нет. Жду нажатия /start в боте...")
        return

    for symbol in SYMBOLS:
        try:
            ob = exchange.fetch_order_book(symbol, limit=50)
            for side in ['bids', 'asks']:
                orders = ob[side]
                if not orders: continue

                volumes = [o[1] for o in orders]
                avg_volume = sum(volumes) / len(volumes)

                for price, volume in orders:
                    if volume > avg_volume * WALL_MULTIPLIER:
                        side_name = "🟢 ПОКУПКА" if side == 'bids' else "🔴 ПРОДАЖА"
                        msg = (f"🐋 **СТЕНКА ОБНАРУЖЕНА!**\n\n"
                               f"**Пара:** {symbol}\n"
                               f"**Тип:** {side_name}\n"
                               f"**Цена:** {price}\n"
                               f"**Объем:** {round(volume, 2)}")

                        # Рассылка всем пользователям
                        for user_id in users:
                            try:
                                bot.send_message(user_id, msg, parse_mode='Markdown')
                            except Exception as send_error:
                                print(f"Не удалось отправить пользователю {user_id}: {send_error}")

                        # Небольшая пауза, чтобы не спамить в одну секунду
                        time.sleep(1)

        except Exception as e:
            print(f"Ошибка анализа {symbol}: {e}")


# Запуск прослушивания команд /start в фоновом потоке
import threading

threading.Thread(target=bot.infinity_polling).start()

print("Детектор и рассылка запущены...")
while True:
    check_order_book()
    time.sleep(20)
