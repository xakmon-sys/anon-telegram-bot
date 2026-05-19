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

# =======================
# ADMIN
# =======================
ADMIN_ID = 342371504

# База користувачів
users_db = {}

# =======================
# KEYBOARDS
# =======================

def get_gender_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👨 Я Хлопець"))
    builder.add(types.KeyboardButton(text="👩 Я Дівчина"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"))
    builder.add(types.KeyboardButton(text="📊 Статистика онлайну"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_search_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🙋‍♂️ Шукаю Хлопця"))
    builder.add(types.KeyboardButton(text="🙋‍♀️ Шукаю Дівчину"))
    builder.add(types.KeyboardButton(text="🌍 Шукаю Будь-кого"))
    builder.add(types.KeyboardButton(text="⬅️ В головне меню"))
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Наступний (Next)"))
    builder.add(types.KeyboardButton(text="🛑 Зупинити чат"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# =======================
# START
# =======================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    users_db[user_id] = {
        "status": "gender_select",
        "gender": None,
        "search_preference": None,
        "partner": None
    }

    welcome_text = (
        "✨ **Ласкаво просимо до Анонімного Чату!** ✨\n\n"
        "Тут ти можеш спілкуватися абсолютно інкогніто.\n"
        "Для початку роботи, будь ласка, **обери свою стать** 👇"
    )

    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_gender_menu())

# =======================
# ADMIN REPLY
# =======================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 Адмін активний")

@dp.message(Command("reply"))
async def admin_reply(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, uid, *txt = message.text.split()
        await bot.send_message(int(uid), "👮 Адмін: " + " ".join(txt))
    except:
        await message.answer("Формат: /reply user_id текст")

# =======================
# GENDER
# =======================

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):
    uid = message.from_user.id

    if uid not in users_db:
        users_db[uid] = {}

    users_db[uid]["gender"] = "male" if "Хлопець" in message.text else "female"
    users_db[uid]["status"] = "idle"

    await message.answer("✅ Збережено", reply_markup=get_main_menu())

# =======================
# SEARCH MENU
# =======================

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def search_menu(message: types.Message):
    await message.answer("Обери фільтр 👇", reply_markup=get_search_menu())

# =======================
# SEARCH LOGIC
# =======================

async def find_partner(user_id, pref_text):
    users_db[user_id]["status"] = "search"

    pref = "any"
    if "Хлопця" in pref_text:
        pref = "male"
    elif "Дівчину" in pref_text:
        pref = "female"

    users_db[user_id]["search_preference"] = pref

    my_gender = users_db[user_id]["gender"]

    for partner_id, data in users_db.items():
        if partner_id == user_id:
            continue

        if data.get("status") != "search":
            continue

        partner_gender = data.get("gender")
        partner_pref = data.get("search_preference")

        if (partner_pref in ["any", my_gender]) and (pref in ["any", partner_gender]):
            users_db[user_id]["status"] = "chat"
            users_db[partner_id]["status"] = "chat"

            users_db[user_id]["partner"] = partner_id
            users_db[partner_id]["partner"] = user_id

            await bot.send_message(user_id, "🎉 Чат знайдено", reply_markup=get_chat_menu())
            await bot.send_message(partner_id, "🎉 Чат знайдено", reply_markup=get_chat_menu())
            return

# =======================
# FIXED SEARCH HANDLER
# =======================

@dp.message(F.text.in_(["🙋‍♂️ Шукаю Хлопця", "🙋‍♀️ Шукаю Дівчину", "🌍 Шукаю Будь-кого"]))
async def start_search(message: types.Message):
    await message.answer("🔎 Пошук...", reply_markup=types.ReplyKeyboardRemove())
    await find_partner(message.from_user.id, message.text)

# =======================
# NEXT FIX (ВАЖЛИВО ВИПРАВЛЕНО)
# =======================

@dp.message(F.text == "⏭ Наступний (Next)")
async def next_chat(message: types.Message):
    uid = message.from_user.id

    if uid in users_db and users_db[uid].get("status") == "chat":
        partner = users_db[uid]["partner"]

        users_db[partner]["status"] = "idle"
        users_db[partner]["partner"] = None

        await bot.send_message(partner, "🔁 Перемкнули тебе", reply_markup=get_main_menu())

    pref = users_db.get(uid, {}).get("search_preference", "any")

    text_map = {
        "male": "🙋‍♂️ Шукаю Хлопця",
        "female": "🙋‍♀️ Шукаю Дівчину",
        "any": "🌍 Шукаю Будь-кого"
    }

    await find_partner(uid, text_map.get(pref, "🌍 Шукаю Будь-кого"))

# =======================
# GLOBAL FORWARD + ADMIN MEDIA FIX
# =======================

@dp.message()
async def forward(message: types.Message):
    uid = message.from_user.id

    # ================= ADMIN LOG (TEXT + MEDIA)
    if uid != ADMIN_ID:
        try:
            if message.text:
                await bot.send_message(ADMIN_ID, f"📩 {uid}: {message.text}")

            elif message.photo:
                await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 {uid}")

            elif message.video:
                await bot.send_video(ADMIN_ID, message.video.file_id, caption=f"📩 {uid}")

            elif message.voice:
                await bot.send_voice(ADMIN_ID, message.voice.file_id, caption=f"📩 {uid}")

            elif message.sticker:
                await bot.send_sticker(ADMIN_ID, message.sticker.file_id)

            elif message.animation:
                await bot.send_animation(ADMIN_ID, message.animation.file_id)

        except Exception as e:
            logging.error(e)

    # ================= CHAT FORWARD
    if uid in users_db and users_db[uid].get("status") == "chat":
        partner = users_db[uid]["partner"]

        try:
            if message.text:
                await bot.send_message(partner, message.text)
            elif message.photo:
                await bot.send_photo(partner, message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(partner, message.video.file_id, caption=message.caption)
            elif message.voice:
                await bot.send_voice(partner, message.voice.file_id)
            elif message.sticker:
                await bot.send_sticker(partner, message.sticker.file_id)
            elif message.animation:
                await bot.send_animation(partner, message.animation.file_id)
        except Exception as e:
            logging.error(e)

# =======================
# WEB SERVER
# =======================

async def handle(request):
    return web.Response(text="OK")

async def start_bg(app):
    asyncio.create_task(dp.start_polling(bot))

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    app.on_startup.append(start_bg)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
