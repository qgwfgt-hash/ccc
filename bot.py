"""Telegram bot that provisions temporary inboxes via tempmail.plus."""

from __future__ import annotations

import logging
import os
import random
import re
from dataclasses import dataclass
from html import unescape
from typing import Dict, Optional
from urllib.parse import quote_plus

import requests
from requests import RequestException
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

API_BASE_URL = "https://tempmail.plus/api"
HTTP_TIMEOUT = 10
DEFAULT_DOMAIN = "mailto.plus"
AVAILABLE_DOMAINS = [
    "tempmail.plus",
    "mailto.plus",
    "fexpost.com",
    "fexbox.org",
    "fexbox.ru",
    "mailbox.in.ua",
    "rover.info",
    "chitthi.in",
    "fextemp.com",
    "any.pink",
    "merepost.com",
]
LOCAL_PART_PATTERN = re.compile(r"^[A-Za-z0-9]+([._-][A-Za-z0-9]+)*$")
BR_RE = re.compile(r"(?i)<br\s*/?>")
TAG_RE = re.compile(r"<[^>]+?>")
SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")


@dataclass
class Mailbox:
    email: str
    local_part: str
    domain: str


user_mailboxes: Dict[int, Mailbox] = {}


def _api_get(path: str, params: Dict[str, str | int]) -> Optional[dict]:
    """Call the tempmail.plus API and return JSON, handling network errors."""

    try:
        response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except RequestException as exc:  # pragma: no cover - network error path
        logger.error("API request failed: %s", exc)
        return None


def _generate_local_part() -> str:
    vowels = "aeouy"
    consonants = "bcdfghkmnpqstvwxz"
    length = random.randint(5, 7)
    use_vowel = bool(random.getrandbits(1))
    swing = 5 if use_vowel else 7
    letters: list[str] = []

    for _ in range(length):
        source = vowels if use_vowel else consonants
        letters.append(random.choice(source))

        if random.randint(0, swing) > 1:
            use_vowel = not use_vowel
            swing = 5 if use_vowel else 10
        else:
            swing += 4

    return "".join(letters)


