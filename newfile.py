import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ChatJoinRequest
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# =========================================================
# ⚙️ SOZLAMALAR
# =========================================================
BOT_TOKEN = "8751774068:AAHH64FrKaYMDiL7i0ikFMEp4AetCH2KO48"
ADMIN_ID = 8311805467  # O'zingizning Telegram ID'ingizni tekshirib ko'ring
DATA_FILE = "bot_data.json"
MAIN_CHANNEL_LINK = "https://t.me/kinolarolamiyuu"

CHANNELS = [
    {"id": -1004426792886, "link": "https://t.me/+-_k_teqqLkdmMThi"},
    {"id": -1004371606396, "link": "https://t.me/+2Zb7IFxIx-kwZWYy"}
]
# =========================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM Bosqichlari
class AdminStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_video = State()
    waiting_for_caption = State()
    waiting_for_delete_code = State()

# =========================================================
# 📦 FAJL BILAN ISHLASH
# =========================================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "movies": {}, "join_requests": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# =========================================================
# 🛠 YORDAMCHI TUGMALAR VA FUNKSIYALAR
# =========================================================
async def check_subscriptions(user_id: int) -> list:
    unsubscribed = []
    for ch in CHANNELS:
        if [user_id, ch["id"]] in db["join_requests"]:
            continue
        try:
            member = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                unsubscribed.append(ch)
        except Exception as e:
            logging.error(f"Kanalni tekshirishda xatolik: {e}")
            unsubscribed.append(ch)
    return unsubscribed

def main_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="🔍 Kino izlash yo'riqnomasi", callback_data="search_info")]]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi kino qo'shish", callback_data="add_movie")],
        [InlineKeyboardButton(text="🗑 Kinoni o'chirish", callback_data="delete_movie")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="back_main")]
    ])

def get_movie_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😍🎲 MULTFILM", url=MAIN_CHANNEL_LINK),
            InlineKeyboardButton(text="🎥🎲 KINO", url=MAIN_CHANNEL_LINK)
        ],
        [
            InlineKeyboardButton(text="📢 Asosiy kanalimiz", url=MAIN_CHANNEL_LINK)
        ]
    ])

# =========================================================
# 📩 HANDLERLAR
# =========================================================

# Zayavkalarni ushlash
@dp.chat_join_request()
async def join_request_handler(event: ChatJoinRequest):
    req = [event.from_user.id, event.chat.id]
    if req not in db["join_requests"]:
        db["join_requests"].append(req)
        save_data(db)

# /start buyrug'i
@dp.message(CommandStart())
async def start_cmd(msg: Message):
    if msg.from_user.id not in db["users"]:
        db["users"].append(msg.from_user.id)
        save_data(db)

    unsubscribed = await check_subscriptions(msg.from_user.id)
    if unsubscribed:
        buttons = []
        for i, ch in enumerate(unsubscribed, start=1):
            buttons.append([InlineKeyboardButton(text=f"📩 {i}-Kanalga zayavka yuborish", url=ch["link"])])
        buttons.append([InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_sub")])
        
        await msg.answer(
            "📌 **Botdan foydalanish uchun quyidagi kanallarga zayavka yuboring:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="Markdown"
        )
        return

    is_admin = (msg.from_user.id == ADMIN_ID)
    await msg.answer(
        f"Xush kelibsiz, **{msg.from_user.first_name}**!\n\nKino ko'rish uchun kino kodini yuboring:",
        reply_markup=main_keyboard(is_admin),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(call: CallbackQuery):
    unsubscribed = await check_subscriptions(call.from_user.id)
    if unsubscribed:
        await call.answer("❌ Hali barcha kanallarga zayavka yubormadingiz!", show_alert=True)
    else:
        await call.message.delete()
        is_admin = (call.from_user.id == ADMIN_ID)
        await call.message.answer(
            "✅ **A'zolik/Zayavka tasdiqlandi!**\nKino kodini yuborishingiz mumkin:",
            reply_markup=main_keyboard(is_admin),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "search_info")
async def search_info(call: CallbackQuery):
    await call.answer()
    await call.message.answer("🔍 Kino kodini raqam ko'rinishida yuboring (Masalan: `101`).")

# Admin Panel navigatsiyasi
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.edit_text("⚙️ **Admin Panel:**", reply_markup=admin_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("📌 **Bosh menyu.** Kodni yuboring:", reply_markup=main_keyboard(True), parse_mode="Markdown")

@dp.callback_query(F.data == "stats")
async def stats_handler(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    users_cnt = len(db["users"])
    movies_cnt = len(db["movies"])
    await call.answer(f"📊 Statistika:\n👥 Foydalanuvchilar: {users_cnt}\n🎬 Kinolar: {movies_cnt}", show_alert=True)

# ➕ KINO QO'SHISH (Kod -> Video -> Tasnif)
@dp.callback_query(F.data == "add_movie")
async def add_movie_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.waiting_for_code)
    await call.message.edit_text(
        "🔢 **1. Yangi kino kodini kiriting:**\n(Masalan: `101`)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_panel")]]),
        parse_mode="Markdown"
    )

