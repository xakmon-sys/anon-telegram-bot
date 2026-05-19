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

# База даних користувачів у пам'яті
# Структура: {user_id: {"status": "idle"/"gender_select"/"search"/"chat", "gender": "male"/"female"/None, "search_preference": "male"/"female"/"any"/None, "partner": partner_id}}
users_db = {}

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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Реєструємо або скидаємо налаштування для старту
    users_db[user_id] = {"status": "gender_select", "gender": None, "search_preference": None, "partner": None}
    
    welcome_text = (
        "✨ **Ласкаво просимо до Анонімного Чату!** ✨\n\n"
        "Тут ти можеш спілкуватися абсолютно інкогніто.\n"
        "Для початку роботи, будь ласка, **обери свою стать** нижче 👇"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_gender_menu())

@dp.message(F.text.in_(["👨 Я Хлопець", "👩 Я Дівчина"]))
async def set_gender(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"status": "idle", "gender": None, "search_preference": None, "partner": None}
        
    gender = "male" if "Хлопець" in message.text else "female"
    users_db[user_id]["gender"] = gender
    users_db[user_id]["status"] = "idle"
    
    await message.answer("✅ Твою стать збережено! Тепер ти можеш шукати пару.", reply_markup=get_main_menu())

@dp.message(F.text == "📊 Статистика онлайну")
@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    total = len(users_db)
    searching = sum(1 for u in users_db.values() if u["status"] == "search")
    chating = sum(1 for u in users_db.values() if u["status"] == "chat")
    
    stats_text = (
        "📊 **Онлайн статистика чату:**\n\n"
        f"👥 Всього користувачів у системі: **{total}**\n"
        f"🔎 Шукають пару прямо зараз: **{searching}**\n"
        f"💬 Зараз спілкуються в чатах: **{chating}**"
    )
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(F.text == "🔍 Знайти співрозмовника")
async def show_search_options(message: types.Message):
    user_id = message.from_user.id
    
    # Перевірка, чи вказана стать
    if user_id not in users_db or users_db[user_id]["gender"] is None:
        await message.answer("⚠️ Спочатку виберіть свою стать!", reply_markup=get_gender_menu())
        return

    if users_db[user_id]["status"] == "chat":
        await message.answer("Ти вже в чаті! Спершу зупини його.", reply_markup=get_chat_menu())
        return
        
    await message.answer("Кого ти хочеш знайти для спілкування? 👇", reply_markup=get_search_menu())

@dp.message(F.text.in_(["🙋‍♂️ Шукаю Хлопця", "🙋‍♀️ Шукаю Дівчину", "🌍 Шукаю Будь-кого"]))
async def start_filtered_search(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in users_db or users_db[user_id]["gender"] is None:
        await message.answer("⚠️ Спочатку виберіть свою стать!", reply_markup=get_gender_menu())
        return

    # Визначаємо вподобання пошуку
    pref = "any"
    if "Хлопця" in message.text:
        pref = "male"
    elif "Дівчину" in message.text:
        pref = "female"
        
    users_db[user_id].update({"status": "search", "search_preference": pref})
    my_gender = users_db[user_id]["gender"]
    
    await message.answer("🔎 Шукаю пару за твоїми фільтрами... Зачекай хвилинку.", reply_markup=types.ReplyKeyboardRemove())
    
    # Алгоритм розумного підбору з урахуванням статі обох сторін
    for partner_id, data in users_db.items():
        if partner_id != user_id and data["status"] == "search":
            partner_gender = data["gender"]
            partner_pref = data["search_preference"]
            
            # Перевіряємо, чи підходимо ми партнеру
            match_me_to_partner = (partner_pref == "any" or partner_pref == my_gender)
            # Перевіряємо, чи підходить партнер нам
            match_partner_to_me = (pref == "any" or pref == partner_gender)
            
            if match_me_to_partner and match_partner_to_me:
                # З'єднуємо пару
                users_db[user_id].update({"status": "chat", "partner": partner_id})
                users_db[partner_id].update({"status": "chat", "partner": user_id})
                
                await bot.send_message(user_id, "🎉 Співрозмовника знайдено! Напиши «Привіт» 👋", reply_markup=get_chat_menu())
                await bot.send_message(partner_id, "🎉 Співрозмовника знайдено! Напиши «Привіт» 👋", reply_markup=get_chat_menu())
                return

@dp.message(F.text == "⬅️ В головне меню")
async def go_to_main(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db:
        users_db[user_id]["status"] = "idle"
    await message.answer("Ти повернувся в головне меню.", reply_markup=get_main_menu())

@dp.message(F.text == "🛑 Зупинити чат")
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        
        users_db[user_id].update({"status": "idle", "partner": None})
        users_db[partner_id].update({"status": "idle", "partner": None})
        
        await bot.send_message(user_id, "🛑 Ти закінчив цей чат.", reply_markup=get_main_menu())
        await bot.send_message(partner_id, "🛑 Співрозмовник залишив чат. Ти повернувся в головне меню.", reply_markup=get_main_menu())
    else:
        await message.answer("Ти зараз не в чаті.", reply_markup=get_main_menu())

@dp.message(F.text == "⏭ Наступний (Next)")
async def next_partner(message: types.Message):
    user_id = message.from_user.id
    
    # Якщо був активний чат, спочатку роз'єднуємо
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        users_db[partner_id].update({"status": "idle", "partner": None})
        await bot.send_message(partner_id, "🛑 Співрозмовник переключився на іншого користувача.", reply_markup=get_main_menu())
    
    # Якщо збереглися старі налаштування фільтру — шукаємо за ними, інакше шукаємо "будь-кого"
    pref = users_db.get(user_id, {}).get("search_preference", "any")
    
    # Створюємо штучне повідомлення для виклику функції пошуку
    fake_message = message
    if pref == "male":
        fake_message.text = "🙋‍♂️ Шукаю Хлопця"
    elif pref == "female":
        fake_message.text = "🙋‍♀️ Шукаю Дівчину"
    else:
        fake_message.text = "🌍 Шукаю Будь-кого"
        
    await start_filtered_search(fake_message)

# Пересилач повідомлень
@dp.message()
async def global_forwarder(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in users_db and users_db[user_id]["status"] == "chat":
        partner_id = users_db[user_id]["partner"]
        try:
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
            elif message.animation:
                await bot.send_animation(partner_id, message.animation.file_id)
        except Exception as e:
            logging.error(f"Error forwarding: {e}")
            await message.answer("⚠️ Не вдалося доставити повідомлення.")
    else:
        # Ігноруємо системні кнопки, на інші тексти відповідаємо підказкою
        if message.text not in ["🔍 Знайти співрозмовника", "🛑 Зупинити чат", "⏭ Наступний (Next)", "📊 Статистика онлайну", "👨 Я Хлопець", "👩 Я Дівчина", "🙋‍♂️ Шукаю Хлопця", "🙋‍♀️ Шукаю Дівчину", "🌍 Шукаю Будь-кого", "⬅️ В головне меню"]:
            await message.answer("Поки що ти ні з ким не спілкуєшся. Скористайся меню нижче 👇", reply_markup=get_main_menu())

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
