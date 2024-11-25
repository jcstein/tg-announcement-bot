# Telegram Announcement Bot
A Telegram bot for sending formatted announcements to multiple channels simultaneously.

## Features
- Send formatted announcements to multiple channels
- Preview and confirm messages before sending 
- Edit previously sent announcements (within 48 hours)
- Support HTML formatting (bold, italic, code blocks)
- Admin management system
- Auto-registration of channels when bot is added
- Failed message and channel tracking

## Setup
1. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install python-telegram-bot python-dotenv
```

2. Get a bot token:
- Message @BotFather on Telegram
- Create new bot with `/newbot`
- Save the token

3. Configure bot:
- Create `.env` file
- Add your bot token as `BOT_TOKEN=your-token-here`
- Add your Telegram ID as `INITIAL_ADMIN_IDS=your-id-number`

4. Run the bot:
```bash
python bot.py
```

## Commands
Basic Commands:
- `/start` - Get your user ID and check admin status
- `/help` - Show available commands

Admin Commands:
- `/preview` - Preview formatted message
- `/announce` - Send announcement to all channels (requires confirmation)
- `/edit` - Edit last sent message (within 48 hours & requires confirmation)
- `/listchannels` - Show registered channels
- `/listadmins` - Show admin users
- `/addadmin` - Add new admin
- `/removeadmin` - Remove admin

## Message Formatting
Supported HTML tags:
```
<b>bold text</b>
<i>italic text</i>
<code>code blocks</code>
```

Example message:
```
/preview This is <b>bold</b> and this is <code>code</code>
list:
- first item
- second item
And <i>italic</i>
```

## Usage
1. Add the bot to your channels
2. The bot will automatically register the channels
3. Use `/preview` to compose and check your message formatting
4. Once satisfied with preview, use `/announce` with the same message
5. Review the send confirmation:
   - ✅ Click Confirm to send to all channels
   - ❌ Click Cancel to abort
6. Bot will report:
   - Total messages successfully sent
   - Total messages failed
   - Number of inaccessible channels removed
7. Use `/edit` to modify any message (within 48 hours)
   - Preview changes and confirm/cancel
   - Get summary of successful and failed edits
