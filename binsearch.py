import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

TOKEN = '7667316037:AAGgQd6dyWZIUfvoxFO8JkVNvlYJUiMTQBM'

CSV_FILE_PATH = 'bin.csv'  # Replace with the path to your CSV file

# Define conversation states
BANK_NAME, CARD_TYPE, CARD_BRAND = range(3)

# Global variable to store the CSV data
bank_data = []

def load_csv_data():
    global bank_data
    with open(CSV_FILE_PATH, 'r') as csvfile:
        reader = csv.reader(csvfile)
        bank_data = list(reader)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Welcome! Please enter the name of the bank you want information about.')
    return BANK_NAME

async def bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['bank_name'] = update.message.text.lower()
    keyboard = [
        [InlineKeyboardButton("Debit", callback_data='debit'),
         InlineKeyboardButton("Credit", callback_data='credit'),
         InlineKeyboardButton("Prepaid", callback_data='prepaid')],
        [InlineKeyboardButton("All Types", callback_data='all_types')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please select the card type:', reply_markup=reply_markup)
    return CARD_TYPE

async def card_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['card_type'] = query.data
    keyboard = [
        [InlineKeyboardButton("Visa", callback_data='visa'),
         InlineKeyboardButton("Mastercard", callback_data='mastercard')],
        [InlineKeyboardButton("All Brands", callback_data='all_brands')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Please select the card brand:', reply_markup=reply_markup)
    return CARD_BRAND

async def card_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['card_brand'] = query.data
    await query.edit_message_text('Thank you for your selections. Searching for matching cards...')
    await send_results(update, context)
    return ConversationHandler.END

async def send_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bank_name = context.user_data['bank_name']
    card_type = context.user_data['card_type']
    card_brand = context.user_data['card_brand']

    matching_cards = [
        card for card in bank_data 
        if bank_name in card[4].lower() and
        (card_type == 'all_types' or card_type.upper() in card[2].upper()) and
        (card_brand == 'all_brands' or card_brand.upper() in card[1].upper())
    ]

    if not matching_cards:
        await update.callback_query.message.reply_text(f'No cards found matching your criteria.')
        return

    for card in matching_cards:
        response = f"""[⌥] 𝐁𝐈𝐍 𝐥𝐨𝐨𝐤𝐮𝐩 𝐀𝐩𝐢
━━━━━━━━━━━━━━━━━
[⌬] 𝐁𝐈𝐍 ⇢ {card[0]}
[⌬] 𝐈𝐧𝐟𝐨 ⇢ {card[1]}-{card[2]}-{card[3]}
[⌬] 𝐈𝐬𝐬𝐮𝐞𝐫 ⇢ {card[4]}
[⌬] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇢ {card[9]}
━━━━━━━━━━━━━━━━━"""
        await update.callback_query.message.reply_text(response)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Operation cancelled. Type /start to begin a new search.')
    return ConversationHandler.END

def main() -> None:
    load_csv_data()
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BANK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bank_name)],
            CARD_TYPE: [CallbackQueryHandler(card_type)],
            CARD_BRAND: [CallbackQueryHandler(card_brand)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
