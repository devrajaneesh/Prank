"""Telegram prank bot using a Render-compatible HTTPS webhook.

The bot stores conversation data only in python-telegram-bot's in-memory
user_data. Render supplies the public HTTPS URL through RENDER_EXTERNAL_URL.
"""

import asyncio
import hashlib
import logging
import os
import threading
from typing import Any

from flask import Flask, jsonify, request
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

WEBHOOK_PATH = "/telegram-webhook"
BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not set. Add it as a private environment variable on Render."
    )

# A stable secret derived from the private token. It is never sent to the client.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or hashlib.sha256(
    BOT_TOKEN.encode("utf-8")
).hexdigest()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_loop: asyncio.AbstractEventLoop | None = None
telegram_ready = threading.Event()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reset the user's in-memory data and show the welcome screen."""
    context.user_data.clear()
    if update.message:
        await update.message.reply_text(START_TEXT, reply_markup=START_BUTTON)
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
    """Cancel the current conversation and clear in-memory data."""
    context.user_data.clear()
    if update.message:
        await update.message.reply_text(
            "❌ Prediction cancelled. Send /start whenever you want to try again."
        )
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors without exposing the bot token or user data."""
    logger.error("Unhandled exception while processing an update", exc_info=context.error)


def build_handlers() -> ConversationHandler:
    """Build the conversation handler shared by webhook processing."""
    return ConversationHandler(
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


application.add_handler(build_handlers())
application.add_handler(CommandHandler("cancel", cancel))
application.add_error_handler(error_handler)


def run_telegram_worker() -> None:
    """Run python-telegram-bot's async application in a background thread."""
    global telegram_loop

    telegram_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(telegram_loop)

    async def initialize() -> None:
        await application.initialize()
        await application.start()

        if not PUBLIC_URL:
            logger.warning(
                "RENDER_EXTERNAL_URL is missing; webhook registration was skipped."
            )
            telegram_ready.set()
            return

        webhook_url = f"{PUBLIC_URL}{WEBHOOK_PATH}"
        await application.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        logger.info("Telegram webhook registered at %s", webhook_url)
        telegram_ready.set()

    try:
        telegram_loop.run_until_complete(initialize())
        telegram_loop.run_forever()
    except Exception:
        logger.exception("Telegram webhook worker stopped unexpectedly")
    finally:
        telegram_ready.clear()


threading.Thread(
    target=run_telegram_worker,
    name="telegram-webhook-worker",
    daemon=True,
).start()


@app.get("/")
def index() -> tuple[str, int]:
    """Simple status page for Render and manual checks."""
    return "Telegram prank bot is running.", 200


@app.get("/health")
def health() -> tuple[Any, int]:
    """Health endpoint used by Render."""
    return jsonify({"ok": True, "telegram_ready": telegram_ready.is_set()}), 200


@app.post(WEBHOOK_PATH)
def telegram_webhook() -> tuple[Any, int]:
    """Receive Telegram updates and schedule them on the bot event loop."""
    supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if supplied_secret != WEBHOOK_SECRET:
        return jsonify({"ok": False, "error": "forbidden"}), 403

    if telegram_loop is None or not telegram_ready.is_set():
        return jsonify({"ok": False, "error": "bot starting"}), 503

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "invalid JSON"}), 400

    try:
        update = Update.de_json(payload, application.bot)
        asyncio.run_coroutine_threadsafe(application.process_update(update), telegram_loop)
    except Exception:
        logger.exception("Could not queue Telegram update")
        return jsonify({"ok": False, "error": "update rejected"}), 500

    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    # Useful for local HTTP testing. For Render, Gunicorn imports `app` instead.
    app.run(host="0.0.0.0", port=PORT, threaded=True)
