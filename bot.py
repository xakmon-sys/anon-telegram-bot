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

    text = (
        "✨ <b>Ласкаво просимо в РОЗМОВА</b> ✨\n\n"
        "🔒 Повністю анонімний чат\n"
        "💬 Спілкування без реєстрації\n"
        "❤️ Пошук по темах\n\n"
        "👇 Обери свою стать"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_gender_menu()
    )

# =====================================================
# GENDER
# =====================================================

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):

    user_id = message.from_user.id

    if user_id not in users_db:
        return

    gender = "male"

    if "Дівчина" in message.text:
        gender = "female"

    users_db[user_id]["gender"] = gender
    users_db[user_id]["status"] = "idle"

    await message.answer(
        "✅ Дані збережено\n\nТепер можеш шукати співрозмовника 👇",
        reply_markup=get_main_menu()
    )

# =====================================================
# RULES
# =====================================================

@dp.message(F.text == "ℹ️ Правила")
async def rules(message: types.Message):

    text = (
        "📜 <b>Правила чату</b>\n\n"
        "🚫 Заборонено спам\n"
        "🚫 Заборонено образи\n"
        "🚫 Заборонено 18+ контент\n\n"
        "✅ Будь ввічливим\n"
        "✅ Поважай співрозмовника"
    )

    await message.answer(text, parse_mode="HTML")

# =====================================================
# ONLINE
# =====================================================

@dp.message(F.text == "📊 Онлайн")
async def stats(message: types.Message):

    total = len(users_db)

    searching = sum(
        1 for x in users_db.values()
        if x["status"] == "search"
    )

    chatting = sum(
        1 for x in users_db.values()
        if x["status"] == "chat"
    )

    text = (
        "📊 <b>Статистика РОЗМОВА</b>\n\n"
        f"👥 Онлайн: <b>{total}</b>\n"
        f"🔎 Шукають: <b>{searching}</b>\n"
        f"💬 В чаті: <b>{chatting}</b>"
    )

    await message.answer(text, parse_mode="HTML")

# =====================================================
# SEARCH MENU
# =====================================================

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def search_menu(message: types.Message):

    await message.answer(
        "👇 Кого шукаємо?",
        reply_markup=get_search_menu()
    )

# =====================================================
# SEARCH PREFERENCE
# =====================================================

@dp.message(F.text.in_([
    "🙋‍♂️ Шукаю Хлопця",
    "🙋‍♀️ Шукаю Дівчину",
    "🌍 Шукаю Будь-кого"
]))
async def choose_topic(message: types.Message):

    user_id = message.from_user.id

    if "Хлопця" in message.text:
        users_db[user_id]["search_preference"] = "male"

    elif "Дівчину" in message.text:
        users_db[user_id]["search_preference"] = "female"

    else:
        users_db[user_id]["search_preference"] = "any"

    await message.answer(
        "🎭 Обери тему спілкування",
        reply_markup=get_topic_menu()
    )

# =====================================================
# TOPIC SEARCH
# =====================================================

@dp.message(F.text.in_([
    "💬 Звичайне спілкування",
    "❤️ Флірт"
]))
async def start_search(message: types.Message):

    user_id = message.from_user.id

    user = users_db[user_id]

    topic = "normal"

    if "Флірт" in message.text:
        topic = "flirt"

    user["topic"] = topic
    user["status"] = "search"

    my_gender = user["gender"]
    my_pref = user["search_preference"]

    await message.answer(
        "🔎 Шукаємо ідеального співрозмовника...",
        reply_markup=types.ReplyKeyboardRemove()
    )

    for partner_id, partner in users_db.items():

        if partner_id == user_id:
            continue

        if partner["status"] != "search":
            continue

        # topic check
        if partner["topic"] != topic:
            continue

        partner_gender = partner["gender"]
        partner_pref = partner["search_preference"]

        # my preference
        if my_pref != "any":
            if partner_gender != my_pref:
                continue

        # partner preference
        if partner_pref != "any":
            if my_gender != partner_pref:
                continue

        # CONNECT
        user["status"] = "chat"
        user["partner"] = partner_id

        partner["status"] = "chat"
        partner["partner"] = user_id

        topic_name = "💬 Звичайне спілкування"

        if topic == "flirt":
            topic_name = "❤️ Флірт"

        await bot.send_message(
            user_id,
            f"🎉 Співрозмовника знайдено!\n\n{topic_name}",
            reply_markup=get_chat_menu()
        )

        await bot.send_message(
            partner_id,
            f"🎉 Співрозмовника знайдено!\n\n{topic_name}",
            reply_markup=get_chat_menu()
        )

        return

