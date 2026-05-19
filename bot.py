import asyncio
import logging
import os
import random
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

BOT_TOKEN = "8724564645:AAFk2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База даних з розширеними полями
users_db = {}
chat_start_times = {}

# --- КЛАВІАТУРИ ---

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="⏭ Next"), 
        types.KeyboardButton(text="🛑 Зупинити чат"),
        types.KeyboardButton(text="🎲 Грати в кубик"),
        types.KeyboardButton(text="✨ Комплімент"),
        types.KeyboardButton(text="🌍 Привітатися мовами")
    )
    builder.adjust(2, 1, 2)
    return builder.as_markup(resize_keyboard=True)

# (Інші функції get_gender_menu, get_main_menu, get_search_menu, get_topic_menu залишаються без змін)

# --- НОВІ ФУНКЦІЇ ---

@dp.message(F.text == "🎲 Грати в кубик")
async def play_dice(message: types.Message):
    user_id = message.from_user.id
    partner_id = users_db[user_id].get("partner")
    
    if partner_id:
        dice = await message.answer_dice()
        await bot.send_message(partner_id, f"🎲 Твій співрозмовник кинув кубик: {dice.dice.value}")
        await message.answer(f"Ви випало: {dice.dice.value}")

@dp.message(F.text == "🌍 Привітатися мовами")
async def say_hi_languages(message: types.Message):
    phrases = ["Hello!", "Bonjour!", "Hola!", "Konnichiwa!", "Hallo!"]
    await message.answer(f"Ваш співрозмовник каже: {random.choice(phrases)}")
    
    # Відправляємо і партнеру
    partner_id = users_db[message.from_user.id].get("partner")
    if partner_id:
        await bot.send_message(partner_id, f"Партнер каже: {random.choice(phrases)}")

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    partner_id = users_db[user_id].get("partner")
    
    # Рахуємо час спілкування
    start_time = chat_start_times.get(user_id, time.time())
    duration = int(time.time() - start_time)
    
    await message.answer(f"🛑 Чат завершено. Ви спілкувалися {duration // 60} хв {duration % 60} сек.")
    
    if partner_id:
        await bot.send_message(partner_id, "❌ Співрозмовник завершив чат.")
        users_db[partner_id]["status"] = "idle"
        users_db[partner_id]["partner"] = None
        
    users_db[user_id]["status"] = "idle"
    users_db[user_id]["partner"] = None

# --- ОНОВЛЕНИЙ CONNECT (з фіксацією часу) ---

# У функції start_search, де йде "CONNECT", додайте це:
# chat_start_times[user_id] = time.time()
# chat_start_times[partner_id] = time.time()

# --- ВАШ СТАРИЙ КОД ---
# (Тут залишається весь ваш оригінальний код, який ви просили не змінювати)
# Просто переконайтеся, що ви додали виклики нових функцій вище в обробники.

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
