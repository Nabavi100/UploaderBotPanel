import os
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = "8193120697:AAE291HpctzLxdL6E7GXLoFyIQK2Qr1hDdg"
CHANNEL_ID = "-1002864976696"
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_code():
    return f"FILE{random.randint(1000, 9999)}"

def format_file_info(entry):
    date = entry['date']
    ftype = entry['type']
    code = entry['code']
    name = entry['name']
    return f"📦 `{code}` | {ftype} | 📅 {date} | {name}"

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document or (update.message.photo[-1] if update.message.photo else None)
    if not file:
        return

    file_id = file.file_id
    file_type = "Document" if update.message.document else "Photo"
    file_name = getattr(file, 'file_name', 'photo.jpg')
    file_size = getattr(file, 'file_size', 0)

    code = generate_code()
    date_str = datetime.now().strftime("%Y-%m-%d")

    # ارسال به کانال
    if file_type == "Document":
        caption = f"📁 کد فایل: {code}\n📝 {file_name}"
        sent = await context.bot.send_document(chat_id=CHANNEL_ID, document=file_id, caption=caption)
    else:
        caption = f"🖼 کد عکس: {code}"
        sent = await context.bot.send_photo(chat_id=CHANNEL_ID, photo=file_id, caption=caption)

    # ذخیره دیتا
    data = load_data()
    data.append({
        "code": code,
        "type": file_type,
        "name": file_name,
        "date": date_str,
        "size": file_size,
        "channel_message_id": sent.message_id
    })
    save_data(data)

    link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{sent.message_id}"
    keyboard = [[InlineKeyboardButton("📎 باز کردن فایل", url=link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"✅ فایل ذخیره شد!\nکد شما: `{code}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_code_or_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()
    result = []

    for entry in data:
        if text.lower() in entry['code'].lower() or text.lower() in entry['name'].lower():
            result.append(entry)

    if result:
        msg = "\n".join([format_file_info(r) for r in result[:5]])
        await update.message.reply_text(f"🔎 نتایج جستجو:\n{msg}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ هیچ فایلی با این مشخصات پیدا نشد.")

async def command_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    count = len(data)
    total_size = sum([entry['size'] for entry in data])
    total_mb = round(total_size / (1024 * 1024), 2)
    doc_count = sum(1 for e in data if e["type"] == "Document")
    photo_count = sum(1 for e in data if e["type"] == "Photo")

    text = (
        f"📊 آمار کلی:\n"
        f"🔹 تعداد فایل‌ها: {count}\n"
        f"🧾 اسناد: {doc_count} | 🖼 عکس‌ها: {photo_count}\n"
        f"💾 حجم کل: {total_mb} مگابایت"
    )
    await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام!\nفایل بفرست تا ذخیره شود.\nیا کد یا بخشی از نام فایل را جستجو کن."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - شروع\n/help - راهنما\n/stats - آمار کلی\nارسال فایل یا جستجو با کد/نام"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("stats", command_stats))
app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_or_search))

print("🤖 Robot Is Runing  🤖 ...")
app.run_polling()
