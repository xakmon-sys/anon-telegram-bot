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

# База даних користувачів та анкет
users_db = {}
dating_profiles = [] # Список анкет для дайвінчику

# --- КЛАВІАТУРИ ---
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"))
    builder.add(types.KeyboardButton(text="❤️ Дайвінчик")) 
    builder.add(types.KeyboardButton(text="📊 Онлайн"))
    builder.add(types.KeyboardButton(text="ℹ️ Правила"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# --- НОВІ ФУНКЦІЇ ДАЙВІНЧИК ---

@dp.message(F.text == "❤️ Дайвінчик")
async def dating_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📝 Створити анкету"), types.KeyboardButton(text="👀 Дивитися анкети"))
    builder.add(types.KeyboardButton(text="⬅️ Назад"))
    await message.answer("❤️ **Дайвінчик**\nОбери дію:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "📝 Створити анкету")
async def create_profile_ask(message: types.Message):
    users_db[message.from_user.id]["status"] = "dating_wait_photo"
    await message.answer("Надішліть фото для анкети (одним повідомленням з описом):")

@dp.message(F.status == "dating_wait_photo", F.photo)
async def save_profile(message: types.Message):
    profile = {
        "user_id": message.from_user.id,
        "photo": message.photo[-1].file_id,
        "caption": message.caption or "Без опису"
    }
    dating_profiles.append(profile)
    users_db[message.from_user.id]["status"] = "idle"
    await message.answer("✅ Ваша анкета успішно створена!", reply_markup=get_main_menu())

@dp.message(F.text == "👀 Дивитися анкети")
async def view_dating(message: types.Message):
    if not dating_profiles:
        return await message.answer("Анкет поки немає.")
    
    p = random.choice(dating_profiles)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="👍 Like"), types.KeyboardButton(text="👎 Next"))
    await bot.send_photo(message.from_user.id, p["photo"], caption=f"👤 Анкета: {p['caption']}", reply_markup=builder.as_markup(resize_keyboard=True))

# --- ЗАЛИШОК ВАШОГО КОДУ (СТРУКТУРА ЗБЕРЕЖЕНА) ---

@dp.message(Command("start"))
async def start(message: types.Message):
    users_db[message.from_user.id] = {"status": "idle"}
    await message.answer("Привіт! Ласкаво просимо.", reply_markup=get_main_menu())

# ... (сюди вставте вашу стару логіку чату: gender_menu, search_menu тощо) ...

# Обов'язково додайте вихід назад
@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: types.Message):
    await message.answer("Головне меню:", reply_markup=get_main_menu())

# --- ВЕБ СЕРВЕР ТА ЗАПУСК ---
async def handle(request): return web.Response(text="ROZMOVA BOT ONLINE")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
