import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

BOT_TOKEN = "8724564645:AAFK2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"
ADMIN_ID = 6109923832

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
users_db = {}

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"))
    return markup

def get_chat_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton(text="⏭ Наступний (Next)"), types.KeyboardButton(text="🛑 Зупинити чат"))
    return markup

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"status": "idle", "partner": None}
    welcome_text = "✨ **Ласкаво просимо до Анонімного Чату!** ✨\n\nСпілкуйся інкогніто."
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "🔍 Знайти співрозмовника")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    users_db[user_id] = {"status": "search", "partner": None}
    await message.answer("🔎 Шукаю співрозмовника...")
    for partner_id, data in users_db.items():
        if partner_id != user_id and data["status"] == "search":
            users_db[user_id].update({"status": "chat", "partner": partner_id})
            users_db[partner_id].update({"status": "chat", "partner": user_id})
            await bot.send_message(user_id, "🎉 Знайдено співрозмовника!", reply_markup=get_chat_menu())
            await bot.send_message(partner_id, "🎉 Знайдено співрозмовника!", reply_markup=get_chat_menu())
            return

async def handle_web(request):
    return web.Response(text="Bot is running!")

# Запуск простого веб-сервера для Render
app = web.Application()
app.router.add_get("/", handle_web)

if __name__ == "__main__":
    # Запускаємо веб-сервер у фоні
    loop = asyncio.get_event_loop()
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    loop.run_until_complete(site.start())
    
    # Запускаємо самого бота
    executor.start_polling(dp, skip_updates=True)