# =====================================================
# STOP CHAT
# =====================================================

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):

    user_id = message.from_user.id

    if user_id not in users_db:
        return

    user = users_db[user_id]

    if user["status"] != "chat":
        return

    partner_id = user["partner"]

    user["status"] = "idle"
    user["partner"] = None

    if partner_id:

        users_db[partner_id]["status"] = "idle"
        users_db[partner_id]["partner"] = None

        await bot.send_message(
            partner_id,
            "❌ Співрозмовник завершив чат",
            reply_markup=get_main_menu()
        )

    await message.answer(
        "🛑 Чат завершено",
        reply_markup=get_main_menu()
    )

# =====================================================
# NEXT
# =====================================================

@dp.message(F.text == "⏭ Next")
async def next_chat(message: types.Message):

    user_id = message.from_user.id

    if user_id not in users_db:
        return

    user = users_db[user_id]

    if user["status"] != "chat":
        return

    partner_id = user["partner"]

    if partner_id:

        users_db[partner_id]["status"] = "idle"
        users_db[partner_id]["partner"] = None

        await bot.send_message(
            partner_id,
            "⏭ Співрозмовник переключив чат",
            reply_markup=get_main_menu()
        )

    user["status"] = "idle"
    user["partner"] = None

    await message.answer(
        "🔍 Шукай нового співрозмовника 👇",
        reply_markup=get_search_menu()
    )

# =====================================================
# TYPING
# =====================================================

@dp.message(F.text == "👀 Хто друкує?")
async def typing_info(message: types.Message):

    await message.answer(
        "😄 Просто напиши щось і перевір"
    )

# =====================================================
# BACK
# =====================================================

@dp.message(F.text == "⬅️ Назад")
async def back(message: types.Message):

    user_id = message.from_user.id

    if user_id in users_db:
        users_db[user_id]["status"] = "idle"

    await message.answer(
        "🏠 Головне меню",
        reply_markup=get_main_menu()
    )

# =====================================================
# MESSAGE FORWARDER
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

        # typing status
        await bot.send_chat_action(
            partner_id,
            "typing"
        )

        # TEXT
        if message.text:
            await bot.send_message(
                partner_id,
                message.text
            )

        # PHOTO
        elif message.photo:
            await bot.send_photo(
                partner_id,
                message.photo[-1].file_id,
                caption=message.caption
            )

        # VIDEO
        elif message.video:
            await bot.send_video(
                partner_id,
                message.video.file_id,
                caption=message.caption
            )

        # VOICE
        elif message.voice:
            await bot.send_voice(
                partner_id,
                message.voice.file_id
            )

        # STICKERS
        elif message.sticker:
            await bot.send_sticker(
                partner_id,
                message.sticker.file_id
            )

        # GIF
        elif message.animation:
            await bot.send_animation(
                partner_id,
                message.animation.file_id
            )

    except Exception as e:

        logging.error(e)

# =====================================================
# WEB SERVER
# =====================================================

async def handle(request):

    return web.Response(text="ROZMOVA BOT ONLINE")

async def start_background(app):

    asyncio.create_task(
        dp.start_polling(bot)
    )

# =====================================================
# MAIN
# =====================================================

async def main():

    await bot.delete_webhook(drop_pending_updates=True)

    app = web.Application()

    app.router.add_get("/", handle)

    app.on_startup.append(start_background)

    port = int(os.getenv("PORT", 10000))

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print("BOT STARTED")

    await asyncio.Event().wait()

if __name__ == "__main__":

    asyncio.run(main())
