"""A simple Telegram prank bot using python-telegram-bot.

The bot keeps the current user's name and partner's name only in memory.
No database or external astrology/numerology service is used.
"""

import asyncio
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Conversation states.
INTRO, ASK_NAME, ASK_PARTNER, SHOWING_PREDICTION = range(4)

START_TEXT = (
    "🔮 Know Your & Your Partner's Future\n"
    "According to Numerology & Astrology"
)

START_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Start Prediction", callback_data="start_prediction")]]
)

TRY_AGAIN_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🔄 Try Again", callback_data="try_again")]]
)

LOADING_MESSAGES = (
    "🔮 Analyzing astrology...",
    "🔢 Calculating numerology...",
    "🌌 Checking planetary alignment...",
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reset the user's in-memory data and show the welcome screen."""
    context.user_data.clear()

    if update.message:
        await update.message.reply_text(START_TEXT, reply_markup=START_BUTTON)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(
            START_TEXT, reply_markup=START_BUTTON
        )

    return INTRO


async def begin_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for the user's name after the Start Prediction button is pressed."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text("👤 Enter your name:")
    return ASK_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the user's name and ask for the partner's name."""
    name = update.message.text.strip()
    context.user_data["name"] = name
    await update.message.reply_text("❤️ Enter your partner's name:")
    return ASK_PARTNER


async def receive_partner_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Save the partner's name, show fake loading messages, and reveal the prank."""
    partner_name = update.message.text.strip()
    context.user_data["partner_name"] = partner_name

    for loading_message in LOADING_MESSAGES:
        await update.message.reply_text(loading_message)
        await asyncio.sleep(1)

    prediction = (
        "🚨 PREDICTION COMPLETE 🚨\n\n"
        f"❤️ Partner: \"{partner_name}\"\n\n"
        "🔮 Prediction:\n"
        f'Tumhari wife "{partner_name}" Rajaneesh ke saath bhaag jayegi 😂😂\n\n'
        "⚠️ Just for fun — this is a prank, not a real prediction."
    )

    await update.message.reply_text(prediction, reply_markup=TRY_AGAIN_BUTTON)
    return SHOWING_PREDICTION


async def try_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restart the process from the welcome screen."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text(START_TEXT, reply_markup=START_BUTTON)
    return INTRO


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation and clear the user's in-memory data."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Prediction cancelled. Send /start whenever you want to try again."
    )
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log unexpected errors without exposing the bot token or user data."""
    logger.error("Unhandled exception while processing an update", exc_info=context.error)


def build_application():
    """Build and configure the Telegram application."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Create a bot token with @BotFather and set it "
            "as an environment variable before running the bot."
        )

    application = ApplicationBuilder().token(token).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INTRO: [
                CallbackQueryHandler(
                    begin_prediction, pattern=r"^start_prediction$"
                )
            ],
            ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
            ],
            ASK_PARTNER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, receive_partner_name
                )
            ],
            SHOWING_PREDICTION: [
                CallbackQueryHandler(try_again, pattern=r"^try_again$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conversation)
    # Also handle /cancel when no conversation is currently active.
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    """Start the bot using Telegram long polling."""
    application = build_application()
    logger.info("Starting Telegram prank bot")
    application.run_polling()


if __name__ == "__main__":
    main()
