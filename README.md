# Telegram Temporary Email Bot 📧

A Telegram bot that allows users to create temporary email addresses and receive emails directly through Telegram.

## Features ✨

- 🎲 Generate random temporary email addresses
- 📬 Check inbox for received emails
- 📖 Read full email content
- 🔄 Auto-refresh inbox
- 🎨 Beautiful inline keyboard interface
- 🆓 Free - uses 1secmail.com API (no API key required)

## Setup 🚀

### 1. Get a Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token you receive

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Bot

```bash
python bot.py
```

When prompted, paste your bot token.

## Usage 📱

### Commands

- `/start` - Start the bot and see welcome message
- `/generate` - Generate a new temporary email address
- `/inbox` - Check your inbox for new emails
- `/email` - Display your current email address
- `/new` - Generate a new email (replaces current one)
- `/help` - Show help message

### How to Use

1. Start the bot with `/start`
2. Generate a temporary email with `/generate`
3. Use the email address wherever you need
4. Check `/inbox` to see received emails
5. Click on any email to read its full content

## Features in Detail 🔍

### Generate Email
Creates a random temporary email address using various domains:
- 1secmail.com
- 1secmail.org
- 1secmail.net
- esiix.com
- wwjmp.com

### Check Inbox
Shows all received emails with:
- Sender address
- Subject line
- Date/time received
- Quick read buttons

### Read Emails
View full email content including:
- Complete headers
- Text body
- HTML body (if available)

## Technical Details ⚙️

- **API**: Uses [1secmail.com](https://www.1secmail.com/) free API
- **Framework**: python-telegram-bot 20.7
- **Storage**: In-memory (for production, use a database)
- **Language**: Python 3.7+

## Limitations ⚠️

- Emails are temporary and expire after some time
- Storage is in-memory (restarts clear all data)
- Maximum 10 emails shown per inbox view
- Email content truncated to 3000 characters for readability

## Privacy 🔒

- No email data is permanently stored
- No user data is collected
- All emails are handled through public temporary email API
- Use responsibly and don't use for sensitive communications

## Future Enhancements 🎯

- [ ] Database integration for persistent storage
- [ ] Support for multiple email addresses per user
- [ ] Email notifications when new mail arrives
- [ ] Attachment support
- [ ] Email search functionality
- [ ] Custom email username selection

## License 📄

Free to use and modify. No warranty provided.

## Support 💬

For issues or questions, please create an issue in the repository.

---

**Note**: This bot uses temporary email services. Don't use these emails for important or sensitive communications!
