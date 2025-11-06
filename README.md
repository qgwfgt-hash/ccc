# 📧 Advanced Telegram Temp Mail Bot

Ekta powerful Telegram bot jekhane apni temporary email address create korte parben **TempMail.plus** use kore.

## ✨ Features

### 🎯 Main Features:
- ✅ **Custom Email Create** - Nijer moto username diye email banano
- ✅ **Multiple Domains** - 10+ domain theke choose korte parben
- ✅ **Code Detection** - OTP/Verification code automatically detect kore
- ✅ **Real-time Inbox** - Instantly email receive hobe
- ✅ **Beautiful Interface** - Clean and easy to use buttons
- ✅ **Powered by TempMail.plus** - Reliable service

### 🔑 Code Detection Features:
- Automatically detect 4-8 digit codes
- Detect alphanumeric codes (ABC123)
- Detect codes with dashes (123-456)
- Show codes separately with one click
- Highlight emails with codes

## 🚀 Setup Korte

### 1. Bot Token Paan

1. Telegram e jayen
2. `@BotFather` search koren
3. `/newbot` command send koren
4. Instructions follow koren
5. Token copy koren

### 2. Dependencies Install Koren

```bash
pip install -r requirements.txt
```

### 3. Bot Run Koren

```bash
python bot.py
```

Token paste koren jokhn asked hobe.

## 📱 Kivabe Use Korben

### Commands:

```
/start      - Bot start koren
/create     - Custom email create (nijer username)
/random     - Random email instantly
/inbox      - Inbox check koren
/email      - Current email dekhun
/codes      - Sob codes extract koren
/domains    - Available domains dekhun
/help       - Help message
```

### Step by Step Guide:

#### 1️⃣ Custom Email Create:

```
/create → Domain select → Username send → Email ready!
```

**Example:**
- Command: `/create`
- Select domain: `@tempmail.plus`
- Send username: `myemail123`
- Result: `myemail123@tempmail.plus` ✅

#### 2️⃣ Random Email (Quick):

```
/random → Instantly email ready!
```

#### 3️⃣ Check Inbox:

```
/inbox → Sob emails dekhun → Click to read
```

#### 4️⃣ Extract Codes:

```
/codes → Automatically sob OTP/codes show hobe
```

## 🌐 Available Domains

- tempmail.plus
- mailto.plus
- bumbarash.com
- easytrashmail.com
- fthcapital.com
- clipmail.eu
- tmail.plus
- disbox.org
- mail.tm
- guerrillamail.com

## 🔑 Code Detection Examples

Bot automatically detect korbe:

```
✅ 123456        (6 digit OTP)
✅ 1234          (4 digit code)
✅ ABC123XYZ     (Alphanumeric)
✅ 123-456       (Code with dash)
✅ 12345678      (8 digit code)
```

## 📋 Features in Detail

### Custom Email Creation
- Apnar choice er username
- 10+ domain theke select
- Username rules:
  - 3-20 characters
  - Letters, numbers, dots, dashes allowed
  - No spaces

### Auto Code Detection
- Email receive korle automatically code detect
- `/codes` command e sob codes eksathe
- Email list e 🔑 icon jodi code thake
- Email read korle codes highlight hobe

### Real-time Updates
- Instant email receive
- Refresh button diye update
- Fast API response
- No delay

## 🛠️ Technical Details

- **API**: TempMail.plus
- **Framework**: python-telegram-bot 20.7
- **Language**: Python 3.7+
- **Dependencies**: requests, python-telegram-bot

## ⚠️ Important Notes

1. **Temporary Emails**: Emails temporary, kichu time por expire hobe
2. **Privacy**: Sensitive information send korben na
3. **Storage**: In-memory storage (restart e clear)
4. **Codes**: Automatically detect hobe common formats

## 🎨 Bot Interface

### Inline Buttons:
- 📬 Check Inbox - Inbox dekhun
- 🔄 New Email - Notun email
- 🔑 Extract Codes - Codes ber koren
- 📖 Read Email - Email poren
- ◀️ Back - Pichone jan

### Auto Features:
- Code detection with 🔑 icon
- Email counter
- Subject preview
- From address display

## 💡 Use Cases

✅ Social media signup
✅ Website testing
✅ OTP receive
✅ Temporary registration
✅ Newsletter subscription
✅ Service testing
✅ Privacy protection

## 🔒 Security & Privacy

- No personal data stored
- Temporary emails only
- API calls encrypted
- No database needed
- All data in-memory

## 🚀 Advanced Features

### Batch Operations:
- Check multiple emails at once
- Extract all codes together
- Refresh inbox quickly

### Smart Detection:
- Auto detect verification codes
- Highlight code emails
- Quick code access

### User Friendly:
- Simple commands
- Clear instructions
- Beautiful interface
- Fast response

## 📞 Support

Issues ba questions hole:
- GitHub issues create koren
- Code review koren
- Documentation poren

## 🎯 Future Plans

- [ ] Database integration
- [ ] Multiple email support
- [ ] Email notifications
- [ ] Attachment support
- [ ] Email search
- [ ] Custom domain addition
- [ ] Email forwarding
- [ ] Auto-delete old emails

## 📄 License

Free to use and modify. Educational purposes only.

## ⭐ Credits

- TempMail.plus API
- python-telegram-bot
- Telegram Bot API

---

**🎉 Enjoy using the bot!**

*Remember: Only use for temporary purposes, not for sensitive data!*
