#!/usr/bin/env python3
"""
Telegram Temporary Email Bot
Allows users to create temporary email addresses and receive emails through Telegram
"""

import asyncio
import logging
import random
import string
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 1secmail API endpoints
API_BASE = "https://www.1secmail.com/api/v1/"

# User data storage (in production, use a database)
user_emails = {}


def generate_random_email():
    """Generate a random temporary email address"""
    domains = ['1secmail.com', '1secmail.org', '1secmail.net', 'esiix.com', 'wwjmp.com']
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(domains)
    return f"{username}@{domain}"


def get_inbox(email):
    """Get inbox for a temporary email"""
    try:
        login, domain = email.split('@')
        url = f"{API_BASE}?action=getMessages&login={login}&domain={domain}"
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        logger.error(f"Error getting inbox: {e}")
        return []


def read_email(email, email_id):
    """Read a specific email"""
    try:
        login, domain = email.split('@')
        url = f"{API_BASE}?action=readMessage&login={login}&domain={domain}&id={email_id}"
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error reading email: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    
    welcome_message = (
        "🎉 *Welcome to Temp Mail Bot!*\n\n"
        "I can help you create temporary email addresses to protect your privacy.\n\n"
        "*Available Commands:*\n"
        "/generate - Generate a new temporary email\n"
        "/inbox - Check your inbox\n"
        "/email - Show your current email address\n"
        "/new - Generate a new email (replaces current)\n"
        "/help - Show this help message\n\n"
        "Let's get started! Use /generate to create your first temp email."
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "*Temp Mail Bot Help* 📧\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/generate - Generate a new temporary email\n"
        "/inbox - Check your inbox for new emails\n"
        "/email - Display your current email address\n"
        "/new - Generate a new email address\n"
        "/help - Show this help message\n\n"
        "*How it works:*\n"
        "1️⃣ Generate a temporary email using /generate\n"
        "2️⃣ Use that email wherever you need\n"
        "3️⃣ Check /inbox to see received emails\n"
        "4️⃣ Click on any email to read its content\n\n"
        "⚠️ *Note:* Emails are temporary and will expire after some time."
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def generate_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a new temporary email for the user"""
    user_id = update.effective_user.id
    
    # Generate new email
    email = generate_random_email()
    user_emails[user_id] = email
    
    keyboard = [
        [InlineKeyboardButton("📬 Check Inbox", callback_data='check_inbox')],
        [InlineKeyboardButton("🔄 Generate New Email", callback_data='new_email')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"✅ *Your Temporary Email:*\n\n"
        f"`{email}`\n\n"
        f"📋 Tap to copy the email address\n"
        f"📧 Use this email wherever you need\n"
        f"📬 Check your inbox using the button below"
    )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current email address"""
    user_id = update.effective_user.id
    
    if user_id not in user_emails:
        await update.message.reply_text(
            "❌ You don't have an email yet!\n"
            "Use /generate to create one."
        )
        return
    
    email = user_emails[user_id]
    keyboard = [
        [InlineKeyboardButton("📬 Check Inbox", callback_data='check_inbox')],
        [InlineKeyboardButton("🔄 Generate New Email", callback_data='new_email')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"📧 *Your Current Email:*\n\n"
        f"`{email}`\n\n"
        f"Tap to copy the email address"
    )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def check_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check inbox for new emails"""
    user_id = update.effective_user.id
    
    if user_id not in user_emails:
        await update.message.reply_text(
            "❌ You don't have an email yet!\n"
            "Use /generate to create one."
        )
        return
    
    email = user_emails[user_id]
    status_msg = await update.message.reply_text("🔍 Checking inbox...")
    
    inbox = get_inbox(email)
    
    if not inbox:
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data='check_inbox')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_msg.edit_text(
            f"📭 *Inbox Empty*\n\n"
            f"No emails received yet for:\n`{email}`\n\n"
            f"Emails will appear here when received.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    # Show inbox with buttons for each email
    keyboard = []
    message = f"📬 *Inbox for:* `{email}`\n\n"
    message += f"📨 *{len(inbox)} email(s) received:*\n\n"
    
    for idx, mail in enumerate(inbox[:10], 1):  # Show max 10 emails
        from_addr = mail.get('from', 'Unknown')
        subject = mail.get('subject', 'No Subject')
        date = mail.get('date', '')
        email_id = mail.get('id')
        
        message += f"{idx}. *From:* {from_addr}\n"
        message += f"   *Subject:* {subject}\n"
        message += f"   *Date:* {date}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"📖 Read Email #{idx}",
                callback_data=f'read_{email_id}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data='check_inbox')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await status_msg.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == 'check_inbox':
        if user_id not in user_emails:
            await query.edit_message_text("❌ You don't have an email yet!\nUse /generate to create one.")
            return
        
        email = user_emails[user_id]
        await query.edit_message_text("🔍 Checking inbox...")
        
        inbox = get_inbox(email)
        
        if not inbox:
            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data='check_inbox')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📭 *Inbox Empty*\n\n"
                f"No emails received yet for:\n`{email}`\n\n"
                f"Emails will appear here when received.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        # Show inbox
        keyboard = []
        message = f"📬 *Inbox for:* `{email}`\n\n"
        message += f"📨 *{len(inbox)} email(s) received:*\n\n"
        
        for idx, mail in enumerate(inbox[:10], 1):
            from_addr = mail.get('from', 'Unknown')
            subject = mail.get('subject', 'No Subject')
            date = mail.get('date', '')
            email_id = mail.get('id')
            
            message += f"{idx}. *From:* {from_addr}\n"
            message += f"   *Subject:* {subject}\n"
            message += f"   *Date:* {date}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"📖 Read Email #{idx}",
                    callback_data=f'read_{email_id}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data='check_inbox')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data == 'new_email':
        email = generate_random_email()
        user_emails[user_id] = email
        
        keyboard = [
            [InlineKeyboardButton("📬 Check Inbox", callback_data='check_inbox')],
            [InlineKeyboardButton("🔄 Generate New Email", callback_data='new_email')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"✅ *New Temporary Email Generated:*\n\n"
            f"`{email}`\n\n"
            f"📋 Tap to copy the email address"
        )
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data.startswith('read_'):
        email_id = data.split('_')[1]
        
        if user_id not in user_emails:
            await query.edit_message_text("❌ You don't have an email yet!")
            return
        
        email = user_emails[user_id]
        await query.edit_message_text("📖 Loading email...")
        
        email_data = read_email(email, email_id)
        
        if not email_data:
            await query.edit_message_text("❌ Failed to load email. It might have been deleted.")
            return
        
        from_addr = email_data.get('from', 'Unknown')
        subject = email_data.get('subject', 'No Subject')
        date = email_data.get('date', '')
        body = email_data.get('textBody', email_data.get('htmlBody', 'No content'))
        
        # Truncate body if too long
        if len(body) > 3000:
            body = body[:3000] + "\n\n... [Content truncated]"
        
        message = (
            f"📧 *Email Details*\n\n"
            f"*From:* {from_addr}\n"
            f"*Subject:* {subject}\n"
            f"*Date:* {date}\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"{body}"
        )
        
        keyboard = [
            [InlineKeyboardButton("◀️ Back to Inbox", callback_data='check_inbox')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, parse_mode='Markdown', reply_markup=reply_markup)


def main():
    """Start the bot"""
    # Get bot token from user
    print("=" * 50)
    print("TELEGRAM TEMP MAIL BOT")
    print("=" * 50)
    print("\nTo run this bot, you need a Telegram Bot Token.")
    print("Get one from @BotFather on Telegram.")
    print("\nSteps:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot and follow the instructions")
    print("3. Copy the token and paste it below")
    print("=" * 50)
    
    token = input("\nEnter your bot token: ").strip()
    
    if not token:
        print("❌ No token provided. Exiting...")
        return
    
    print("\n🚀 Starting bot...")
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_email))
    application.add_handler(CommandHandler("new", generate_email))
    application.add_handler(CommandHandler("email", show_email))
    application.add_handler(CommandHandler("inbox", check_inbox))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the Bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
