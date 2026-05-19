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

# =========================
# ADMIN CONFIG
# =========================
ADMIN_ID = 342371504
admin_watch = {}

# =====================================================
# USERS DATABASE (RAM)
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

    text = (
        "✨ <b>Ласкаво просимо в РОЗМОВА</b> ✨\n\n"
        "🔒 Повністю анонімний чат\n"
        "💬 Спілкування без реєстрації\n"
        "❤️ Пошук по темах\n\n"
        "👇 Обери свою стать"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_gender_menu())

# =====================================================
# ADMIN COMMAND
# =====================================================
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 Адмін режим активний\n/ reply user_id текст")

@dp.message(Command("reply"))
async def admin_reply(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, uid, *txt = message.text.split()
        uid = int(uid)
        text = " ".join(txt)

        await bot.send_message(uid, f"👮 Адмін: {text}")
        await message.answer("✅ Sent")

    except:
        await message.answer("❌ /reply user_id text")

# =====================================================
# FORWARD + ADMIN LOG
# =====================================================
@dp.message()
async def forwarder(message: types.Message):

    user_id = message.from_user.id

    # admin log
    if user_id != ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"📩 USER {user_id}:\n{message.text or 'MEDIA'}"
            )
        except:
            pass

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
            await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)

        elif message.video:
            await bot.send_video(partner_id, message.video.file_id, caption=message.caption)

        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id)

        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)

        elif message.animation:
            await bot.send_animation(partner_id, message.animation.file_id)

    except Exception as e:
        logging.error(e)

# =====================================================
# WEB SERVER
# =====================================================
async def handle(request):
    return web.Response(text="OK")

# =====================================================
# FIX: ONLY ONE POLLING INSTANCE (ВАЖЛИВО)
# =====================================================
async def start_bg(app):
    # ВАЖЛИВО: не створюємо дублікати polling
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))

# =====================================================
# MAIN
# =====================================================
async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    app.on_startup.append(start_bg)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        int(os.getenv("PORT", 10000))
    )

    await site.start()

    print("BOT RUNNING")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
