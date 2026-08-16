import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
PROCEED, INVITED_BY, COUNTRY, PROFIT = range(4)

# CopyTrade bot username
VERIFICATION_BOT = "CopyEntries00bot"

WELCOME_TEXT = (
    "👋 *ONE STEP TO RICHES BRO!!*\n\n"
    "You're now at the entrance of a *professional insider community* "
    "where precision meets performance.\n\n"
    "🔹 Automated trade execution\n"
    "🔹 Strategic planning & risk management\n"
    "🔹 Real-time market insights\n"
    "🔹 Exclusive signals & community support\n\n"
    "We don't just trade — we build consistent results together.\n\n"
    "Ready to join the inner circle?"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton("✅ Proceed", callback_data="proceed")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return PROCEED

async def proceed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("👤 Existing Member", callback_data="invited_member")],
        [InlineKeyboardButton("💰 Paid to Join", callback_data="invited_paid")],
        [InlineKeyboardButton("🔗 Referral", callback_data="invited_referral")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "Who invited you to this community?",
        reply_markup=reply_markup
    )
    return INVITED_BY

async def invited_by(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["invited_by"] = query.data.replace("invited_", "")

    await query.edit_message_text(
        "🌍 Which country are you based in?\n\n"
        "Please type your country name below:"
    )
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    country_name = update.message.text.strip()
    context.user_data["country"] = country_name

    keyboard = [
        [InlineKeyboardButton("0 – $1,000", callback_data="profit_0_1000")],
        [InlineKeyboardButton("$1,000 – $10,000", callback_data="profit_1000_10000")],
        [InlineKeyboardButton("$10,000 – $100,000", callback_data="profit_10000_100000")],
        [InlineKeyboardButton("$100,000 and above", callback_data="profit_100000_plus")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Thanks! You're joining from *{country_name}*.\n\n"
        "What is the *highest profit* you've made from trading so far?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return PROFIT

async def profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["profit"] = query.data.replace("profit_", "")

    logger.info(
        f"New user | ID: {query.from_user.id} | "
        f"Username: @{query.from_user.username} | "
        f"Invited: {context.user_data.get('invited_by')} | "
        f"Country: {context.user_data.get('country')} | "
        f"Profit: {context.user_data.get('profit')}"
    )

    keyboard = [
        [InlineKeyboardButton(
            "✅ Verification to Join",
            url="https://inisider-screener.pages.dev"
        )],
        [InlineKeyboardButton(
            "📈 Use CopyTrade Bot",
            url=f"https://t.me/{VERIFICATION_BOT}"
        )],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "✅ *You're all set!*\n\n"
        "Kindly click the button below to verify.\n\n"
        "You can also start using the CopyTrade bot right away.\n\n"
        "Choose an option below 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Process cancelled. Type /start anytime to begin again.")
    return ConversationHandler.END

def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is missing!")

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PROCEED: [CallbackQueryHandler(proceed, pattern="^proceed$")],
            INVITED_BY: [CallbackQueryHandler(invited_by, pattern="^invited_")],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country)],
            PROFIT: [CallbackQueryHandler(profit, pattern="^profit_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()