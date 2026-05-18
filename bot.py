import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

# Токен твого бота та ID адміністратора
BOT_TOKEN = "8724564645:AAFK2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"
ADMIN_ID = "6109923832"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
users_db = {}

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Наступний (Next)"))
    builder.add(types.KeyboardButton(text="🛑 Зупинити чат"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"status": "idle", "partner": None}
    welcome_text = "✨ **Ласкаво просимо до Анонімного Чату!** ✨\n\nСпілкуйся інкогніто."
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.message(F.text == "🔍 Знайти співрозмовника")
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
    return web.Response(text="Bot is running smoothly!")

async def main():
    # Налаштування веб-сервера під порт Render
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматично видає PORT, якщо його немає — беремо 10000
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    # Запуск довгого опитування бота (Long Polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