def _normalize_domain(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None

    domain = raw.strip().lower()
    if domain.startswith("@"):
        domain = domain[1:]

    return domain if domain in AVAILABLE_DOMAINS else None


def _parse_new_mailbox_args(args: list[str]) -> tuple[Optional[str], str, Optional[str]]:
    if not args:
        return None, DEFAULT_DOMAIN, None

    text = " ".join(args).strip()
    local_candidate: Optional[str] = None
    domain_candidate: Optional[str] = None

    if "@" in text:
        before, after = text.split("@", 1)
        local_candidate = before.strip() or None
        domain_candidate = after.strip() or None
    else:
        if len(args) == 1:
            single = args[0].strip()
            normalized_domain = _normalize_domain(single)
            if normalized_domain:
                domain_candidate = normalized_domain
            else:
                local_candidate = single or None
        else:
            local_candidate = args[0].strip() or None
            domain_candidate = args[1].strip() if len(args) > 1 else None

    domain = _normalize_domain(domain_candidate)
    if domain_candidate and not domain:
        error = (
            f"❌ Unsupported domain '{domain_candidate}'. Use /domains to see the list of allowed domains."
        )
        return None, DEFAULT_DOMAIN, error

    if domain is None:
        domain = DEFAULT_DOMAIN

    if local_candidate:
        local_candidate = local_candidate.strip()
        if len(local_candidate) > 200:
            return None, domain, "❌ Mailbox name must be 200 characters or fewer."
        if not LOCAL_PART_PATTERN.fullmatch(local_candidate):
            return (
                None,
                domain,
                "❌ Mailbox name can only contain letters, digits, and the separators .-_ (no spaces).",
            )
    else:
        local_candidate = None

    return local_candidate, domain, None


def _get_mailbox(update: Update) -> Optional[Mailbox]:
    user = update.effective_user
    if not user:
        return None
    return user_mailboxes.get(user.id)


def _html_to_text(html_content: str) -> str:
    text = BR_RE.sub("\n", html_content)
    text = TAG_RE.sub("", text)
    return unescape(text)


def _format_size(size: int) -> str:
    value = float(size)
    unit_index = 0

    while value >= 1024 and unit_index < len(SIZE_UNITS) - 1:
        value /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(value)} {SIZE_UNITS[unit_index]}"
    return f"{value:.1f} {SIZE_UNITS[unit_index]}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    user = update.effective_user
    greeting = f"Hey {user.first_name}!" if user and user.first_name else "Hey there!"
    reply_text = (
        f"{greeting}\n\n"
        "I can generate disposable mailboxes for you via https://tempmail.plus.\n\n"
        "Commands:\n"
        "• /new — create a mailbox (use `/new name domain` to customize)\n"
        "• /address — show your active mailbox\n"
        "• /inbox — list the latest messages\n"
        "• /read <id> — open a message by its ID\n"
        "• /domains — list available domains\n"
        "• /help — show this menu again"
    )

    await message.reply_text(reply_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def new_mailbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return

    local_part, domain, error = _parse_new_mailbox_args(context.args)
    if error:
        await message.reply_text(error)
        return

    if local_part is None:
        local_part = _generate_local_part()

    email = f"{local_part}@{domain}"
    user_mailboxes[user.id] = Mailbox(email=email, local_part=local_part, domain=domain)

    await message.reply_text(
        "✅ Mailbox ready!\n"
        f"Address: <code>{email}</code>\n"
        "Use /inbox to check for incoming messages.",
        parse_mode=ParseMode.HTML,
    )


async def show_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    mailbox = _get_mailbox(update)
    if not mailbox:
        await message.reply_text("ℹ️ You don't have a mailbox yet. Use /new to create one.")
        return

    await message.reply_text(
        f"📮 Your current mailbox is <code>{mailbox.email}</code>.",
        parse_mode=ParseMode.HTML,
    )


async def list_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    mailbox = _get_mailbox(update)
    if not mailbox:
        await message.reply_text("ℹ️ You don't have a mailbox yet. Use /new to create one.")
        return

    data = _api_get("/mails", {"email": mailbox.email, "limit": 10})

    if data is None:
        await message.reply_text("⚠️ Couldn't reach tempmail.plus right now. Please try again soon.")
        return

    if not data.get("result", False):
        err = data.get("err") or {}
        err_msg = err.get("msg") or "Temp mail service returned an error."
        await message.reply_text(f"⚠️ {err_msg}")
        return

    mail_items = data.get("mail_list") or []
    if not mail_items:
        await message.reply_text("📭 Inbox is empty for now. We'll watch for new messages.")
        return

    lines = ["✉️ Latest messages (newest first):"]
    for item in mail_items[:10]:
        mail_id = item.get("mail_id")
        sender = item.get("from_name") or item.get("from_mail") or "Unknown sender"
        subject = item.get("subject") or "(No subject)"
        timestamp = item.get("time")
        prefix = "🆕 " if item.get("is_new") else ""
        if timestamp:
            lines.append(f"{prefix}ID {mail_id}: {subject} (from {sender}, {timestamp})")
        else:
            lines.append(f"{prefix}ID {mail_id}: {subject} (from {sender})")

    lines.append("Use /read <id> to open a message.")
    await message.reply_text("\n".join(lines))


async def read_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    mailbox = _get_mailbox(update)
    if not mailbox:
        await message.reply_text("ℹ️ You don't have a mailbox yet. Use /new to create one.")
        return

    if not context.args:
        await message.reply_text("Usage: /read <id>. Use /inbox to see available IDs.")
        return

    message_id = context.args[0]
    data = _api_get(f"/mails/{message_id}", {"email": mailbox.email})

    if data is None:
        await message.reply_text("⚠️ Couldn't reach tempmail.plus right now. Please try again later.")
        return

    if not data.get("result", False):
        err = data.get("err") or {}
        err_msg = err.get("msg") or "Unable to fetch that message."
        await message.reply_text(f"⚠️ {err_msg}")
        return

    subject = data.get("subject") or "(No subject)"
    sender = data.get("from") or data.get("from_mail") or "Unknown sender"
    date = data.get("date") or data.get("time") or "Unknown date"

    body = data.get("text") or data.get("text_body") or ""
    if not body:
        html_body = data.get("html") or ""
        if html_body:
            body = _html_to_text(html_body)

    body = body.strip() or "(Empty message)"
    if len(body) > 3500:
        body = body[:3497] + "..."

    attachments = data.get("attachments") or []
    attachment_lines: list[str] = []
    if attachments:
        attachment_lines.append("Attachments:")
        for attachment in attachments:
            name = attachment.get("name") or f"attachment-{attachment.get('attachment_id')}"
            size_raw = attachment.get("size")
            size_label = ""
            if isinstance(size_raw, int):
                size_label = _format_size(size_raw)
            elif isinstance(size_raw, str) and size_raw.isdigit():
                size_label = _format_size(int(size_raw))

            attachment_id = attachment.get("attachment_id")
            if attachment_id is not None:
                url = (
                    f"{API_BASE_URL}/mails/{message_id}/attachments/{attachment_id}?email={quote_plus(mailbox.email)}"
                )
                attachment_lines.append(f"• {name} ({size_label}) → {url}".rstrip())
            else:
                info = f"• {name} ({size_label})".rstrip()
                attachment_lines.append(info)

    response_lines = [
        f"Subject: {subject}",
        f"From: {sender}",
        f"Date: {date}",
        "",
        body,
    ]

    if attachment_lines:
        response_lines.append("")
        response_lines.extend(attachment_lines)

    await message.reply_text("\n".join(response_lines))


async def list_domains(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message:
        return

    lines = ["🌐 Available domains:"]
    for domain in AVAILABLE_DOMAINS:
        label = f"• {domain}"
        if domain == DEFAULT_DOMAIN:
            label += " (default)"
        lines.append(label)

    lines.append("Use /new <name> <domain> to claim one, e.g. /new hero any.pink")
    await message.reply_text("\n".join(lines))


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message:
        await message.reply_text("I don't know that command. Try /help for options.")


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
    application.add_handler(CommandHandler("domains", list_domains))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Bot is starting...")
    application.run_polling(close_loop=False)


if __name__ == "__main__":  # pragma: no cover - manual execution guard
    main()

