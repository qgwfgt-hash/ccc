"""Telegram bot that provisions temporary email inboxes via TempMail Plus.

Usage::

    export TELEGRAM_BOT_TOKEN="<your_bot_token>"
    python bot.py

Commands::

    /start                 -> Show help and current mailbox status
    /domains               -> List available temp mail domains
    /new [name] [domain]   -> Generate mailbox (auto-random if omitted)
    /address               -> Display the current mailbox address
    /inbox                 -> List message metadata for the mailbox
    /read <id>             -> Read a specific message by numeric ID from /inbox

Dependencies:
    python-telegram-bot>=20.0
    httpx
"""

from __future__ import annotations

import html
import logging
import os
import re
import secrets
import string
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


API_BASE = "https://tempmail.plus/api"
REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) TempMailBot/1.0",
}
DEFAULT_LANG = "en"
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
    local_part: str
    domain: str

    @property
    def address(self) -> str:
        return f"{self.local_part}@{self.domain}"

    def query_params(self) -> Dict[str, str]:
        return {
            "email": self.local_part,
            "domain": self.domain,
            "lang": DEFAULT_LANG,
        }


@dataclass
class MessageMeta:
    message_id: int
    sender: str
    subject: str
    date: str


_DOMAIN_CACHE: Optional[List[str]] = None
_LOCAL_PART_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,30}$")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _sanitize_local_part(value: str) -> str:
    clean = value.strip().lower()
    if clean.startswith("@"):  # allow people to send just @name
        clean = clean[1:]
    if not clean:
        raise TempMailError("Mailbox name can not be empty.")
    if not _LOCAL_PART_PATTERN.fullmatch(clean):
        raise TempMailError(
            "Mailbox name may only contain letters, numbers, dots, underscores or dashes (max 30)."
        )
    return clean


def _sanitize_domain(value: str) -> str:
    clean = value.strip().lower()
    if clean.startswith("@"):  # allow entering like @domain.com
        clean = clean[1:]
    if not clean:
        raise TempMailError("Domain can not be empty.")
    return clean


def _random_local_part(length: int = 10) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _html_to_text(value: str) -> str:
    if not value:
        return ""
    stripped = _HTML_TAG_RE.sub("", value)
    return html.unescape(stripped).strip()


async def fetch_available_domains(force_refresh: bool = False) -> List[str]:
    """Fetch and cache the list of active domains from TempMail Plus."""

    global _DOMAIN_CACHE
    if _DOMAIN_CACHE is not None and not force_refresh:
        return list(_DOMAIN_CACHE)

    async with httpx.AsyncClient(timeout=10, headers=REQUEST_HEADERS) as client:
        try:
            response = await client.get(f"{API_BASE}/domains", params={"lang": DEFAULT_LANG})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TempMailError(f"Failed to fetch domain list: {exc}") from exc

    payload = response.json()
    candidates: List[str] = []

    if isinstance(payload, dict):
        for key in ("domains", "domain", "data", "items"):
            maybe = payload.get(key)
            if isinstance(maybe, list):
                candidates = maybe
                break
        else:
            # Some responses may already be flat, attempt to coerce
            if "domain" in payload and isinstance(payload["domain"], str):
                candidates = [payload]
    elif isinstance(payload, list):
        candidates = payload

    domains: List[str] = []
    for item in candidates:
        if isinstance(item, dict):
            domain = item.get("domain") or item.get("name")
            is_active = item.get("isActive", True)
            if isinstance(domain, str) and is_active:
                domains.append(domain.lower())
        elif isinstance(item, str):
            domains.append(item.lower())

    if not domains:
        raise TempMailError("Domain list from TempMail Plus was empty or malformed.")

    _DOMAIN_CACHE = domains
    logger.info("Fetched %d TempMail Plus domains", len(domains))
    return list(domains)


async def generate_mailbox(local_part: Optional[str] = None, domain: Optional[str] = None) -> Mailbox:
    """Create (locally) a mailbox descriptor for TempMail Plus."""

    domains = await fetch_available_domains()

    if local_part:
        normalized_local = _sanitize_local_part(local_part)
    else:
        normalized_local = _random_local_part()

    if domain:
        normalized_domain = _sanitize_domain(domain)
        if normalized_domain not in domains:
            raise TempMailError(
                f"Domain '{normalized_domain}' is not available. Use /domains to see valid options."
            )
    else:
        normalized_domain = secrets.choice(domains)

    return Mailbox(local_part=normalized_local, domain=normalized_domain)


