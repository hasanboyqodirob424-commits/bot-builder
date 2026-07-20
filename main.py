import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp import web

# Ma'lumotlar
TOKEN = "8781482418:AAGnZ9IqnZW_w5BjHzfcj5Wys0eFHcUSt0M"
ADMIN_ID = 7677636892
ADMIN_USERNAME = "hasanboyqodirov"

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

# Holatlar (FSM)
class BuilderState(StatesGroup):
    waiting_for_token = State()

# Asosiy menyu tugmalari
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton("🤖 Yangi bot yaratish"),
        types.KeyboardButton("🎛️ Botlarim"),
        types.KeyboardButton("💼 Kabinet"),
        types.KeyboardButton("💎 PRO rejim (10 000 so'm)"),
        types.KeyboardButton("🎁 Bonuslar"),
        types.KeyboardButton("📖 Qo'llanma")
    )
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_name = message.from_user.first_name
    text = (
        f"👋 Salom, **{user_name}**!\n\n"
        f"ViBot.uz platformasiga xush kelibsiz.\n"
        f"Siz bu yerda dasturlash bilimisiz, atigi 3 daqiqada o'z biznesingiz yoki loyihangiz uchun Telegram bot yarata olasiz.\n\n"
        f"💡 **Bepul limit:** 20 ta foydalanuvchi.\n"
        f"💰 **PRO rejim:** Oyiga atigi **10 000 so'm**!\n\n"
        f"👇 O'zingizning birinchi botingizni yaratish uchun menyudan tanlang:"
    )
    await message.reply(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message_handler(text="🤖 Yangi bot yaratish")
async def create_bot_start(message: types.Message):
    text = (
        "<b>MEDIA BOT [KINOBOT] ( Test Rejim )</b>\n\n"
        "🔑 <b>Botni ulash uchun API Token kerak</b>\n\n"
        "Qanday olinadi?\n"
        "1️⃣ @BotFather ga kiring va /newbot deb yozing.\n"
        "2️⃣ Botga nom va username bering, so'ngra tokenni nusxalab oling.\n"
        "3️⃣ Olingan tokenni aynan shu yerga yuboring.\n\n"
        "<i>Namuna:</i>\n<code>1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ</code>\n\n"
        "👇 <b>Tokenni pastga yozib yuboring:</b>"
    )
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("❌ Bekor qilish"))
    
    await message.reply(text, parse_mode="HTML", reply_markup=keyboard)
    await BuilderState.waiting_for_token.set()

@dp.message_handler(text="❌ Bekor qilish", state=BuilderState.waiting_for_token)
async def cancel_process(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Amaliyot bekor qilindi.", reply_markup=get_main_keyboard())

@dp.message_handler(state=BuilderState.waiting_for_token)
async def receive_bot_token(message: types.Message, state: FSMContext):
    token_text = message.text.strip()
    
    if ":" not in token_text or len(token_text) < 30:
        await message.reply("❌ Noto'g'ri token format kiritildi. Iltimos, @BotFather'dan olingan tokerni to'g'ri nusxalab yuboring:")
        return

    await state.finish()
    
    success_text = (
        f"🎉 **Tabriklaymiz!**\n\n"
        f"Botingiz muvaffaqiyatli ishga tushirildi. Endi botingizga kirib, ishni boshlashingiz mumkin."
    )
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🚀 Botni ochish", url=f"https://t.me/BotFather"))
    keyboard.add(types.InlineKeyboardButton("🔙 Bosh menyuga qaytish", callback_data="main_menu"))

    await message.reply(success_text, parse_mode="Markdown", reply_markup=keyboard)
    await message.answer("Boshqaruv paneliga xush kelibsiz:", reply_markup=get_main_keyboard())

@dp.message_handler(text="💎 PRO rejim (10 000 so'm)")
async def pro_rejim_menu(message: types.Message):
    text = (
        "💎 **PRO Rejim va Balansni To'ldirish**\n\n"
        "Botdagi 20 ta bepul limit tugaganda yoki botingiz cheklovsiz ishlashi uchun PRO tarifini yoqing.\n"
        "💰 **Narxi:** 10 000 so'm / oy\n\n"
        "To'lov qilish uchun quyidagi kartalardan birini tanlang yoki admin bilan bog'laning:"
    )
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💳 HUMO orqali to'lash", callback_data="pay_humo"),
        types.InlineKeyboardButton("💳 UZCARD orqali to'lash", callback_data="pay_uzcard")
    )
    keyboard.add(
        types.InlineKeyboardButton("👨‍💻 Admin bilan bog'lanish", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    
    await message.reply(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data in ["pay_humo", "pay_uzcard"])
async def process_payment(callback_query: types.CallbackQuery):
    card_type = "HUMO" if callback_query.data == "pay_humo" else "UZCARD"
    card_number = "9860 1234 5678 9012" # O'z karta raqamingizni yozasiz
    card_holder = "HASANBOY QODIROV"     # Karta egasining ismi
    
    text = (
        f"💳 **{card_type} karta raqami orqali to'lov**\n\n"
        f"Karta raqami:\n`{card_number}`\n\n"
        f"Karta egasi: **{card_holder}**\n"
        f"Summa: **10 000 so'm**\n\n"
        f"⚠️ **Diqqat:** Pulni o'tkazgach, chek (skrinshot) rasmini **@hasanboyqodirov** ga yuboring. Admin tezda PRO rejimni faollashtirib beradi!"
    )
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📤 Chekni adminga yuborish", url=f"https://t.me/{ADMIN_USERNAME}"))
    
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown", reply_markup=keyboard)

@dp.message_handler(text=["🎛️ Botlarim", "💼 Kabinet", "🎁 Bonuslar", "📖 Qo'llanma"])
async def other_menus(message: types.Message):
    await message.reply(f"Siz «{message.text}» bo'limini tanladingiz. Tez orada bu yerda to'liq boshqaruv paneli ishga tushadi.")

# --- 24/7 UZLUKSIZ ISHLASH UCHUN WEB SERVER ---
async def handle(request):
    return web.Response(text="Bot is running 24/7!")

async def web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.AppSite(runner, "0.0.0.0", port)
    await site.start()

async def on_startup(dispatcher):
    await web_server()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
  
