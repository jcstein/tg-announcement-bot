# Telegram Announcement Bot

A Telegram bot for sending formatted announcements to multiple channels simultaneously.

## Features
- Send formatted announcements to multiple channels
- Preview messages before sending
- Support HTML formatting (bold, italic, code blocks)
- Admin management system
- Auto-registration of channels when bot is added

## Setup

1. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install python-telegram-bot
```

2. Get a bot token:
- Message @BotFather on Telegram
- Create new bot with `/newbot`
- Save the token

3. Configure bot:
- Create a `config.py` file
- Add your bot token as `BOT_TOKEN = "your-token-here"`
- Add your Telegram ID as `INITIAL_ADMIN_IDS = [your-id-number]`

4. Run the bot:
```bash
python bot.py
```

## Commands

Basic Commands:
- `/start` - Get your user ID and check admin status
- `/help` - Show available commands

Admin Commands:
- `/announce` - Send announcement to all channels
- `/preview` - Preview formatted message
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
3. Use /announce to send messages to all channels at once
4. Use /preview to test your message formatting
