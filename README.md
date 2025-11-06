# 📧 Telegram Temp Mail Bot

Ekta advanced Telegram bot jekhane apni temporary email address create korte parben **@any.pink** domain diye.

## ✨ Main Features

### 🎯 Core Features:
- ✅ **1-Click Copy** - Email ar codes tap kore copy
- ✅ **Auto Notification** - Notun email ashle automatic notification
- ✅ **Code Detection** - OTP/Verification code automatically detect
- ✅ **@any.pink Domain** - Single, simple domain
- ✅ **Real-time Monitoring** - Background e inbox check kore
- ✅ **Clean Interface** - Simple 4 button menu

### 🔔 Auto Notification System:
- 📧 Notun email ashle instantly notification
- 🔑 Code detect korle special notification with copy button
- ⚡ 30 second e ekbar check kore
- 📱 Direct bot e notification asbe

### 📋 1-Click Copy:
- Email address - `<tap to copy>`
- Verification codes - `<tap to copy>`
- Easy ar fast!

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Bot Token

1. Telegram e jayen
2. `@BotFather` search koren
3. `/newbot` command send koren
4. Instructions follow koren
5. Token copy koren

### 3. Run Bot & Enter Token

```bash
python bot.py
```

## 📱 How to Use

### Simple Flow:

```
1. /start → Main Menu
2. 🎨 Create Email → Username send
3. Email ready: username@any.pink
4. Tap email to copy ✅
5. Wait for emails...
6. 🔔 Get notification automatically!
7. Tap code to copy ✅
```

## 🎯 Menu Buttons

### Main Menu (4 Buttons):
```
🎨 Create Email     → Custom email banao
📬 Check Inbox      → Inbox check koro
📧 My Email         → Current email dekho
🔑 Get Codes        → Sob codes extract koro
```

## 🔔 Auto Notification Examples

### Email with Code:
```
🔔 New Email with Code!

From: noreply@service.com
Subject: Your verification code

🔑 Codes Found:
123456 | ABC789

📋 Tap to copy

[📖 Read Full Email] [📬 Check Inbox]
```

### Normal Email:
```
📧 New Email Received!

From: support@website.com
Subject: Welcome to our service

[📖 Read Email] [📬 Check Inbox]
```

## 💡 Features in Detail

### 1. Email Creation
- Click **"🎨 Create Email"**
- Domain automatically set: `@any.pink`
- Send your username
- Email: `username@any.pink`
- Tap to copy! ✅

### 2. Auto Monitoring
- Bot background e 30 second interval e check kore
- Notun email detect korle notification send kore
- Code thakle special notification with copy button

### 3. Code Detection
Automatically detect kore:
- ✅ 4-8 digit codes (123456)
- ✅ Alphanumeric codes (ABC123)
- ✅ Codes with dashes (123-456)
- ✅ All copyable with 1 tap!

### 4. Copy Feature
HTML `<code>` tags use kora:
```
Email: username@any.pink  → Tap to copy
Code: 123456              → Tap to copy
```

## 🛠️ Technical Details

### Technologies:
- **API**: TempMail.plus
- **Framework**: python-telegram-bot 20.7
- **Domain**: any.pink only
- **Language**: Python 3.7+
- **Storage**: In-memory (lightweight)

### Background Monitoring:
```python
# Check every 30 seconds
job_queue.run_repeating(check_new_emails, interval=30, first=10)
```

### Copy Mechanism:
```python
# HTML code tags for tap-to-copy
<code>email@any.pink</code>
<code>123456</code>
```

## 📋 File Structure

```
/workspace/
├── bot.py              # Main bot code
├── requirements.txt    # Dependencies
├── .gitignore         # Git ignore
└── README.md          # This file
```

## 🔒 Security & Privacy

- ⚠️ Temporary emails only
- ⚠️ Don't use for sensitive data
- ✅ No personal data stored
- ✅ In-memory storage (clears on restart)
- ✅ Bot token entered in terminal (not saved)

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run bot
python bot.py

# 3. Terminal e token paste koren when prompted

# 4. Telegram e /start
```

## 🎯 Use Cases

✅ Social media signup  
✅ Website testing  
✅ OTP receive  
✅ Temporary registration  
✅ Newsletter test  
✅ Service verification  
✅ Privacy protection  

## 📊 Features Summary

| Feature | Status |
|---------|--------|
| 1-Click Copy | ✅ |
| Auto Notification | ✅ |
| Code Detection | ✅ |
| Background Monitoring | ✅ |
| Single Domain (@any.pink) | ✅ |
| Terminal Token Input | ✅ |
| Simple 4-Button UI | ✅ |
| Real-time Updates | ✅ |

## 🐛 Troubleshooting

### Bot not starting?
```bash
# Make sure you entered correct token
# Get new token from @BotFather if needed

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### No notifications?
- Make sure bot is running
- Check terminal for errors
- Wait 30 seconds for first check
- Send test email to your temp address

### Can't copy email/code?
- Make sure using official Telegram app
- Try long-press on the text
- Code tags work on mobile & desktop

## 🔄 Updates & Improvements

### Current Version Features:
- [x] Auto notification system
- [x] 1-click copy functionality
- [x] Code detection & extraction
- [x] Background monitoring
- [x] Terminal token input

### Future Plans:
- [ ] Database integration
- [ ] Multiple domains option
- [ ] Custom notification interval
- [ ] Email forwarding
- [ ] Attachment support

## 💬 Support

Issues ba questions hole:
- Check terminal output for errors
- Read this README carefully
- Test with a simple email first

## 📄 License

Free to use and modify for personal use.

---

**🎉 Enjoy using the bot!**

*Made with ❤️ for easy temporary emails*

**Remember:** 
- Tap email to copy ✅
- Tap codes to copy ✅
- Get auto notifications 🔔
- Simple & fast! ⚡
