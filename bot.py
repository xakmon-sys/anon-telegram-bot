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

# База даних: {user_id: {"status": "idle/chat/search", "partner": id, "karma": 0, "wants_contact": False}}
users_db = {}

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Почати пошук"))
    builder.add(types.KeyboardButton(text="📊 Статистика"))
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Наступний"))
    builder.add(types.KeyboardButton(text="🔗 Відкрити профіль"))
    builder.add(types.KeyboardButton(text="🛑 Зупинити"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_karma_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👍 Сподобався"))
    builder.add(types.KeyboardButton(text="👎 Не сподобався"))
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"status": "idle", "partner": None, "karma": 0, "wants_contact": False}
    await message.answer("✨ **РОЗМОВА** — анонімний чат.\nТисни «Почати пошук», щоб знайти співрозмовника!", reply_markup=get_main_menu())

@dp.message(F.text == "🔍 Почати пошук")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    users_db[user_id].update({"status": "search", "wants_contact": False})
    await message.answer("🔎 *Шукаю цікаву людину...*", parse_mode="Markdown")
    
    for p_id, data in users_db.items():
        if p_id != user_id and data["status"] == "search":
            users_db[user_id].update({"status": "chat", "partner": p_id})
            users_db[p_id].update({"status": "chat", "partner": user_id})
            await bot.send_message(user_id, "✅ **Знайдено!** Можете спілкуватися.", reply_markup=get_chat_menu())
            await bot.send_message(p_id, "✅ **Знайдено!** Можете спілкуватися.", reply_markup=get_chat_menu())
            return

@dp.message(F.text == "🔗 Відкрити профіль")
async def share_contact(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        users_db[user_id]["wants_contact"] = True
        
        if users_db[partner_id]["wants_contact"]:
            u1 = await bot.get_chat(user_id)
            u2 = await bot.get_chat(partner_id)
            link1 = f"tg://user?id={user_id}"
            link2 = f"tg://user?id={partner_id}"
            await bot.send_message(user_id, f"🤝 **Взаємно!** Твій співрозмовник: {u2.full_name} ({link2})")
            await bot.send_message(partner_id, f"🤝 **Взаємно!** Твій співрозмовник: {u1.full_name} ({link1})")
        else:
            await message.answer("⏳ *Чекаємо, поки співрозмовник теж натисне кнопку...*", parse_mode="Markdown")

@dp.message(F.text.in_(["👍 Сподобався", "👎 Не сподобався"]))
async def rate_user(message: types.Message):
    await message.answer("Дякуємо за оцінку! Тисни «Почати пошук», щоб продовжити.", reply_markup=get_main_menu())

@dp.message(F.text == "🛑 Зупинити")
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        users_db[user_id].update({"status": "idle", "partner": None})
        users_db[partner_id].update({"status": "idle", "partner": None})
        await bot.send_message(user_id, "Оціни співрозмовника:", reply_markup=get_karma_menu())
        await bot.send_message(partner_id, "Співрозмовник вийшов. Оціни його:", reply_markup=get_karma_menu())

@dp.message()
async def forwarder(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        if message.text: await bot.send_message(partner_id, message.text)
        elif message.photo: await bot.send_photo(partner_id, message.photo[-1].file_id)
    else:
        await message.answer("Тисни «Почати пошук»!", reply_markup=get_main_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