def _extract_message_items(payload) -> List[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("mail_list", "mailList", "mails", "data", "items", "list"):
            maybe = payload.get(key)
            if isinstance(maybe, list):
                return [item for item in maybe if isinstance(item, dict)]
    return []


async def fetch_messages(mailbox: Mailbox) -> List[MessageMeta]:
    """Retrieve metadata for all messages in the mailbox."""

    params = {**mailbox.query_params(), "limit": 20, "page": 1, "sort": "desc"}

    async with httpx.AsyncClient(timeout=10, headers=REQUEST_HEADERS) as client:
        try:
            response = await client.get(f"{API_BASE}/mails", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TempMailError(f"Failed to fetch messages: {exc}") from exc

    payload = response.json()
    items = _extract_message_items(payload)
    if not items and isinstance(payload, dict) and "message" in payload:
        logger.debug("TempMail Plus response message: %s", payload.get("message"))

    messages: List[MessageMeta] = []
    for item in items:
        try:
            raw_id = item.get("id") or item.get("mail_id") or item.get("mailId")
            message_id = int(raw_id)
        except (TypeError, ValueError):
            logger.warning("Skipping mail item without numeric id: %s", item)
            continue

        sender = str(
            item.get("from")
            or item.get("sender")
            or item.get("from_email")
            or "(unknown sender)"
        ).strip()
        subject = str(item.get("subject") or item.get("title") or "(no subject)").strip()
        date = str(
            item.get("date")
            or item.get("time")
            or item.get("created_at")
            or item.get("timestamp")
            or "(no date)"
        ).strip()

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

    params = mailbox.query_params()

    async with httpx.AsyncClient(timeout=10, headers=REQUEST_HEADERS) as client:
        try:
            response = await client.get(f"{API_BASE}/mails/{message_id}", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TempMailError(f"Failed to read message {message_id}: {exc}") from exc

    payload = response.json()
    mail_data = None
    if isinstance(payload, dict):
        if isinstance(payload.get("mail"), dict):
            mail_data = payload["mail"]
        else:
            mail_data = payload

    if not isinstance(mail_data, dict):
        raise TempMailError("Unexpected response while reading message")

    sender = str(mail_data.get("from") or mail_data.get("sender") or "(unknown sender)").strip()
    subject = str(mail_data.get("subject") or mail_data.get("title") or "(no subject)").strip()
    date = str(
        mail_data.get("date")
        or mail_data.get("time")
        or mail_data.get("created_at")
        or mail_data.get("timestamp")
        or "(no date)"
    ).strip()

    text_body = str(
        mail_data.get("body_text")
        or mail_data.get("text")
        or mail_data.get("textBody")
        or mail_data.get("bodyPlain")
        or ""
    )
    if not text_body:
        html_body = str(
            mail_data.get("body_html")
            or mail_data.get("html")
            or mail_data.get("htmlBody")
            or ""
        )
        text_body = _html_to_text(html_body) if html_body else ""

    return {
        "from": sender or "(unknown sender)",
        "subject": subject or "(no subject)",
        "date": date or "(no date)",
        "text": text_body if text_body else "(No body)",
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
        "👋 Temp Mail bot, powered by tempmail.plus!\n\n"
        "Use /domains to browse available domains.\n"
        "Use /new to create a mailbox (example: /new hero inbox.me).\n"
        "You can also pass name@domain in a single argument.\n\n"
        "Once you have an address you can:\n"
        "• /address – see your current mailbox\n"
        "• /inbox – list incoming messages\n"
        "• /read <id> – open a specific message from the inbox\n\n"
        f"Current mailbox: {current_address}"
    )

    if update.message:
        await update.message.reply_text(message)


async def handle_domains(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        domains = await fetch_available_domains()
    except TempMailError as exc:
        logger.exception("Could not list domains")
        if update.message:
            await update.message.reply_text(f"⚠️ Error: {exc}")
        return

    if update.message:
        await update.message.reply_text(
            "Available domains:\n" + "\n".join(f"• {domain}" for domain in domains)
        )


def _parse_new_args(args: List[str]) -> Dict[str, Optional[str]]:
    local_part: Optional[str] = None
    domain: Optional[str] = None

    if not args:
        return {"local": None, "domain": None}

    if len(args) == 1 and "@" in args[0]:
        local_part, _, domain = args[0].partition("@")
        domain = domain or None
        local_part = local_part or None
    elif len(args) >= 2:
        local_part = args[0]
        domain = args[1]
    else:
        local_part = args[0]

    return {"local": local_part, "domain": domain}


async def handle_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = _parse_new_args(context.args)

    try:
        mailbox = await generate_mailbox(parts["local"], parts["domain"])
    except TempMailError as exc:
        logger.exception("Could not generate mailbox")
        if update.message:
            await update.message.reply_text(f"⚠️ Error: {exc}")
        return

    set_mailbox(context, mailbox)
    if update.message:
        await update.message.reply_text(
            "\n".join(
                [
                    "📬 Mailbox ready!",
                    f"Address: {mailbox.address}",
                    "Use /inbox to check for new messages.",
                ]
            )
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
    application.add_handler(CommandHandler("domains", handle_domains))
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

