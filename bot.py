import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Ваш токен
BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База даних в пам'яті
users_db = {}

# --- КНОПКИ ---
def get_kb(buttons):
    builder = ReplyKeyboardBuilder()
    for b in buttons: builder.add(types.KeyboardButton(text=b))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# --- ЛОГІКА ---
@dp.message(Command("start"))
async def start(message: types.Message):
    users_db[message.from_user.id] = {"status": "idle", "partner": None}
    await message.answer("Привіт! Натисни кнопку, щоб знайти пару.", 
                         reply_markup=get_kb(["🔍 Знайти пару"]))

@dp.message(F.text == "🔍 Знайти пару")
async def find_partner(message: types.Message):
    user_id = message.from_user.id
    users_db[user_id]["status"] = "search"
    
    # Шукаємо іншого користувача зі статусом search
    for pid, data in users_db.items():
        if pid != user_id and data["status"] == "search":
            # З'єднуємо
            users_db[user_id].update({"status": "chat", "partner": pid})
            data.update({"status": "chat", "partner": user_id})
            
            # Повідомляємо обох
            await bot.send_message(user_id, "✅ Знайдено! Можеш писати.", reply_markup=get_kb(["🛑 Зупинити"]))
            await bot.send_message(pid, "✅ Знайдено! Можеш писати.", reply_markup=get_kb(["🛑 Зупинити"]))
            return
            
    await message.answer("🔎 Шукаю... зачекай секунду.")

@dp.message(F.text == "🛑 Зупинити")
async def stop_chat(message: types.Message):
    user = users_db.get(message.from_user.id)
    if user and user["status"] == "chat":
        partner_id = user["partner"]
        user.update({"status": "idle", "partner": None})
        
        if partner_id in users_db:
            users_db[partner_id].update({"status": "idle", "partner": None})
            await bot.send_message(partner_id, "❌ Співрозмовник вийшов.", reply_markup=get_kb(["🔍 Знайти пару"]))
            
    await message.answer("🛑 Чат завершено.", reply_markup=get_kb(["🔍 Знайти пару"]))

@dp.message()
async def chat_forward(message: types.Message):
    user = users_db.get(message.from_user.id)
    if user and user["status"] == "chat" and user["partner"]:
        try:
            await bot.copy_message(user["partner"], message.chat.id, message.message_id)
        except: pass

async def main():
    # Очищуємо "завислі" запити
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
