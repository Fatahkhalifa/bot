
import telebot
from telebot import types
import time
import os

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

users = {}
products = []

SUB_DURATION = {
    "free": 7,
    "pro": 30,
    "premium": 3650
}

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in users:
        users[chat_id] = {"subscription": "free"}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 تصفح السوق", "➕ عرض منتج للبيع")
    markup.add("⭐ الاشتراك")
    bot.send_message(chat_id, "أهلاً بك في سوق البوت 👋", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "⭐ الاشتراك")
def show_subscription(msg):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("مجاني", callback_data="sub_free"))
    markup.add(types.InlineKeyboardButton("محترف - 500 دج", callback_data="sub_pro"))
    markup.add(types.InlineKeyboardButton("متقدم - 1000 دج", callback_data="sub_premium"))
    bot.send_message(msg.chat.id, "اختر نوع الاشتراك:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def handle_subscription(call):
    level = call.data.split("_")[1]
    if level == "free":
        users[call.message.chat.id]["subscription"] = "free"
        bot.send_message(call.message.chat.id, "تم تفعيل الاشتراك المجاني ✅")
    else:
        price = "500 دج" if level == "pro" else "1000 دج"
        msg = f"💳 للدفع عبر BaridiMob:
💰 المبلغ: {price}
📞 الرقم: 0770xxxxxx
ثم أرسل لقطة شاشة للتأكيد."
        users[call.message.chat.id]["subscription"] = level
        bot.send_message(call.message.chat.id, msg)

@bot.message_handler(func=lambda msg: msg.text == "➕ عرض منتج للبيع")
def add_product_step1(msg):
    chat_id = msg.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📱 هواتف", "👕 ملابس", "🚗 سيارات")
    markup.add("🧸 ألعاب", "🍽️ أواني", "🛵 دراجات")
    markup.add("💍 إكسسوارات", "📦 أخرى")
    users[chat_id]["state"] = "select_category"
    bot.send_message(chat_id, "اختر نوع المنتج:", reply_markup=markup)

@bot.message_handler(func=lambda msg: users.get(msg.chat.id, {}).get("state") == "select_category")
def receive_category(msg):
    chat_id = msg.chat.id
    users[chat_id]["new_product"] = {"category": msg.text}
    users[chat_id]["state"] = "enter_title"
    bot.send_message(chat_id, "أدخل عنوان المنتج:")

@bot.message_handler(func=lambda msg: users.get(msg.chat.id, {}).get("state") == "enter_title")
def receive_title(msg):
    chat_id = msg.chat.id
    users[chat_id]["new_product"]["title"] = msg.text
    users[chat_id]["state"] = "enter_price"
    bot.send_message(chat_id, "أدخل سعر المنتج:")

@bot.message_handler(func=lambda msg: users.get(msg.chat.id, {}).get("state") == "enter_price")
def receive_price(msg):
    chat_id = msg.chat.id
    try:
        price = int(msg.text)
        users[chat_id]["new_product"]["price"] = price
        users[chat_id]["state"] = "awaiting_photo"
        bot.send_message(chat_id, "أرسل صورة المنتج الآن:")
    except:
        bot.send_message(chat_id, "❌ السعر غير صحيح. حاول مرة أخرى.")

@bot.message_handler(content_types=["photo"])
def receive_photo(msg):
    chat_id = msg.chat.id
    if users.get(chat_id, {}).get("state") == "awaiting_photo":
        file_id = msg.photo[-1].file_id
        new_product = users[chat_id]["new_product"]
        new_product["photo"] = file_id
        new_product["seller_id"] = chat_id
        new_product["timestamp"] = time.time()
        sub = users[chat_id].get("subscription", "free")
        new_product["duration_days"] = SUB_DURATION.get(sub, 7)
        new_product["featured"] = sub in ["pro", "premium"]
        products.append(new_product)
        users[chat_id]["state"] = None
        bot.send_message(chat_id, "✅ تم نشر المنتج في السوق!")

@bot.message_handler(func=lambda msg: msg.text == "🛒 تصفح السوق")
def browse_market(msg):
    markup = types.InlineKeyboardMarkup()
    for cat in ["📱 هواتف", "👕 ملابس", "🚗 سيارات", "🧸 ألعاب", "🍽️ أواني", "🛵 دراجات", "💍 إكسسوارات", "📦 أخرى"]:
        markup.add(types.InlineKeyboardButton(cat, callback_data=f"category_{cat}"))
    bot.send_message(msg.chat.id, "اختر نوع المنتجات:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def show_category_products(call):
    category = call.data.split("_", 1)[1]
    now = time.time()
    results = [p for p in products if p["category"] == category and now < p["timestamp"] + p["duration_days"] * 86400]
    if not results:
        bot.send_message(call.message.chat.id, "لا توجد منتجات حاليًا في هذا الصنف.")
        return
    for p in results:
        caption = f"📦 {p['title']}
💰 السعر: {p['price']} دج
📂 الصنف: {p['category']}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 طلب المنتج", callback_data="order"))
        bot.send_photo(call.message.chat.id, p["photo"], caption=caption, reply_markup=markup)

print("🚀 البوت قيد التشغيل...")
bot.polling()
