"""Telegram bot that provisions temporary email inboxes via the 1secmail API.

Usage:
    export TELEGRAM_BOT_TOKEN="<your_bot_token>"
    python bot.py

Commands:
    /start   -> Show help and current mailbox status
    /new     -> Generate a new temporary mailbox
    /address -> Display the current mailbox address
    /inbox   -> List message metadata for the mailbox
    /read ID -> Read a specific message by numeric ID from /inbox

Dependencies:
    python-telegram-bot>=20.0
    httpx
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TEMP_MAIL_API = "https://www.1secmail.com/api/v1/"
MAILBOX_KEY = "temp_mailbox"


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class TempMailError(RuntimeError):
    """Domain-specific exception for temp mail errors."""


@dataclass
class Mailbox:
    login: str
    domain: str

    @property
    def address(self) -> str:
        return f"{self.login}@{self.domain}"


@dataclass
class MessageMeta:
    message_id: int
    sender: str
    subject: str
    date: str


async def generate_mailbox() -> Mailbox:
    """Request a new random mailbox from the 1secmail API."""

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                TEMP_MAIL_API,
                params={"action": "genRandomMailbox", "count": 1},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:  # covers RequestError & HTTPStatusError
            raise TempMailError(f"Failed to generate mailbox: {exc}") from exc

    data = response.json()
    if not isinstance(data, list) or not data:
        raise TempMailError("API returned an unexpected response while creating mailbox")

    email = data[0]
    if not isinstance(email, str) or "@" not in email:
        raise TempMailError("Generated mailbox address is invalid")

    login, domain = email.split("@", maxsplit=1)
    return Mailbox(login=login, domain=domain)


async def fetch_messages(mailbox: Mailbox) -> List[MessageMeta]:
    """Retrieve metadata for all messages in the mailbox."""

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                TEMP_MAIL_API,
                params={
                    "action": "getMessages",
                    "login": mailbox.login,
                    "domain": mailbox.domain,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TempMailError(f"Failed to fetch messages: {exc}") from exc

    payload = response.json()
    if not isinstance(payload, list):
        raise TempMailError("Unexpected response while listing messages")

    messages: List[MessageMeta] = []
    for item in payload:
        try:
            message_id = int(item.get("id"))
            sender = str(item.get("from", ""))
            subject = str(item.get("subject", ""))
            date = str(item.get("date", ""))
        except (TypeError, ValueError) as exc:
            logger.warning("Skipping malformed message metadata: %s", exc)
            continue

        messages.append(
            MessageMeta(
                message_id=message_id,
                sender=sender or "(unknown sender)",
                subject=subject or "(no subject)",
                date=date or "(no date)",
            )
        )

    return messages


async def read_message(mailbox: Mailbox, message_id: int) -> Dict[str, str]:
    """Fetch a message body by ID."""

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                TEMP_MAIL_API,
                params={
                    "action": "readMessage",
                    "login": mailbox.login,
                    "domain": mailbox.domain,
                    "id": message_id,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TempMailError(f"Failed to read message {message_id}: {exc}") from exc

    body = response.json()
    if not isinstance(body, dict) or not body:
        raise TempMailError("Unexpected response while reading message")

    return {
        "from": str(body.get("from", "(unknown sender)")),
        "subject": str(body.get("subject", "(no subject)")),
        "date": str(body.get("date", "(no date)")),
        "text": str(body.get("textBody", "")) or str(body.get("htmlBody", "")),
    }


def get_mailbox(context: ContextTypes.DEFAULT_TYPE) -> Optional[Mailbox]:
    mailbox = context.user_data.get(MAILBOX_KEY)
    if isinstance(mailbox, Mailbox):
        return mailbox
    return None


def set_mailbox(context: ContextTypes.DEFAULT_TYPE, mailbox: Mailbox) -> None:
    context.user_data[MAILBOX_KEY] = mailbox


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mailbox = get_mailbox(context)
    current_address = mailbox.address if mailbox else "None yet"

    message = (
        "👋 Welcome to the Temp Mail bot!\n\n"
        "Use /new to generate a fresh temporary mailbox.\n"
        "Once you have an address you can:\n"
        "• /address – see your current mailbox\n"
        "• /inbox – list incoming messages\n"
        "• /read <id> – open a specific message\n\n"
        f"Current mailbox: {current_address}"
    )

    if update.message:
        await update.message.reply_text(message)


async def handle_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        mailbox = await generate_mailbox()
    except TempMailError as exc:
        logger.exception("Could not generate mailbox")
        if update.message:
            await update.message.reply_text(f"⚠️ Error: {exc}")
        return

    set_mailbox(context, mailbox)
    if update.message:
        await update.message.reply_text(
            f"📬 Your new temporary mailbox is: {mailbox.address}\n"
            "Keep this bot open to check incoming messages with /inbox."
        )


async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mailbox = get_mailbox(context)
    if update.message:
        if mailbox:
            await update.message.reply_text(f"Your current mailbox: {mailbox.address}")
        else:
            await update.message.reply_text("You don't have a mailbox yet. Use /new to create one.")


async def handle_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mailbox = get_mailbox(context)
    if not mailbox:
        if update.message:
            await update.message.reply_text("You don't have a mailbox yet. Use /new to create one.")
        return

    try:
        messages = await fetch_messages(mailbox)
    except TempMailError as exc:
        logger.exception("Could not fetch inbox")
        if update.message:
            await update.message.reply_text(f"⚠️ Error: {exc}")
        return

    if not messages:
        if update.message:
            await update.message.reply_text(
                f"No messages for {mailbox.address} yet. Try again in a moment."
            )
        return

    lines = [f"Inbox for {mailbox.address}:"]
    for msg in messages:
        lines.append(
            f"• ID {msg.message_id} | From: {msg.sender} | Subject: {msg.subject} | Date: {msg.date}"
        )

    if update.message:
        await update.message.reply_text("\n".join(lines))


async def handle_read(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mailbox = get_mailbox(context)
    if not mailbox:
        if update.message:
            await update.message.reply_text("You don't have a mailbox yet. Use /new to create one.")
        return

    if not context.args:
        if update.message:
            await update.message.reply_text("Usage: /read <message_id>")
        return

    try:
        message_id = int(context.args[0])
    except ValueError:
        if update.message:
            await update.message.reply_text("Message ID must be a number. Example: /read 123456789")
        return

    try:
        message = await read_message(mailbox, message_id)
    except TempMailError as exc:
        logger.exception("Could not read message")
        if update.message:
            await update.message.reply_text(f"⚠️ Error: {exc}")
        return

    text_body = message.get("text", "(No body)")
    if len(text_body) > 3500:
        text_body = text_body[:3500] + "\n\n… (truncated)"

    if update.message:
        await update.message.reply_text(
            "\n".join(
                [
                    f"From: {message['from']}",
                    f"Subject: {message['subject']}",
                    f"Date: {message['date']}",
                    "",
                    text_body,
                ]
            )
        )


def build_application(token: str):
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("new", handle_new))
    application.add_handler(CommandHandler("address", handle_address))
    application.add_handler(CommandHandler("inbox", handle_inbox))
    application.add_handler(CommandHandler("read", handle_read))

    return application


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

    application = build_application(token)
    logger.info("Starting Telegram bot")
    application.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()

