import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База даних: {user_id: {"status": ..., "gender": ..., "likes": 0, "dislikes": 0, "partner": None}}
users_db = {}

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {"status": "idle", "gender": None, "likes": 0, "dislikes": 0, "partner": None, "pref": "any"}
    return users_db[user_id]

# --- КЛАВІАТУРИ ---
def get_menu(name):
    builder = ReplyKeyboardBuilder()
    if name == "gender":
        builder.add(types.KeyboardButton(text="👨 Я Хлопець"), types.KeyboardButton(text="👩 Я Дівчина"))
    elif name == "main":
        builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"), types.KeyboardButton(text="📊 Статистика онлайну"))
        builder.adjust(1)
    elif name == "search":
        builder.add(types.KeyboardButton(text="🙋‍♂️ Шукаю Хлопця"), types.KeyboardButton(text="🙋‍♀️ Шукаю Дівчину"), 
                    types.KeyboardButton(text="🌍 Шукаю Будь-кого"), types.KeyboardButton(text="⬅️ В головне меню"))
        builder.adjust(2, 1, 1)
    elif name == "chat":
        builder.add(types.KeyboardButton(text="⏭ Наступний (Next)"), types.KeyboardButton(text="🛑 Зупинити чат"))
    elif name == "karma":
        builder.add(types.KeyboardButton(text="👍 Сподобався"), types.KeyboardButton(text="👎 Не сподобався"))
    return builder.as_markup(resize_keyboard=True)

# --- ХЕНДЛЕРИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    get_user(message.from_user.id)
    await message.answer("✨ Привіт! Обери свою стать:", reply_markup=get_menu("gender"))

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):
    user = get_user(message.from_user.id)
    user["gender"] = "male" if "Хлопець" in message.text else "female"
    user["status"] = "idle"
    await message.answer("✅ Збережено!", reply_markup=get_menu("main"))

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def find_partner(message: types.Message):
    await message.answer("Кого шукаємо?", reply_markup=get_menu("search"))

@dp.message(F.text.in_(["🙋‍♂️ Шукаю Хлопця", "🙋‍♀️ Шукаю Дівчину", "🌍 Шукаю Будь-кого"]))
async def start_search(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    user["status"] = "search"
    
    for pid, data in users_db.items():
        if pid != user_id and data["status"] == "search":
            user["status"] = "chat"; user["partner"] = pid
            data["status"] = "chat"; data["partner"] = user_id
            
            r_user = f"👍 {user['likes']} / 👎 {user['dislikes']}"
            r_pid = f"👍 {data['likes']} / 👎 {data['dislikes']}"
            
            await bot.send_message(user_id, f"🎉 Знайдено! Рейтинг співрозмовника: {r_pid}", reply_markup=get_menu("chat"))
            await bot.send_message(pid, f"🎉 Знайдено! Рейтинг співрозмовника: {r_user}", reply_markup=get_menu("chat"))
            return
    await message.answer("🔎 Шукаю...")

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    user = get_user(message.from_user.id)
    pid = user.get("partner")
    user.update({"status": "idle", "partner": None})
    if pid:
        users_db[pid].update({"status": "idle", "partner": None})
        await bot.send_message(message.from_user.id, "Оціни:", reply_markup=get_menu("karma"))
        await bot.send_message(pid, "Оціни:", reply_markup=get_menu("karma"))

@dp.message(F.text.in_(["👍 Сподобався", "👎 Не сподобався"]))
async def karma(message: types.Message):
    user = get_user(message.from_user.id)
    if "Сподобався" in message.text: user["likes"] += 1
    else: user["dislikes"] += 1
    await message.answer("✅ Дякую!", reply_markup=get_menu("main"))

@dp.message()
async def chat_forward(message: types.Message):
    user = get_user(message.from_user.id)
    if user["status"] == "chat" and user["partner"]:
        await bot.send_message(user["partner"], message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
