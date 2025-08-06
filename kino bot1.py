import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, StateFilter
from aiogram.client.default import DefaultBotProperties
import os

API_TOKEN = "8074451053:AAGe1HKCMUWqA5UmuiBll5lkJbWWqzU-Vqw"  # Bot tokenni bu yerga yozing
CHANNEL_ID = -1002839351049  # Majburiy obuna uchun kanal ID
ADMIN_ID = 7721380244  # Admin ID bu yerga

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar saqlash
users = set()
movies = {}
series = {}

# Holatlar
class UploadMovie(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()

class UploadSeries(StatesGroup):
    waiting_for_lang = State()
    waiting_for_quality = State()
    waiting_for_title = State()
    waiting_for_count = State()
    waiting_for_episodes = State()
    waiting_for_series_code = State()

# Inline tugmalar
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Kino yuklash", callback_data="upload_movie")],
        [InlineKeyboardButton(text="🎞 Serial yuklash", callback_data="upload_series")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")]
    ])

def user_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Admin bilan bogʻlanish", url="https://t.me/sevinchbek001")],
        [InlineKeyboardButton(text="☕ Donat", url="https://t.me/Anime_Koprik_Reklama")],
        [InlineKeyboardButton(text="🔍 Kino qidirish", switch_inline_query_current_chat="")]
    ])

# Majburiy obuna tekshiruvi
async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@dp.message(Command("start"))
async def cmd_start(message: Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        return await message.answer("👋 Avvalo kanalimizga obuna bo'ling: https://t.me/AnimeKoprik")

    users.add(message.from_user.id)

    if message.from_user.id == ADMIN_ID:
        await message.answer("Assalomu alaykum, admin!", reply_markup=main_keyboard())
    else:
        await message.answer("Xush kelibsiz!", reply_markup=user_keyboard())

# --- Kino yuklash ---
@dp.callback_query(F.data == "upload_movie")
async def cb_upload_movie(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Faqat admin uchun!", show_alert=True)

    await callback.message.answer("🎥 Kinoni yuboring")
    await state.set_state(UploadMovie.waiting_for_video)

@dp.message(UploadMovie.waiting_for_video)
async def get_movie_video(message: Message, state: FSMContext):
    if not message.video:
        return await message.answer("Video yuboring")

    await state.update_data(video=message.video)
    await message.answer("Kino uchun kodni yuboring")
    await state.set_state(UploadMovie.waiting_for_code)

@dp.message(UploadMovie.waiting_for_code)
async def get_movie_code(message: Message, state: FSMContext):
    data = await state.get_data()
    code = message.text
    movies[code] = data["video"]
    await message.answer(f"✅ Kino kod bilan saqlandi: {code}")
    await state.clear()

# --- Serial yuklash ---
@dp.callback_query(F.data == "upload_series")
async def cb_upload_series(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Faqat admin uchun!", show_alert=True)

    await callback.message.answer("🌐 Tilni yozing:")
    await state.set_state(UploadSeries.waiting_for_lang)

@dp.message(UploadSeries.waiting_for_lang)
async def get_lang(message: Message, state: FSMContext):
    await state.update_data(lang=message.text)
    await message.answer("📽 Sifatni yozing (masalan: 1080p):")
    await state.set_state(UploadSeries.waiting_for_quality)

@dp.message(UploadSeries.waiting_for_quality)
async def get_quality(message: Message, state: FSMContext):
    await state.update_data(quality=message.text)
    await message.answer("🎞 Serial nomini kiriting:")
    await state.set_state(UploadSeries.waiting_for_title)

@dp.message(UploadSeries.waiting_for_title)
async def get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Nechta qism bor?")
    await state.set_state(UploadSeries.waiting_for_count)

@dp.message(UploadSeries.waiting_for_count)
async def get_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
    except:
        return await message.answer("Iltimos, butun son kiriting")

    await state.update_data(count=count, episodes=[])
    await message.answer("1-qismni yuboring")
    await state.set_state(UploadSeries.waiting_for_episodes)

@dp.message(UploadSeries.waiting_for_episodes)
async def get_episodes(message: Message, state: FSMContext):
    data = await state.get_data()
    episodes = data["episodes"]
    episodes.append(message.video)
    await state.update_data(episodes=episodes)

    if len(episodes) >= data["count"]:
        await message.answer("🔢 Endi kodni yuboring:")
        await state.set_state(UploadSeries.waiting_for_series_code)
    else:
        await message.answer(f"{len(episodes)+1}-qismni yuboring")

@dp.message(UploadSeries.waiting_for_series_code)
async def get_series_code(message: Message, state: FSMContext):
    data = await state.get_data()
    code = message.text
    series[code] = {
        "lang": data["lang"],
        "quality": data["quality"],
        "title": data["title"],
        "episodes": data["episodes"]
    }
    await message.answer(f"✅ Serial saqlandi: {code}")
    await state.clear()

# --- Kod orqali kino yoki serial ---
@dp.message()
async def process_code(message: Message):
    code = message.text

    if code in movies:
        await message.answer_video(movies[code].file_id)
    elif code in series:
        s = series[code]
        await message.answer(f"🎞 {s['title']}\n🌐 {s['lang']} | 📽 {s['quality']}\nQismlar quyida")
        for idx, ep in enumerate(s['episodes'], start=1):
            await message.answer_video(ep.file_id, caption=f"{idx}-qism")
    else:
        await message.answer("❌ Bunday kod topilmadi")

# --- Statistika ---
@dp.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Faqat admin uchun!", show_alert=True)

    await callback.message.answer(f"📊 Foydalanuvchilar: {len(users)}\n🎬 Kinolar: {len(movies)}\n🎞 Serialar: {len(series)}")

# --- Botni ishga tushurish ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
