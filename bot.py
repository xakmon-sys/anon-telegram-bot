import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# users_db structure: { user_id: {status, gender, search_preference, topic, partner, photo, caption} }
users_db = {}

# --- KEYBOARDS ---
def get_gender_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👨 Я Хлопець"), types.KeyboardButton(text="👩 Я Дівчина"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"))
    builder.add(types.KeyboardButton(text="❤️ Дайвінчик"))
    builder.add(types.KeyboardButton(text="📊 Онлайн"))
    builder.add(types.KeyboardButton(text="ℹ️ Правила"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_search_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🙋‍♂️ Шукаю Хлопця"), types.KeyboardButton(text="🙋‍♀️ Шукаю Дівчину"),
                types.KeyboardButton(text="🌍 Шукаю Будь-кого"), types.KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

def get_topic_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="💬 Звичайне спілкування"), types.KeyboardButton(text="❤️ Флірт"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Next"), types.KeyboardButton(text="🛑 Зупинити чат"), types.KeyboardButton(text="👀 Хто друкує?"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

# --- COMMANDS ---
@dp.message(Command("start"))
async def start(message: types.Message):
    users_db[message.from_user.id] = {"status": "gender_select", "gender": None, "search_preference": "any", "topic": "normal", "partner": None}
    await message.answer("✨ Ласкаво просимо в РОЗМОВА!\n👇 Обери свою стать", parse_mode="HTML", reply_markup=get_gender_menu())

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):
    users_db[message.from_user.id].update({"gender": "male" if "Хлопець" in message.text else "female", "status": "idle"})
    await message.answer("✅ Дані збережено!", reply_markup=get_main_menu())

# --- DATING (DAIVINCHIK) ---
@dp.message(F.text == "❤️ Дайвінчик")
async def dating_menu(message: types.Message):
    await message.answer("❤️ **Дайвінчик**\nНадішліть фото та опис, щоб створити анкету, або натисніть /view для перегляду інших.", parse_mode="HTML")
    users_db[message.from_user.id]["status"] = "dating_setup"

@dp.message(F.status == "dating_setup", F.photo)
async def create_profile(message: types.Message):
    users_db[message.from_user.id].update({"photo": message.photo[-1].file_id, "caption": message.caption or "Без опису", "status": "idle"})
    await message.answer("✅ Анкета створена!")

@dp.message(Command("view"))
async def view_profiles(message: types.Message):
    profiles = [data for uid, data in users_db.items() if "photo" in data and uid != message.from_user.id]
    if not profiles: return await message.answer("Анкет поки немає.")
    p = random.choice(profiles)
    await bot.send_photo(message.from_user.id, p["photo"], caption=f"👤 Анкета: {p['caption']}")

# --- CHAT LOGIC (YOUR ORIGINAL) ---
@dp.message(F.text == "🔍 Знайти співрозмовника")
async def search_menu(message: types.Message):
    await message.answer("👇 Кого шукаємо?", reply_markup=get_search_menu())

@dp.message(F.text.in_(["🙋‍♂️ Шукаю Хлопця", "🙋‍♀️ Шукаю Дівчину", "🌍 Шукаю Будь-кого"]))
async def choose_topic(message: types.Message):
    users_db[message.from_user.id]["search_preference"] = "male" if "Хлопця" in message.text else "female" if "Дівчину" in message.text else "any"
    await message.answer("🎭 Обери тему", reply_markup=get_topic_menu())

@dp.message(F.text.in_(["💬 Звичайне спілкування", "❤️ Флірт"]))
async def start_search(message: types.Message):
    user_id = message.from_user.id
    users_db[user_id].update({"topic": "flirt" if "Флірт" in message.text else "normal", "status": "search"})
    await message.answer("🔎 Шукаємо...", reply_markup=types.ReplyKeyboardRemove())
    
    for pid, p in users_db.items():
        if pid != user_id and p["status"] == "search" and p["topic"] == users_db[user_id]["topic"]:
            users_db[user_id].update({"status": "chat", "partner": pid})
            p.update({"status": "chat", "partner": user_id})
            await bot.send_message(user_id, "🎉 Знайдено!", reply_markup=get_chat_menu())
            await bot.send_message(pid, "🎉 Знайдено!", reply_markup=get_chat_menu())
            return

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    u = users_db.get(message.from_user.id)
    if u and u["status"] == "chat":
        p_id = u["partner"]
        u.update({"status": "idle", "partner": None})
        if p_id:
            users_db[p_id].update({"status": "idle", "partner": None})
            await bot.send_message(p_id, "❌ Співрозмовник вийшов", reply_markup=get_main_menu())
    await message.answer("🛑 Завершено", reply_markup=get_main_menu())

@dp.message(F.text == "📊 Онлайн")
async def stats(message: types.Message):
    await message.answer(f"👥 Всього: {len(users_db)}")

@dp.message()
async def forwarder(message: types.Message):
    u = users_db.get(message.from_user.id)
    if u and u["status"] == "chat":
        try:
            if message.text: await bot.send_message(u["partner"], message.text)
            elif message.photo: await bot.send_photo(u["partner"], message.photo[-1].file_id, caption=message.caption)
        except: pass

# --- WEB & MAIN ---
async def handle(request): return web.Response(text="BOT ONLINE")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000))).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
