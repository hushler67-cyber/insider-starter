import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
PROCEED, INVITED_BY, COUNTRY, PROFIT = range(4)

# ───────────────────────────────────────────────
# REPLACE THIS with the verification bot username (without @)
VERIFICATION_BOT = "YourVerificationBot"   # e.g. "SpamVerifyBot"
# ───────────────────────────────────────────────

WELCOME_TEXT = (
    "👋 *Welcome to Elite AutoTrade Hub*\n\n"
    "You're now at the entrance of a *professional trading community* "
    "where precision meets performance.\n\n"
    "🔹 Automated trade execution\n"
    "🔹 Strategic planning & risk management\n"
    "🔹 Real-time market insights\n"
    "🔹 Exclusive signals & community support\n\n"
    "We don't just trade — we build consistent results together.\n\n"
    "Ready to join the inner circle?"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send professional welcome message with Proceed button."""
    keyboard = [[InlineKeyboardButton("✅ Proceed", callback_data="proceed")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return PROCEED

async def proceed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask how the user was invited."""
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
    """Save invitation method and ask for country."""
    query = update.callback_query
    await query.answer()

    # Store the answer
    context.user_data["invited_by"] = query.data.replace("invited_", "")

    await query.edit_message_text(
        "🌍 Which country are you based in?\n\n"
        "Please type your country name below:"
    )
    return COUNTRY

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save country and ask for highest profit range."""
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
    """Final step — show Join Trade button that links to verification bot."""
    query = update.callback_query
    await query.answer()

    context.user_data["profit"] = query.data.replace("profit_", "")

    # Optional: log the collected data
    logger.info(
        f"New user | ID: {query.from_user.id} | "
        f"Invited: {context.user_data.get('invited_by')} | "
        f"Country: {context.user_data.get('country')} | "
        f"Profit: {context.user_data.get('profit')}"
    )

    keyboard = [
        [InlineKeyboardButton(
            "🚀 Join Trade Now",
            url=f"https://t.me/{VERIFICATION_BOT}"
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "✅ *You're all set!*\n\n"
        "One final step: complete a quick spam verification to unlock full access "
        "to the trading group and autotrade features.\n\n"
        "Click the button below to continue 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Allow user to cancel the conversation."""
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
            COUNTRY: [CallbackQueryHandler(profit)],  # temporary fallback, real handler below
            PROFIT: [CallbackQueryHandler(profit, pattern="^profit_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    # Fix: country is a text message, not callback
    conv_handler.states[COUNTRY] = [
        # MessageHandler is needed for free text
    ]

    # Better way — rebuild cleanly
    from telegram.ext import MessageHandler, filters

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
    application.add_handler(CommandHandler("cancel", cancel))

    # Start the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()