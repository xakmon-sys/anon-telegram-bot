import asyncio
import logging
import os
import random
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

# Токен беремо зі змінних середовища для безпеки
BOT_TOKEN = os.getenv("BOT_TOKEN", "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_db = {}
chat_start_times = {}

# --- КЛАВІАТУРИ ---

def get_gender_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👨 Я Хлопець"), types.KeyboardButton(text="👩 Я Дівчина"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"), 
                types.KeyboardButton(text="📊 Онлайн"), 
                types.KeyboardButton(text="ℹ️ Правила"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Next"), types.KeyboardButton(text="🛑 Зупинити чат"),
                types.KeyboardButton(text="🎲 Грати в кубик"), types.KeyboardButton(text="✨ Комплімент"),
                types.KeyboardButton(text="⚠️ Скаржитися"))
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# --- ЛОГІКА БОТА ---

@dp.message(Command("start"))
async def start(message: types.Message):
    users_db[message.from_user.id] = {"status": "gender_select", "gender": None, "partner": None, "topic": "normal"}
    await message.answer("✨ Привіт! Обери свою стать:", reply_markup=get_gender_menu())

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):
    users_db[message.from_user.id].update({"gender": "male" if "Хлопець" in message.text else "female", "status": "idle"})
    await message.answer("✅ Дані збережено! Готовий до пошуку.", reply_markup=get_main_menu())

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    users_db[user_id]["status"] = "search"
    await message.answer("🔎 Шукаємо співрозмовника...", reply_markup=types.ReplyKeyboardRemove())
    
    # Спроба знайти партнера
    for pid, partner in users_db.items():
        if pid != user_id and partner["status"] == "search":
            users_db[user_id].update({"status": "chat", "partner": pid})
            users_db[pid].update({"status": "chat", "partner": user_id})
            chat_start_times[user_id] = chat_start_times[pid] = time.time()
            for uid in [user_id, pid]:
                await bot.send_message(uid, "🎉 Співрозмовника знайдено! Починайте спілкування.", reply_markup=get_chat_menu())
            return

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    partner_id = users_db[user_id].get("partner")
    
    start_time = chat_start_times.get(user_id, time.time())
    duration = int(time.time() - start_time)
    
    await message.answer(f"🛑 Чат завершено. Час: {duration // 60}хв {duration % 60}сек.", reply_markup=get_main_menu())
    if partner_id:
        users_db[partner_id].update({"status": "idle", "partner": None})
        await bot.send_message(partner_id, "❌ Співрозмовник завершив чат.", reply_markup=get_main_menu())
    
    users_db[user_id].update({"status": "idle", "partner": None})

@dp.message(F.text == "🎲 Грати в кубик")
async def play_dice(message: types.Message):
    partner_id = users_db[message.from_user.id].get("partner")
    if partner_id:
        dice = await message.answer_dice()
        await bot.send_message(partner_id, f"🎲 Співрозмовник кинув кубик: {dice.dice.value}")

@dp.message(F.text == "✨ Комплімент")
async def compliment(message: types.Message):
    comps = ["Ти супер!", "У тебе чудовий смак!", "З тобою приємно розмовляти!"]
    await message.answer(random.choice(comps))

@dp.message()
async def forwarder(message: types.Message):
    user_id = message.from_user.id
    if users_db.get(user_id, {}).get("status") == "chat":
        partner_id = users_db[user_id]["partner"]
        if message.text: await bot.send_message(partner_id, message.text)
        elif message.photo: await bot.send_photo(partner_id, message.photo[-1].file_id)

# --- ВЕБ-СЕРВЕР (Для Render) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Порт для Render
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"Bot started on port {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
