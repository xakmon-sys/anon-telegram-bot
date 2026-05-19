import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# =========================================
# НОВИЙ TOKEN ВСТАВ СЮДИ
# =========================================
BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================================
# SQLITE DATABASE
# =========================================
db = sqlite3.connect("rozmova.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    gender TEXT,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0
)
""")

db.commit()

# =========================================
# RAM DATA
# =========================================
users = {}
search_queue = []

"""
users structure:
{
    user_id: {
        status: idle/search/chat,
        partner: user_id or None,
        pref: male/female/any
    }
}
"""

# =========================================
# USER FUNCTIONS
# =========================================
def init_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "status": "idle",
            "partner": None,
            "pref": "any"
        }

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    db.commit()

def get_rating(user_id):
    cursor.execute(
        "SELECT likes, dislikes FROM users WHERE user_id=?",
        (user_id,)
    )
    row = cursor.fetchone()

    if row:
        return row[0], row[1]

    return 0, 0

def add_like(user_id):
    cursor.execute(
        "UPDATE users SET likes = likes + 1 WHERE user_id=?",
        (user_id,)
    )
    db.commit()

def add_dislike(user_id):
    cursor.execute(
        "UPDATE users SET dislikes = dislikes + 1 WHERE user_id=?",
        (user_id,)
    )
    db.commit()

def get_gender(user_id):
    cursor.execute(
        "SELECT gender FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    return None

def set_gender(user_id, gender):
    cursor.execute(
        "UPDATE users SET gender=? WHERE user_id=?",
        (gender, user_id)
    )
    db.commit()

# =========================================
# KEYBOARDS
# =========================================
def kb(name):

    builder = ReplyKeyboardBuilder()

    if name == "gender":
        builder.add(
            types.KeyboardButton(text="👨 Я Хлопець"),
            types.KeyboardButton(text="👩 Я Дівчина")
        )

    elif name == "main":
        builder.add(
            types.KeyboardButton(text="🔍 Знайти співрозмовника"),
            types.KeyboardButton(text="📊 Онлайн")
        )
        builder.adjust(1)

    elif name == "search":
        builder.add(
            types.KeyboardButton(text="🙋‍♂️ Шукаю Хлопця"),
            types.KeyboardButton(text="🙋‍♀️ Шукаю Дівчину"),
            types.KeyboardButton(text="🌍 Будь-кого"),
            types.KeyboardButton(text="⬅️ Назад")
        )
        builder.adjust(2, 1, 1)

    elif name == "chat":
        builder.add(
            types.KeyboardButton(text="⏭ Next"),
            types.KeyboardButton(text="🛑 Зупинити")
        )

    elif name == "rate":
        builder.add(
            types.KeyboardButton(text="👍"),
            types.KeyboardButton(text="👎")
        )

    return builder.as_markup(resize_keyboard=True)

# =========================================
# START
# =========================================
@dp.message(Command("start"))
async def start(message: types.Message):

    init_user(message.from_user.id)

    await message.answer(
        "👋 Привіт у РОЗМОВА\n\nОбери свою стать:",
        reply_markup=kb("gender")
    )

# =========================================
# GENDER
# =========================================
@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def gender(message: types.Message):

    user_id = message.from_user.id

    init_user(user_id)

    gender = "male"

    if "Дівчина" in message.text:
        gender = "female"

    set_gender(user_id, gender)

    await message.answer(
        "✅ Збережено",
        reply_markup=kb("main")
    )

# =========================================
# FIND MENU
# =========================================
@dp.message(F.text == "🔍 Знайти співрозмовника")
async def find(message: types.Message):

    await message.answer(
        "Кого шукаємо?",
        reply_markup=kb("search")
    )

# =========================================
# SEARCH
# =========================================
@dp.message(F.text.in_([
    "🙋‍♂️ Шукаю Хлопця",
    "🙋‍♀️ Шукаю Дівчину",
    "🌍 Будь-кого"
]))
async def search(message: types.Message):

    user_id = message.from_user.id

    init_user(user_id)

    user = users[user_id]

    # preference
    if "Хлопця" in message.text:
        user["pref"] = "male"

    elif "Дівчину" in message.text:
        user["pref"] = "female"

    else:
        user["pref"] = "any"

    user["status"] = "search"

    my_gender = get_gender(user_id)

    # MATCHMAKING
    for partner_id in search_queue:

        if partner_id == user_id:
            continue

        partner = users.get(partner_id)

        if not partner:
            continue

        if partner["status"] != "search":
            continue

        partner_gender = get_gender(partner_id)

        # my pref
        if user["pref"] != "any":
            if partner_gender != user["pref"]:
                continue

        # partner pref
        if partner["pref"] != "any":
            if my_gender != partner["pref"]:
                continue

        # CONNECT
        user["status"] = "chat"
        user["partner"] = partner_id

        partner["status"] = "chat"
        partner["partner"] = user_id

        if user_id in search_queue:
            search_queue.remove(user_id)

        if partner_id in search_queue:
            search_queue.remove(partner_id)

        likes1, dislikes1 = get_rating(partner_id)
        likes2, dislikes2 = get_rating(user_id)

        await bot.send_message(
            user_id,
            f"🎉 Співрозмовника знайдено\n\n👍 {likes1} | 👎 {dislikes1}",
            reply_markup=kb("chat")
        )

        await bot.send_message(
            partner_id,
            f"🎉 Співрозмовника знайдено\n\n👍 {likes2} | 👎 {dislikes2}",
            reply_markup=kb("chat")
        )

        return

    if user_id not in search_queue:
        search_queue.append(user_id)

    await message.answer(
        "🔎 Шукаю співрозмовника...",
        reply_markup=kb("chat")
    )

# =========================================
# STOP CHAT
# =========================================
@dp.message(F.text == "🛑 Зупинити")
async def stop(message: types.Message):

    user_id = message.from_user.id

    user = users[user_id]

    partner_id = user["partner"]

    user["status"] = "idle"
    user["partner"] = None

    if partner_id:

        partner = users[partner_id]

        partner["status"] = "idle"
        partner["partner"] = None

        await bot.send_message(
            user_id,
            "Оціни співрозмовника:",
            reply_markup=kb("rate")
        )

        await bot.send_message(
            partner_id,
            "Оціни співрозмовника:",
            reply_markup=kb("rate")
        )

# =========================================
# NEXT
# =========================================
@dp.message(F.text == "⏭ Next")
async def next_chat(message: types.Message):

    user_id = message.from_user.id

    user = users[user_id]

    partner_id = user["partner"]

    if partner_id:

        users[partner_id]["status"] = "idle"
        users[partner_id]["partner"] = None

        await bot.send_message(
            partner_id,
            "❌ Співрозмовник переключив чат",
            reply_markup=kb("main")
        )

    user["status"] = "idle"
    user["partner"] = None

    await message.answer(
        "🔎 Шукаємо нового...",
        reply_markup=kb("search")
    )

# =========================================
# RATING
# =========================================
@dp.message(F.text.in_(["👍", "👎"]))
async def rating(message: types.Message):

    user_id = message.from_user.id

    user = users[user_id]

    last_partner = user.get("last_partner")

    if last_partner:

        if message.text == "👍":
            add_like(last_partner)

        else:
            add_dislike(last_partner)

    await message.answer(
        "✅ Дякуємо за оцінку",
        reply_markup=kb("main")
    )

# =========================================
# ONLINE
# =========================================
@dp.message(F.text == "📊 Онлайн")
async def online(message: types.Message):

    total = len(users)

    searching = len([
        x for x in users.values()
        if x["status"] == "search"
    ])

    chatting = len([
        x for x in users.values()
        if x["status"] == "chat"
    ])

    text = (
        f"👥 Онлайн: {total}\n"
        f"🔎 Шукають: {searching}\n"
        f"💬 В чаті: {chatting}"
    )

    await message.answer(text)

# =========================================
# BACK
# =========================================
@dp.message(F.text == "⬅️ Назад")
async def back(message: types.Message):

    await message.answer(
        "🏠 Головне меню",
        reply_markup=kb("main")
    )

# =========================================
# MEDIA FORWARD
# =========================================
@dp.message()
async def relay(message: types.Message):

    user_id = message.from_user.id

    init_user(user_id)

    user = users[user_id]

    if user["status"] != "chat":
        return

    partner_id = user["partner"]

    if not partner_id:
        return

    try:

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

        # STICKER
        elif message.sticker:
            await bot.send_sticker(
                partner_id,
                message.sticker.file_id
            )

    except:
        pass

# =========================================
# MAIN
# =========================================
async def main():

    print("BOT STARTED")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
