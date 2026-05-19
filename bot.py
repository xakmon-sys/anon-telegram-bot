import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

BOT_TOKEN = "8724564645:AAFK2Im7H2_WpY9G9EiRZbnIz1fRuwa_4J4"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База даних користувачів у пам'яті
# Структура: {user_id: {"status": "idle" / "search" / "chat", "partner": partner_id}}
users_db = {}

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🔍 Знайти співрозмовника"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_chat_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="⏭ Наступний (Next)"))
    builder.add(types.KeyboardButton(text="🛑 Зупинити чат"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"status": "idle", "partner": None}
    
    welcome_text = (
        "✨ **Ласкаво просимо до Анонімного Чату!** ✨\n\n"
        "Тут ти можеш спілкуватися абсолютно інкогніто.\n"
        "Твій співрозмовник не дізнається твого імені чи юзернейму.\n\n"
        "👇 Натисни кнопку нижче, щоб знайти пару:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    total = len(users_db)
    searching = sum(1 for u in users_db.values() if u["status"] == "search")
    chating = sum(1 for u in users_db.values() if u["status"] == "chat")
    
    stats_text = (
        "📊 **Статистика чату:**\n\n"
        f"👥 Всього користувачів у системі: {total}\n"
        f"🔎 Шукають пару прямо зараз: {searching}\n"
        f"💬 Зараз спілкуються: {chating}"
    )
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    
    # Якщо користувач уже в чаті, ігноруємо
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        await message.answer("Ти вже перебуваєш у чаті! Спершу зупини поточний.", reply_markup=get_chat_menu())
        return

    users_db[user_id] = {"status": "search", "partner": None}
    await message.answer("🔎 Шукаю для тебе крутого співрозмовника... Зачекай хвилинку.", reply_markup=types.ReplyKeyboardRemove())
    
    # Шукаємо вільну пару
    for partner_id, data in users_db.items():
        if partner_id != user_id and data["status"] == "search":
            # З'єднуємо користувачів
            users_db[user_id].update({"status": "chat", "partner": partner_id})
            users_db[partner_id].update({"status": "chat", "partner": user_id})
            
            # Надсилаємо сповіщення обом
            await bot.send_message(user_id, "🎉 Співрозмовника знайдено! Можете спілкуватися. Напиши «Привіт» 👋", reply_markup=get_chat_menu())
            await bot.send_message(partner_id, "🎉 Співрозмовника знайдено! Можете спілкуватися. Напиши «Привіт» 👋", reply_markup=get_chat_menu())
            return

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        
        users_db[user_id] = {"status": "idle", "partner": None}
        users_db[partner_id] = {"status": "idle", "partner": None}
        
        await bot.send_message(user_id, "🛑 Ти закінчив цей чат.", reply_markup=get_main_menu())
        await bot.send_message(partner_id, "🛑 Співрозмовник залишив чат. Ти повернувся в головне меню.", reply_markup=get_main_menu())
    else:
        await message.answer("Ти зараз не перебуваєш у чаті.", reply_markup=get_main_menu())

@dp.message(F.text == "⏭ Наступний (Next)")
async def next_partner(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        
        # Відключаємо старого партнера
        users_db[partner_id] = {"status": "idle", "partner": None}
        await bot.send_message(partner_id, "🛑 Співрозмовник переключився на іншого користувача.", reply_markup=get_main_menu())
    
    # Одразу запускаємо пошук нового для нашого користувача
    await start_search(message)

# 💬 Головний пересилач ВСІХ типів повідомлень (текст, фото, стікери, голосові)
@dp.message()
async def global_forwarder(message: types.Message):
    user_id = message.from_user.id
    
    # Перевіряємо, чи користувач у чаті
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        
        try:
            # Пересилаємо залежно від типу контенту
            if message.text:
                await bot.send_message(partner_id, message.text)
            elif message.photo:
                await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            elif message.voice:
                await bot.send_voice(partner_id, message.voice.file_id, caption=message.caption)
            elif message.sticker:
                await bot.send_sticker(partner_id, message.sticker.file_id)
            elif message.video:
                await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            elif message.animation: # Гіфки
                await bot.send_animation(partner_id, message.animation.file_id)
            else:
                await message.answer("⚠️ Цей тип повідомлень поки не підтримується анонімним чатом.")
        except Exception as e:
            logging.error(f"Помилка пересилання: {e}")
            await message.answer("⚠️ Не вдалося доставити повідомлення співрозмовнику.")
    else:
        # Якщо користувач просто пише текст поза чатом
        if message.text not in ["🔍 Знайти співрозмовника", "🛑 Зупинити чат", "⏭ Наступний (Next)"]:
            await message.answer("Поки що ти ні з ким не спілкуєшся. Натисни кнопку нижче, щоб знайти пару 👇", reply_markup=get_main_menu())

async def handle_web(request):
    return web.Response(text="Bot is perfectly alive!")

async def start_bot_background(app):
    asyncio.create_task(dp.start_polling(bot))

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    app.on_startup.append(start_bot_background)
    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
