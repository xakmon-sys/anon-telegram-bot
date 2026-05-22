import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_db = {}

# --- КЛАВІАТУРИ ---
def get_kb(buttons, adjust=1):
    builder = ReplyKeyboardBuilder()
    for text in buttons:
        builder.add(types.KeyboardButton(text=text))
    builder.adjust(adjust)
    return builder.as_markup(resize_keyboard=True)

# --- ЛОГІКА ---
@dp.message(Command("start"))
async def start(message: types.Message):
    users_db[message.from_user.id] = {"status": "idle", "gender": None, "pref": "any", "topic": "normal", "partner": None}
    await message.answer("✨ Обери свою стать:", reply_markup=get_kb(["👨 Я Хлопець", "👩 Я Дівчина"], 2))

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):
    if message.from_user.id not in users_db: return
    users_db[message.from_user.id]["gender"] = "male" if "Хлопець" in message.text else "female"
    await message.answer("✅ Готово! Шукай співрозмовника.", reply_markup=get_kb(["🔍 Знайти співрозмовника", "📊 Онлайн"]))

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def search_menu(message: types.Message):
    await message.answer("Кого шукаємо?", reply_markup=get_kb(["🙋‍♂️ Хлопця", "🙋‍♀️ Дівчину", "🌍 Будь-кого", "⬅️ Назад"], 2))

@dp.message(F.text.in_(["🙋‍♂️ Хлопця", "🙋‍♀️ Дівчину", "🌍 Будь-кого"]))
async def choose_topic(message: types.Message):
    pref = {"🙋‍♂️ Хлопця": "male", "🙋‍♀️ Дівчину": "female", "🌍 Будь-кого": "any"}[message.text]
    users_db[message.from_user.id]["pref"] = pref
    await message.answer("🎭 Обери тему:", reply_markup=get_kb(["💬 Звичайне", "❤️ Флірт"]))

@dp.message(F.text.in_(["💬 Звичайне", "❤️ Флірт"]))
async def start_search(message: types.Message):
    user_id = message.from_user.id
    user = users_db[user_id]
    user["topic"] = "flirt" if "Флірт" in message.text else "normal"
    user["status"] = "search"
    
    await message.answer("🔎 Пошук...", reply_markup=types.ReplyKeyboardRemove())
    
    for pid, partner in users_db.items():
        if pid != user_id and partner["status"] == "search" and partner["topic"] == user["topic"]:
            # Перевірка преференцій
            if (user["pref"] == "any" or user["pref"] == partner["gender"]) and \
               (partner["pref"] == "any" or partner["pref"] == user["gender"]):
                
                user.update({"status": "chat", "partner": pid})
                partner.update({"status": "chat", "partner": user_id})
                
                await bot.send_message(user_id, "🎉 Знайдено!", reply_markup=get_kb(["⏭ Next", "🛑 Зупинити"]))
                await bot.send_message(pid, "🎉 Знайдено!", reply_markup=get_kb(["⏭ Next", "🛑 Зупинити"]))
                return

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    user = users_db.get(message.from_user.id)
    if user and user["status"] == "chat":
        partner_id = user["partner"]
        user.update({"status": "idle", "partner": None})
        if partner_id in users_db:
            users_db[partner_id].update({"status": "idle", "partner": None})
            await bot.send_message(partner_id, "❌ Співрозмовник вийшов.", reply_markup=get_kb(["🔍 Знайти співрозмовника"]))
        await message.answer("🛑 Чат завершено.", reply_markup=get_kb(["🔍 Знайти співрозмовника"]))

@dp.message()
async def forwarder(message: types.Message):
    user = users_db.get(message.from_user.id)
    if user and user["status"] == "chat" and user["partner"]:
        try:
            await bot.copy_message(user["partner"], message.chat.id, message.message_id)
        except: pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
