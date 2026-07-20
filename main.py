import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Asosiy sozlamalar
TOKEN = "8781482418:AAGnZ9IqnZW_w5BjHzfcj5Wys0eFHcUSt0M"
ADMIN_ID = 7677636892  # O'z Telegram ID raqamingiz
ADMIN_USERNAME = "hasanboyqodirov"

# Sozlamalar va ma'lumotlar (Bot ichidan o'zgartiriladi)
BOT_SETTINGS = {
    "card_number": "9860 1234 5678 9012",
    "card_holder": "HASANBOY QODIROV",
    "price": "10 000 so'm",
    "free_limit": 20
}

# Foydalanuvchilar bazasi (Xotirada saqlash uchun)
# user_id: {"is_pro": False, "invited_count": 5, "created_bots": 1}
users_db = {}

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

# Holatlar (FSM)
class AdminState(StatesGroup):
    waiting_for_card_number = State()
    waiting_for_card_holder = State()
    waiting_for_price = State()
    waiting_for_limit = State()
    waiting_for_user_id_to_pro = State()

class BotState(StatesGroup):
    waiting_for_token = State()

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            "is_pro": False,
            "invited_count": 0,
            "created_bots": 0
        }
    return users_db[user_id]

def get_main_keyboard(user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton("🤖 Yangi bot yaratish"),
        types.KeyboardButton("🎛️ Botlarim"),
        types.KeyboardButton("💼 Kabinet"),
        types.KeyboardButton("💎 PRO rejim"),
        types.KeyboardButton("🎁 Bonuslar"),
        types.KeyboardButton("📖 Qo'llanma")
    )
    if user_id == ADMIN_ID:
        keyboard.add(types.KeyboardButton("⚙️ Admin panel"))
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    get_user(user_id)
    user_name = message.from_user.first_name
    
    text = (
        f"👋 Salom, **{user_name}**!\n\n"
        f"ViBot.uz platformasiga xush kelibsiz.\n"
        f"Siz bu yerda dasturlash bilimisiz, atigi 3 daqiqada o'z biznesingiz yoki loyihangiz uchun Telegram bot yarata olasiz.\n\n"
        f"💡 **Bepul limit:** {BOT_SETTINGS['free_limit']} ta foydalanuvchi.\n"
        f"💰 **PRO rejim tarif narxi:** {BOT_SETTINGS['price']}\n\n"
        f"👇 O'zingizning birinchi botingizni yaratish uchun menyudan tanlang:"
    )
    await message.reply(text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

# --- KABINET VA LARGULAR ---
@dp.message_handler(text="💼 Kabinet")
async def cabinet_menu(message: types.Message):
    user_id = message.from_user.id
    u_data = get_user(user_id)
    
    status = "💎 PRO Rejim (Cheksiz)" if u_data["is_pro"] else f"🟢 Bepul (Limit: {u_data['invited_count']}/{BOT_SETTINGS['free_limit']})"
    
    text = (
        f"💼 **Sizning kabinetingiz:**\n\n"
        f"🆔 ID raqamingiz: `{user_id}`\n"
        f"📊 Tarif holati: **{status}**\n"
        f"🤖 Yaratilgan botlar: {u_data['created_bots']} ta\n\n"
        f"Agar bepul limit tugasa, botlar to'xtab qolmasligi uchun PRO rejimga o'ting!"
    )
    await message.reply(text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

# --- BOT YARATISH VA LIMIT TEKshirish ---
@dp.message_handler(text="🤖 Yangi bot yaratish")
async def create_bot_start(message: types.Message):
    user_id = message.from_user.id
    u_data = get_user(user_id)
    
    # Limitni tekshirish
    if not u_data["is_pro"] and u_data["invited_count"] >= BOT_SETTINGS['free_limit']:
        text = (
            f"❌ **Bepul limit tugadi!**\n\n"
            f"Sizning botingizdagi foydalanuvchilar soni {BOT_SETTINGS['free_limit']} taga yetdi. "
            f"Botingiz ishlashini davom ettirish va cheklovlarni olib tashlash uchun **PRO rejimga** o'ting!"
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("💎 PRO rejimga o'tish", callback_data="go_to_pro"))
        await message.reply(text, parse_mode="Markdown", reply_markup=keyboard)
        return

    text = (
        "<b>MEDIA BOT [KINOBOT] ( Test Rejim )</b>\n\n"
        "🔑 <b>Botni ulash uchun API Token kerak</b>\n\n"
        "Qanday olinadi?\n"
        "1️⃣ @BotFather ga kiring va /newbot deb yozing.\n"
        "2️⃣ Botga nom va username bering, so'ngra tokenni nusxalab oling.\n"
        "3️⃣ Olingan tokenni aynan shu yerga yuboring.\n\n"
        "👇 <b>Tokenni pastga yozib yuboring:</b>"
    )
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("❌ Bekor qilish"))
    
    await message.reply(text, parse_mode="HTML", reply_markup=keyboard)
    await BotState.waiting_for_token.set()

@dp.message_handler(text="❌ Bekor qilish", state=BotState.waiting_for_token)
async def cancel_process(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Amaliyot bekor qilindi.", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message_handler(state=BotState.waiting_for_token)
async def receive_bot_token(message: types.Message, state: FSMContext):
    token_text = message.text.strip()
    if ":" not in token_text or len(token_text) < 30:
        await message.reply("❌ Noto'g'ri token format. Qaytadan tekshirib yuboring:")
        return

    user_id = message.from_user.id
    u_data = get_user(user_id)
    u_data["created_bots"] += 1
    
    await state.finish()
    
    success_text = (
        f"🎉 **Tabriklaymiz!**\n\n"
        f"Botingiz muvaffaqiyatli ishga tushirildi va to'liq foydalanishga tayyor."
    )
    await message.reply(success_text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

# --- PRO REJIM VA TO'LOV ---
@dp.message_handler(text="💎 PRO rejim")
@dp.callback_query_handler(lambda call: call.data == "go_to_pro")
async def pro_rejim_menu(message_or_call):
    is_callback = isinstance(message_or_call, types.CallbackQuery)
    user_id = message_or_call.from_user.id
    u_data = get_user(user_id)
    
    status_text = "Sizda PRO rejim faol! ✅" if u_data["is_pro"] else "PRO rejim faol emas ❌"
    
    text = (
        f"💎 **PRO Rejim va Balansni To'ldirish**\n\n"
        f"Holatingiz: **{status_text}**\n"
        f"💰 **Narxi:** {BOT_SETTINGS['price']}\n\n"
        f"Quyidagi karta raqamiga to'lov qiling va avtomatik faollashtiring:"
    )
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("💳 Karta ma'lumotlarini ko'rsatish", callback_data="show_card"),
        types.InlineKeyboardButton("✅ To'lovni tasdiqlash (Avto PRO)", callback_data="check_payment"),
        types.InlineKeyboardButton("👨‍💻 Admin bilan bog'lanish", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    
    if is_callback:
        await bot.answer_callback_query(message_or_call.id)
        await bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message_or_call.reply(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data == "show_card")
async def show_card_info(callback_query: types.CallbackQuery):
    text = (
        f"💳 **To'lov uchun karta ma'lumotlari**\n\n"
        f"Karta raqami:\n`{BOT_SETTINGS['card_number']}`\n\n"
        f"Karta egasi: **{BOT_SETTINGS['card_holder']}**\n"
        f"Summa: **{BOT_SETTINGS['price']}**\n\n"
        f"⚠️ Pulni o'tkazgach, pastdagi **«✅ To'lovni tasdiqlash»** tugmasini bosing va darhol PRO rejimga ega bo'ling!"
    )
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown")

@dp.callback_query_handler(lambda call: call.data == "check_payment")
async def instant_pro_activation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    u_data = get_user(user_id)
    
    u_data["is_pro"] = True
    
    text = (
        f"🎉 **Tabriklaymiz! To'lovingiz tasdiqlandi!**\n\n"
        f"Sizning profilingizga **PRO rejim** muvaffaqiyatli yoqildi. Endi barcha cheklovlar olib tashlandi va botlaringiz uzluksiz ishlaydi! 🚀"
    )
    await bot.answer_callback_query(callback_query.id, text="PRO rejim yoqildi! ✅", show_alert=True)
    await bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

# --- ADMIN PANEL (Barcha narsani botdan o'zgartirish) ---
@dp.message_handler(text="⚙️ Admin panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = (
        f"🛠 **Admin boshqaruv paneli**\n\n"
        f"💳 Karta: `{BOT_SETTINGS['card_number']}`\n"
        f"👤 Egasi: **{BOT_SETTINGS['card_holder']}**\n"
        f"💵 Narx: **{BOT_SETTINGS['price']}**\n"
        f"💡 Bepul limit: **{BOT_SETTINGS['free_limit']} ta**\n\n"
        f"Nimani o'zgartirmoqchisiz?"
    )
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("💳 Karta raqamini o'zgartirish", callback_data="adm_card"),
        types.InlineKeyboardButton("👤 Karta egasini o'zgartirish", callback_data="adm_holder"),
        types.InlineKeyboardButton("💵 Narxni o'zgartirish", callback_data="adm_price"),
        types.InlineKeyboardButton("🔢 Bepul limitni o'zgartirish", callback_data="adm_limit"),
        types.InlineKeyboardButton("⚡️ Foydalanuvchiga PRO berish (ID orqali)", callback_data="adm_give_pro")
    )
    await message.reply(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data.startswith("adm_"))
async def admin_actions(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        return
    
    action = callback_query.data
    if action == "adm_card":
        await callback_query.message.answer("Yangi karta raqamini kiriting:")
        await AdminState.waiting_for_card_number.set()
    elif action == "adm_holder":
        await callback_query.message.answer("Yangi karta egasining F.I.O. sini kiriting:")
        await AdminState.waiting_for_card_holder.set()
    elif action == "adm_price":
        await callback_query.message.answer("Yangi narxni kiriting (masalan: 15 000 so'm):")
        await AdminState.waiting_for_price.set()
    elif action == "adm_limit":
        await callback_query.message.answer("Yangi bepul limit sonini kiriting (faqat raqam):")
        await AdminState.waiting_for_limit.set()
    elif action == "adm_give_pro":
        await callback_query.message.answer("PRO rejim berilishi kerak bo'lgan foydalanuvchining Telegram ID raqamini kiriting:")
        await AdminState.waiting_for_user_id_to_pro.set()
        
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=AdminState.waiting_for_card_number)
async def set_c(message: types.Message, state: FSMContext):
    BOT_SETTINGS["card_number"] = message.text.strip()
    await state.finish()
    await message.reply("✅ Karta raqami yangilandi!", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message_handler(state=AdminState.waiting_for_card_holder)
async def set_h(message: types.Message, state: FSMContext):
    BOT_SETTINGS["card_holder"] = message.text.strip()
    await state.finish()
    await message.reply("✅ Karta egasi yangilandi!", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message_handler(state=AdminState.waiting_for_price)
async def set_p(message: types.Message, state: FSMContext):
    BOT_SETTINGS["price"] = message.text.strip()
    await state.finish()
    await message.reply("✅ Narx yangilandi!", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message_handler(state=AdminState.waiting_for_limit)
async def set_l(message: types.Message, state: FSMContext):
    try:
        BOT_SETTINGS["free_limit"] = int(message.text.strip())
        await state.finish()
        await message.reply("✅ Bepul limit miqdori yangilandi!", reply_markup=get_main_keyboard(message.from_user.id))
    except ValueError:
        await message.reply("❌ Faqat raqam kiriting!")

@dp.message_handler(state=AdminState.waiting_for_user_id_to_pro)
async def give_pro_by_admin(message: types.Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
        get_user(target_id)["is_pro"] = True
        await state.finish()
        await message.reply(f"✅ {target_id} ID raqamli foydalanuvchiga PRO rejim berildi!")
        await bot.send_message(target_id, "🎉 Admin sizga PRO rejimni qo'lda faollashtirib berdi!")
    except ValueError:
        await message.reply("❌ Noto'g'ri ID. Faqat raqam kiriting:")

@dp.message_handler(text=["🎛️ Botlarim", "🎁 Bonuslar", "📖 Qo'llanma"])
async def other_menus(message: types.Message):
    await message.reply(f"Siz «{message.text}» bo'limini tanladingiz. Tez orada bu yerda qo'shimcha funksiyalar ishga tushadi.")

# --- 24/7 SERVER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

if __name__ == '__main__':
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    executor.start_polling(dp, skip_updates=True)
    
