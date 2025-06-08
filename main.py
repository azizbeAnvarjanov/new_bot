import logging
import gspread
from google.oauth2 import service_account
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram token
TOKEN = os.getenv('TELEGRAM_TOKEN')  # Get token from .env file

import json
credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Check if token is set
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in .env file")


# Google Sheets sozlamalari
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = credentials.with_scopes(scope)
client = gspread.authorize(creds)
sheet = client.open("Talabalar Qabuli").sheet1

# Logging sozlamasi
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Conversation bosqichlari
ISM, TELEFON, VILOYAT, YONALISH, FILIAL = range(5)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Ismingizni va familiyangizni kiriting:")
    return ISM

def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['fio'] = update.message.text

    contact_button = KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)

    update.message.reply_text("Quyidagi tugmani bosib telefon raqamingizni yuboring:", reply_markup=reply_markup)
    return TELEFON

def get_phone(update: Update, context: CallbackContext) -> int:
    if update.message.contact:
        context.user_data['phone'] = update.message.contact.phone_number
    else:
        update.message.reply_text("Iltimos, tugmani bosib telefon raqamingizni yuboring.")
        return TELEFON

    viloyatlar = [
        ["Toshkent shahar","Toshkent viloyati", "Andijon", "Namangan"],
        ["Fargʻona", "Buxoro", "Samarqand"],
        ["Qashqadaryo", "Surxondaryo", "Jizzax"],
        ["Navoiy", "Sirdaryo", "Xorazm"],
        ["Qoraqalpogʻiston"]
    ]
    reply_markup = ReplyKeyboardMarkup(viloyatlar, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Qaysi viloyatda yashaysiz?", reply_markup=reply_markup)
    return VILOYAT

def get_region(update: Update, context: CallbackContext) -> int:
    context.user_data['region'] = update.message.text

    keyboard = [['Davolash ishi'], ['Stomatologiya'], ['Pediatriya']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Topshirmoqchi bo'lgan yo'nalishingizni tanlang:", reply_markup=reply_markup)
    return YONALISH

def get_direction(update: Update, context: CallbackContext) -> int:
    context.user_data['direction'] = update.message.text

    filiallar = [['Chirchiq'], ['Namangan'], ['Andijon']]
    reply_markup = ReplyKeyboardMarkup(filiallar, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Qaysi filialda kirish imtihonlarini topshirmoqchisiz?", reply_markup=reply_markup)
    return FILIAL

def get_branch(update: Update, context: CallbackContext) -> int:
    context.user_data['branch'] = update.message.text

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Google Sheets-ga yozish
    sheet.append_row([
        context.user_data['fio'],
        context.user_data['phone'],
        context.user_data['region'],
        context.user_data['direction'],
        context.user_data['branch'],
        now
    ])

    # Yakuniy xabar
    update.message.reply_text(
        "Ma’lumotlaringiz muvaffaqiyatli qabul qilindi.\n"
        "Mutaxassisimiz tez orada siz bilan bog’lanadi."
    )

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Jarayon bekor qilindi.")
    return ConversationHandler.END

def main():
    try:
        updater = Updater(TOKEN)
    except Exception as e:
        logging.error(f"Failed to initialize bot: {str(e)}")
        raise

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ISM: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            TELEFON: [MessageHandler(Filters.contact, get_phone)],
            VILOYAT: [MessageHandler(Filters.text & ~Filters.command, get_region)],
            YONALISH: [MessageHandler(Filters.text & ~Filters.command, get_direction)],
            FILIAL: [MessageHandler(Filters.text & ~Filters.command, get_branch)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
