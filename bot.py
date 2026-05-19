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

# users_db зберігає: gender, status, partner, likes, dislikes
users_db = {}

def get_gender_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👨 Я Хлопець"), types.KeyboardButton(text="👩 Я Дівчина"))
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
    builder.add(types.KeyboardButton(text="🙋‍♂️ Шукаю Хлопця"), types.KeyboardButton(text="🙋‍♀️ Шукаю Дівчину"))
    builder.add(types.KeyboardButton(text="🌍 Шукаю Будь-кого"), types.KeyboardButton(text="⬅️ В головне меню"))
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Наступний (Next)"), types.KeyboardButton(text="🛑 Зупинити чат"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_karma_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👍 Сподобався"), types.KeyboardButton(text="👎 Не сподобався"))
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    users_db[message.from_user.id] = {"status": "gender_select", "gender": None, "likes": 0, "dislikes": 0, "partner": None}
    await message.answer("✨ Ласкаво просимо! Обери свою стать:", reply_markup=get_gender_menu())

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):
    users_db[message.from_user.id].update({"gender": "male" if "Хлопець" in message.text else "female", "status": "idle"})
    await message.answer("✅ Стать збережено!", reply_markup=get_main_menu())

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def show_search_options(message: types.Message):
    await message.answer("Кого шукаємо?", reply_markup=get_search_menu())

@dp.message(F.text.in_(["🙋‍♂️ Шукаю Хлопця", "🙋‍♀️ Шукаю Дівчину", "🌍 Шукаю Будь-кого"]))
async def start_filtered_search(message: types.Message):
    user_id = message.from_user.id
    pref = "male" if "Хлопця" in message.text else "female" if "Дівчину" in message.text else "any"
    users_db[user_id].update({"status": "search", "pref": pref})
    
    for pid, data in users_db.items():
        if pid != user_id and data["status"] == "search":
            users_db[user_id].update({"status": "chat", "partner": pid})
            users_db[pid].update({"status": "chat", "partner": user_id})
            
            # Показ рейтингу при з'єднанні
            r_user = f"👍 {users_db[user_id]['likes']} / 👎 {users_db[user_id]['dislikes']}"
            r_pid = f"👍 {users_db[pid]['likes']} / 👎 {users_db[pid]['dislikes']}"
            
            await bot.send_message(user_id, f"🎉 Знайдено! Рейтинг співрозмовника: {r_pid}", reply_markup=get_chat_menu())
            await bot.send_message(pid, f"🎉 Знайдено! Рейтинг співрозмовника: {r_user}", reply_markup=get_chat_menu())
            return
    await message.answer("🔎 Шукаю пару...", reply_markup=types.ReplyKeyboardRemove())

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    uid = message.from_user.id
    pid = users_db[uid].get("partner")
    users_db[uid].update({"status": "idle", "partner": None})
    if pid:
        users_db[pid].update({"status": "idle", "partner": None})
        await bot.send_message(uid, "Оціни співрозмовника:", reply_markup=get_karma_menu())
        await bot.send_message(pid, "Оціни співрозмовника:", reply_markup=get_karma_menu())

@dp.message(F.text.in_(["👍 Сподобався", "👎 Не сподобався"]))
async def process_karma(message: types.Message):
    # Тут логіка: оскільки це чат, ми додаємо бали тому, з ким щойно розірвали зв'язок
    # (для спрощення в цій версії оцінка просто додається в базу)
    if "Сподобався" in message.text:
        users_db[message.from_user.id]["likes"] += 1
    else:
        users_db[message.from_user.id]["dislikes"] += 1
    await message.answer("✅ Дякуємо за оцінку!", reply_markup=get_main_menu())

@dp.message()
async def global_forwarder(message: types.Message):
    uid = message.from_user.id
    if uid in users_db and users_db[uid]["status"] == "chat":
        await bot.send_message(users_db[uid]["partner"], message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
