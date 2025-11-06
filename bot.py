"""Telegram bot that provisions temporary inboxes via 1secmail.com."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

import requests
from requests import RequestException
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

API_BASE_URL = "https://www.1secmail.com/api/v1/"
HTTP_TIMEOUT = 10


@dataclass
class Mailbox:
    email: str
    login: str
    domain: str


user_mailboxes: Dict[int, Mailbox] = {}


def _api_get(params: Dict[str, str]) -> Optional[dict | list]:
    """Call the 1secmail API and return JSON, handling network errors."""

    try:
        response = requests.get(API_BASE_URL, params=params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except RequestException as exc:  # pragma: no cover - network error path
        logger.error("API request failed: %s", exc)
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    greeting = f"Hey {user.first_name}!" if user and user.first_name else "Hey there!"
    message = (
        f"{greeting}\n\n"
        "I can generate disposable email addresses for you using 1secmail.\n\n"
        "Available commands:\n"
        "• /new — create a fresh temporary email address\n"
        "• /address — show your current temporary email\n"
        "• /inbox — list recent emails in your mailbox\n"
        "• /read <id> — read a specific email from the list\n"
        "• /help — show this message again"
    )
    await update.message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def new_mailbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    data = _api_get({"action": "genRandomMailbox", "count": 1})
    if not data:
        await update.message.reply_text("⚠️ Unable to reach temp mail service. Please try again later.")
        return

    email = data[0]
    login, domain = email.split("@", maxsplit=1)
    user_mailboxes[user_id] = Mailbox(email=email, login=login, domain=domain)

    await update.message.reply_text(
        "✅ New temporary mailbox ready!\n"
        f"Address: <code>{email}</code>\n"
        "Use /inbox to check for messages.",
        parse_mode=ParseMode.HTML,
    )


def _get_mailbox(update: Update) -> Optional[Mailbox]:
    user_id = update.effective_user.id
    mailbox = user_mailboxes.get(user_id)
    return mailbox


async def show_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mailbox = _get_mailbox(update)
    if not mailbox:
        await update.message.reply_text("ℹ️ You don't have a mailbox yet. Use /new to create one.")
        return

    await update.message.reply_text(
        f"📮 Your current mailbox is <code>{mailbox.email}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def list_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mailbox = _get_mailbox(update)
    if not mailbox:
        await update.message.reply_text("ℹ️ You don't have a mailbox yet. Use /new to create one.")
        return

    data = _api_get(
        {"action": "getMessages", "login": mailbox.login, "domain": mailbox.domain}
    )

    if data is None:
        await update.message.reply_text("⚠️ Couldn't fetch inbox right now. Please try again soon.")
        return

    if not data:
        await update.message.reply_text("📭 Inbox is empty. We'll keep it warm for you!")
        return

    lines = ["✉️ Latest messages:"]
    for message in data:
        lines.append(
            f"• ID {message['id']}: from {message['from']} — {message['subject'] or 'No subject'}"
        )

    await update.message.reply_text("\n".join(lines))


async def read_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mailbox = _get_mailbox(update)
    if not mailbox:
        await update.message.reply_text("ℹ️ You don't have a mailbox yet. Use /new to create one.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /read <id>. Use /inbox to see available IDs.")
        return

    message_id = context.args[0]
    data = _api_get(
        {
            "action": "readMessage",
            "login": mailbox.login,
            "domain": mailbox.domain,
            "id": message_id,
        }
    )

    if data is None:
        await update.message.reply_text("⚠️ Couldn't reach temp mail service. Please try again later.")
        return

    if "error" in data:
        await update.message.reply_text(f"⚠️ {data['error']}")
        return

    subject = data.get("subject") or "(No subject)"
    sender = data.get("from") or "Unknown"
    date = data.get("date") or "Unknown"
    body = data.get("textBody") or data.get("body") or "(Empty message)"

    excerpt = body.strip()
    if len(excerpt) > 3500:
        excerpt = excerpt[:3497] + "..."

    await update.message.reply_text(
        f"Subject: {subject}\nFrom: {sender}\nDate: {date}\n\n{excerpt}",
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("I don't know that command. Try /help for options.")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set the TELEGRAM_BOT_TOKEN environment variable before running the bot.")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new", new_mailbox))
    application.add_handler(CommandHandler("address", show_address))
    application.add_handler(CommandHandler("inbox", list_inbox))
    application.add_handler(CommandHandler("read", read_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Bot is starting...")
    application.run_polling(close_loop=False)


if __name__ == "__main__":  # pragma: no cover - manual execution guard
    main()

