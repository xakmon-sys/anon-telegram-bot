import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import os

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
    
    welcome_text = (
        "✨ **Ласкаво просимо до Анонімного Чату!** ✨\n\n"
        "Спілкуйся з випадковими людьми повністю інкогніто.\n\n"
        "📜 **Правила:**\n"
        "• Твій юзернейм приховано.\n"
        "• Натискай кнопку нижче для пошуку."
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"status": "idle", "partner": None}
    if users_db[user_id]["status"] == "chat":
        await message.answer("Ви вже в чаті!")
        return
        
    users_db[user_id]["status"] = "search"
    await message.answer("🔎 Шукаю співрозмовника...", reply_markup=types.ReplyKeyboardRemove())
    
    for partner_id, data in users_db.items():
        if partner_id != user_id and data["status"] == "search":
            users_db[user_id]["status"] = "chat"
            users_db[user_id]["partner"] = partner_id
            users_db[partner_id]["status"] = "chat"
            users_db[partner_id]["partner"] = user_id
            
            await bot.send_message(user_id, "🎉 Знайдено! Напиши щось.\n\n/report — скарга.", reply_markup=get_chat_menu())
            await bot.send_message(partner_id, "🎉 Знайдено! Напиши щось.\n\n/report — скарга.", reply_markup=get_chat_menu())
            return

async def disconnect_users(user_id):
    partner_id = users_db[user_id]["partner"]
    users_db[user_id]["status"] = "idle"
    users_db[user_id]["partner"] = None
    if partner_id:
        users_db[partner_id]["status"] = "idle"
        users_db[partner_id]["partner"] = None
        try:
            await bot.send_message(partner_id, "🛑 Співрозмовник завершив розмову.", reply_markup=get_main_menu())
        except: pass

@dp.message(F.text.in_({"🛑 Зупинити чат", "/stop"}))
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        await disconnect_users(user_id)
        await message.answer("Ви вийшли з чату.", reply_markup=get_main_menu())
    else:
        await message.answer("Ви зараз не в чаті.")

@dp.message(F.text == "⏭ Наступний (Next)")
async def next_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        await disconnect_users(user_id)
    await start_search(message)

@dp.message(Command("report"))
async def report_user(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        bad_user_id = users_db[user_id]["partner"]
        try:
            await bot.send_message(ADMIN_ID, f"⚠️ СКАРГА від {user_id} на `{bad_user_id}`.")
        except: pass
        await message.answer("🚨 Скаргу надіслано.")

@dp.message()
async def forward_to_partner(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db or users_db[user_id]["status"] != "chat":
        await message.answer("Натисни кнопку нижче, щоб знайти друга! 👇", reply_markup=get_main_menu())
        return
    partner_id = users_db[user_id]["partner"]
    try:
        await message.copy_to(chat_id=partner_id)
    except:
        await message.answer("❌ Повідомлення не доставлено.")
        await disconnect_users(user_id)

async def main():
    from aiohttp import web
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