@dp.message(AdminStates.waiting_for_code)
async def process_code(msg: Message, state: FSMContext):
    code = msg.text.strip()
    if code in db["movies"]:
        await msg.answer("⚠️ Bu kod bilan kino allaqachon mavjud! Boshqa kod kiriting:")
        return
    await state.update_data(code=code)
    await state.set_state(AdminStates.waiting_for_video)
    await msg.answer("📹 **2. Endi ushbu kodga mos video faylini yuboring:**", parse_mode="Markdown")

@dp.message(AdminStates.waiting_for_video, F.video)
async def process_video(msg: Message, state: FSMContext):
    await state.update_data(file_id=msg.video.file_id)
    await state.set_state(AdminStates.waiting_for_caption)
    await msg.answer("📝 **3. Endi kino tasnifini (matnini) kiriting:**\n\n*(Agar tasnif kerak bo'lmasa `-` belgisini yuboring)*", parse_mode="Markdown")

@dp.message(AdminStates.waiting_for_caption)
async def process_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    code = data['code']
    file_id = data['file_id']
    
    caption_text = msg.text if msg.text != "-" else ""
    
    db["movies"][code] = {
        "file_id": file_id,
        "caption": caption_text
    }
    save_data(db)
    
    await state.clear()
    await msg.answer(f"✅ **Kino muvaffaqiyatli saqlandi!**\n🔑 Kodi: `{code}`", reply_markup=admin_keyboard(), parse_mode="Markdown")

# 🗑 KINO O'CHIRISH
@dp.callback_query(F.data == "delete_movie")
async def delete_movie_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.waiting_for_delete_code)
    await call.message.edit_text(
        "🗑 **O'chirmoqchi bo'lgan kino kodini kiriting:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_panel")]]),
        parse_mode="Markdown"
    )

@dp.message(AdminStates.waiting_for_delete_code)
async def process_delete(msg: Message, state: FSMContext):
    code = msg.text.strip()
    await state.clear()
    
    if code in db["movies"]:
        del db["movies"][code]
        save_data(db)
        await msg.answer(f"🗑 Kodi `{code}` bo'lgan kino o'chirildi!", reply_markup=admin_keyboard(), parse_mode="Markdown")
    else:
        await msg.answer("❌ Bunday kodli kino topilmadi.", reply_markup=admin_keyboard())

# 🔍 FOYDALANUVCHIGA KINO YUBORISH
@dp.message(F.text & ~F.text.startswith('/'))
async def find_movie(msg: Message):
    unsubscribed = await check_subscriptions(msg.from_user.id)
    if unsubscribed:
        await msg.answer("⚠️ Kino ko'rish uchun avval kanallarga zayavka yuboring.")
        return

    code = msg.text.strip()
    if code in db["movies"]:
        movie_data = db["movies"][code]
        
        if isinstance(movie_data, dict):
            video_id = movie_data["file_id"]
            custom_caption = movie_data.get("caption", "")
        else:
            video_id = movie_data
            custom_caption = ""

        text_caption = f"🎬 **Kino kodi:** `{code}`\n"
        if custom_caption:
            text_caption += f"\n📝 **Tasnif:**\n{custom_caption}\n"
        text_caption += "\n🍿 Yoqimli tomosha tilaymiz!"

        await msg.answer_video(
            video=video_id,
            caption=text_caption,
            reply_markup=get_movie_inline_keyboard(),  # Video ostidagi tugmalar
            parse_mode="Markdown"
        )
    else:
        await msg.answer("❌ **Bunday kodli kino topilmadi.**")

# =========================================================
# 🚀 ISHGA TUSHIRISH
# =========================================================
async def main():
    print("🚀 Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
