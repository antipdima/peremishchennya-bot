from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
import nest_asyncio
import asyncio

PHOTO, RECEIVER, CENTER, PHONE = range(4)
TARGET_CHAT_ID = -1002152321701  # ID цільового чату

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Відправте фото відправлення:")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    photo = update.message.photo[-1].file_id
    context.user_data['photo'] = photo
    await update.message.reply_text("👤 Кому відправлення? (Прізвище та ініціали)")
    return RECEIVER

async def get_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['receiver'] = update.message.text
    context.user_data['centers'] = []
    keyboard = [[KeyboardButton("РЦК")], [KeyboardButton("РЦЛ")], [KeyboardButton("РЦВ")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🏢 Куди відправлення? Оберіть один або кілька РЦ. Коли завершите — напишіть 'Готово'.",
        reply_markup=reply_markup
    )
    return CENTER

async def get_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    valid_centers = {"РЦК", "РЦЛ", "РЦВ"}

    if text == "ГОТОВО":
        if not context.user_data.get("centers"):
            await update.message.reply_text("⚠️ Ви ще не вибрали жодного РЦ.")
            return CENTER
        request_contact_button = KeyboardButton("📞 Надіслати номер", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[request_contact_button]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("📱 Поділіться номером телефону:", reply_markup=reply_markup)
        return PHONE

    elif text in valid_centers:
        if text not in context.user_data['centers']:
            context.user_data['centers'].append(text)
    else:
        await update.message.reply_text("⚠️ Будь ласка, виберіть РЦ зі списку або напишіть 'Готово'")

    return CENTER

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data['phone'] = phone

    caption = (
        f"📦 *Відправлення*\n"
        f"👤 Отримувач: {context.user_data['receiver']}\n"
        f"🏢 РЦ: {', '.join(context.user_data['centers'])}\n"
        f"📞 Номер телефону: {context.user_data['phone']}"
    )

    await context.bot.send_photo(
        chat_id=TARGET_CHAT_ID,
        photo=context.user_data['photo'],
        caption=caption,
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Дякуємо! Ваше відправлення збережено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Операцію скасовано.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def main():
    application = ApplicationBuilder().token("7852735303:AAFydrs-NvtHZwMc9ztWKRyWZgP7HaBNsv4").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            RECEIVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_receiver)],
            CENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_center)],
            PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    await application.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())

