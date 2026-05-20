import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)

# Використовуємо FSM для станів (це надійніше ніж словник)
class DatingForm(StatesGroup):
    waiting_for_photo = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dating_profiles = []

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Знайти співрозмовника")
    builder.button(text="❤️ Дайвінчик")
    builder.button(text="📊 Онлайн")
    builder.button(text="ℹ️ Правила")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# --- ДАЙВІНЧИК ---
@dp.message(F.text == "❤️ Дайвінчик")
async def dating_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Створити анкету")
    builder.button(text="👀 Дивитися анкети")
    builder.button(text="⬅️ Назад")
    builder.adjust(1)
    await message.answer("❤️ **Дайвінчик**\nОбери дію:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "📝 Створити анкету")
async def create_profile_ask(message: types.Message, state: FSMContext):
    await state.set_state(DatingForm.waiting_for_photo)
    await message.answer("Надішліть фото для анкети (з описом в підписі):")

@dp.message(DatingForm.waiting_for_photo, F.photo)
async def save_profile(message: types.Message, state: FSMContext):
    profile = {
        "user_id": message.from_user.id,
        "photo": message.photo[-1].file_id,
        "caption": message.caption or "Без опису"
    }
    dating_profiles.append(profile)
    await state.clear()
    await message.answer("✅ Анкета створена!", reply_markup=get_main_menu())

@dp.message(F.text == "👀 Дивитися анкети")
async def view_dating(message: types.Message):
    if not dating_profiles:
        return await message.answer("Анкет поки немає.")
    
    p = random.choice(dating_profiles)
    builder = ReplyKeyboardBuilder()
    builder.button(text="👍 Like")
    builder.button(text="👎 Next")
    builder.button(text="⬅️ Назад")
    await bot.send_photo(message.chat.id, p["photo"], caption=f"👤: {p['caption']}", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.in_({"👍 Like", "👎 Next"}))
async def next_profile(message: types.Message):
    await view_dating(message)

@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Головне меню:", reply_markup=get_main_menu())

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привіт! Ласкаво просимо.", reply_markup=get_main_menu())

# --- ЗАПУСК ---
async def on_startup():
    logging.info("Бот запущений!")

async def main():
    # Запускаємо веб-сервер та поллінг паралельно
    await dp.start_polling(bot, on_startup=on_startup)

if __name__ == "__main__":
    asyncio.run(main())
