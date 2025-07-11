
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler

PHOTO, RECEIVER, CENTER, PHONE = range(4)
TARGET_CHAT_ID = -1002152321701  # справжній ID групи

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
   await update.message.reply_text("Відправте фото відправлення")
   return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
   photo = update.message.photo[-1].file_id
   context.user_data['photo'] = photo
   await update.message.reply_text("Кому відправлення?")
   return RECEIVER

async def get_receiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
   context.user_data['receiver'] = update.message.text
   keyboard = [[KeyboardButton("РЦВ"), KeyboardButton("РЦЛ")], [KeyboardButton("РЦК")]]
   reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
   await update.message.reply_text("Куди відправлення? Оберіть одне або декілька. Коли закінчите, напишіть 'Готово'", reply_markup=reply_markup)
   context.user_data['centers'] = []
   return CENTER

async def get_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
   text = update.message.text
   if text.lower() == 'готово':
       request_contact_button = KeyboardButton("Надіслати номер", request_contact=True)
       reply_markup = ReplyKeyboardMarkup([[request_contact_button]], one_time_keyboard=True, resize_keyboard=True)
       await update.message.reply_text("Будь ласка, поділіться своїм номером телефону:", reply_markup=reply_markup)
       return PHONE
   elif text in ["РЦВ", "РЦЛ", "РЦК"]:
       if text not in context.user_data['centers']:
           context.user_data['centers'].append(text)
       await update.message.reply_text(f"Додано: {text}. Оберіть ще або напишіть 'Готово'")
   else:
       await update.message.reply_text("Будь ласка, оберіть РЦ або напишіть 'Готово'")
   return CENTER

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
   contact = update.message.contact
   context.user_data['phone'] = contact.phone_number

   centers = ", ".join(context.user_data['centers'])
   caption = (f"📦 Нова відправка\n"
              f"Кому: {context.user_data['receiver']}\n"
              f"Куди: {centers}\n"
              f"Відправник: {contact.first_name} ({context.user_data['phone']})")

   await context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=context.user_data['photo'], caption=caption)
   await update.message.reply_text("Дякую! Відправку збережено.", reply_markup=ReplyKeyboardRemove())
   return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
   await update.message.reply_text("Операцію скасовано.", reply_markup=ReplyKeyboardRemove())
   return ConversationHandler.END

if __name__ == '__main__':
   TOKEN = "7852735303:AAFydrs-NvtHZwMc9ztWKRyWZgP7HaBNsv4"
   app = ApplicationBuilder().token(TOKEN).build()

   conv_handler = ConversationHandler(
       entry_points=[CommandHandler('start', start)],
       states={
           PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
           RECEIVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_receiver)],
           CENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_center)],
           PHONE: [MessageHandler(filters.CONTACT, get_phone)]
       },
       fallbacks=[CommandHandler('cancel', cancel)]
   )

   app.add_handler(conv_handler)
   app.run_polling()
