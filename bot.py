import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import json
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
INITIAL_ADMIN_IDS = [int(id) for id in os.getenv('INITIAL_ADMIN_IDS', '').split(',')]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CHANNELS_FILE = 'channels.json'
ADMINS_FILE = 'admins.json'

class AnnouncementBot:
    def __init__(self):
        self.channels = set()
        self.admin_ids = set()
        self.last_messages = {}
        self.pending_announcements = {}
        self.load_channels()
        self.load_admins()

    def load_channels(self):
        if os.path.exists(CHANNELS_FILE):
            with open(CHANNELS_FILE, 'r') as f:
                self.channels = set(json.load(f))

    def save_channels(self):
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(list(self.channels), f)

    def load_admins(self):
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, 'r') as f:
                self.admin_ids = set(json.load(f))
        else:
            self.admin_ids = set(INITIAL_ADMIN_IDS)
            self.save_admins()

    def save_admins(self):
        with open(ADMINS_FILE, 'w') as f:
            json.dump(list(self.admin_ids), f)

    async def remove_channel(self, channel_id: int):
        if channel_id in self.channels:
            self.channels.remove(channel_id)
            self.save_channels()
            logger.info(f"Removed channel: {channel_id}")
            if channel_id in self.last_messages:
                del self.last_messages[channel_id]

    async def verify_channel_access(self, channel_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        try:
            bot_member = await context.bot.get_chat_member(
                chat_id=channel_id,
                user_id=context.bot.id
            )
            return bot_member.status not in ['left', 'kicked']
        except Exception:
            await self.remove_channel(channel_id)
            return False

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user:
            user_id = update.effective_user.id
            is_admin = self.is_admin(user_id)
            message = (
                'Hi! I\'m an announcement bot. Add me to channels and use /announce to send messages and /help to see the menu.\n'
                f'Your user ID is: {user_id}\n'
                f'Admin status: {"✅ You are an admin" if is_admin else "❌ You are not an admin"}'
            )
            await update.message.reply_text(message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        is_admin = self.is_admin(update.effective_user.id)
        help_text = """
🤖 <b>Announcement Bot Help</b>

<b>Basic Commands:</b>
• /start - Start the bot and see your user ID
• /help - Show this help message
"""
        if is_admin:
            help_text += """
<b>Admin Commands:</b>
• /announce - Send message to all channels (requires confirmation)
• /edit - Edit last sent message
• /preview - Preview how message will look
• /listchannels - Show all registered channels
• /listadmins - Show all admin users
• /addadmin - Add new admin
• /removeadmin - Remove admin

<b>Required HTML Tags for Formatting:</b>
• Bold: &lt;b&gt;text&lt;/b&gt;
• Code: &lt;code&gt;text&lt;/code&gt;
• Italic: &lt;i&gt;text&lt;/i&gt;
• Lists: Regular hyphens work (-)
• Links: URLs work automatically

<b>Example Message:</b>
/preview Hey everyone! Here's a &lt;b&gt;bold announcement&lt;/b&gt;:

- First point
- Second point

Using &lt;code&gt;code&lt;/code&gt; for technical terms.
Read more at https://docs.example.com
"""
        await update.message.reply_text(
            help_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    async def register_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat and chat.type in ['channel', 'supergroup', 'group']:
            chat_id = chat.id
            self.channels.add(chat_id)
            self.save_channels()
            logger.info(f"Registered new channel: {chat_id}")

    async def announce(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to send announcements.")
            return

        if not update.message.text:
            await update.message.reply_text("Please provide a message to announce.")
            return

        full_text = update.message.text
        if ' ' in full_text:
            message = full_text[full_text.find(' '):].strip()
        else:
            await update.message.reply_text("Please provide a message to announce.")
            return

        self.pending_announcements[user_id] = message

        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_announce"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_announce")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        preview_text = f"""
📢 <b>Confirm Announcement</b>

{message}

This message will be sent to {len(self.channels)} channels.
"""
        await update.message.reply_text(
            preview_text,
            reply_markup=reply_markup,
            parse_mode='HTML',
            disable_web_page_preview=False
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id

        if not self.is_admin(user_id):
            await query.answer("You don't have permission to do this.")
            return

        await query.answer()

        if query.data == "confirm_announce":
            if user_id not in self.pending_announcements:
                await query.edit_message_text("No pending announcement found.")
                return

            message = self.pending_announcements[user_id]
            success_count = 0
            fail_count = 0
            self.last_messages.clear()
            channels_to_remove = set()

            for channel_id in self.channels.copy():
                if not await self.verify_channel_access(channel_id, context):
                    channels_to_remove.add(channel_id)
                    fail_count += 1
                    continue

                try:
                    message_obj = await context.bot.send_message(
                        chat_id=channel_id,
                        text=message,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
                    self.last_messages[channel_id] = message_obj.message_id
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send message to channel {channel_id}: {e}")
                    channels_to_remove.add(channel_id)
                    fail_count += 1

            for channel_id in channels_to_remove:
                await self.remove_channel(channel_id)

            del self.pending_announcements[user_id]
            await query.edit_message_text(
                f"✅ Announcement sent to {success_count} channels.\n"
                f"❌ Failed to send to {fail_count} channels.\n"
                f"📝 Removed {len(channels_to_remove)} inaccessible channels."
            )

        elif query.data == "cancel_announce":
            if user_id in self.pending_announcements:
                del self.pending_announcements[user_id]
            await query.edit_message_text("❌ Announcement cancelled.")

    async def edit_announce(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to edit announcements.")
            return

        if not update.message.text:
            await update.message.reply_text("Please provide a message to edit.")
            return

        full_text = update.message.text
        if ' ' in full_text:
            message = full_text[full_text.find(' '):].strip()
        else:
            await update.message.reply_text("Please provide a message to edit.")
            return

        success_count = 0
        fail_count = 0
        channels_to_remove = set()

        for channel_id in self.channels.copy():
            if not await self.verify_channel_access(channel_id, context):
                channels_to_remove.add(channel_id)
                fail_count += 1
                continue

            if channel_id in self.last_messages:
                try:
                    await context.bot.edit_message_text(
                        chat_id=channel_id,
                        message_id=self.last_messages[channel_id],
                        text=message,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to edit message in channel {channel_id}: {e}")
                    channels_to_remove.add(channel_id)
                    fail_count += 1

        for channel_id in channels_to_remove:
            await self.remove_channel(channel_id)

        await update.message.reply_text(
            f"✅ Announcement edited in {success_count} channels.\n"
            f"❌ Failed to edit in {fail_count} channels.\n"
            f"📝 Removed {len(channels_to_remove)} inaccessible channels."
        )

    async def preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to preview announcements.")
            return

        if not update.message.text:
            await update.message.reply_text("Please provide a message to preview.")
            return

        full_text = update.message.text
        if ' ' in full_text:
            message = full_text[full_text.find(' '):].strip()
        else:
            await update.message.reply_text("Please provide a message to preview.")
            return

        try:
            preview_text = f"""
📢 <b>Preview of Announcement</b>

{message}

This message will be sent to {len(self.channels)} channels.
Use /announce with the same message to send it.
"""
            await update.message.reply_text(
                preview_text,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
        except Exception as e:
            await update.message.reply_text(
                "⚠️ Preview failed. Format guide:\n"
                "- <b>bold</b> for bold\n"
                "- <code>text</code> for code\n"
                "- <i>text</i> for italic"
            )

    async def list_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to list channels.")
            return

        if not self.channels:
            await update.message.reply_text("No channels registered yet.")
            return

        channels_text = "Registered channels:\n"
        for channel_id in self.channels:
            channels_text += f"- {channel_id}\n"
        await update.message.reply_text(channels_text)

    async def list_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to list admins.")
            return

        admins_text = "Admin users:\n"
        for admin_id in self.admin_ids:
            admins_text += f"- {admin_id}\n"
        await update.message.reply_text(admins_text)

    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to add admins.")
            return

        if not context.args:
            await update.message.reply_text("Please provide a user ID to add as admin.")
            return

        try:
            new_admin_id = int(context.args[0])
            self.admin_ids.add(new_admin_id)
            self.save_admins()
            await update.message.reply_text(f"✅ Added user {new_admin_id} as admin.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")

    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ You don't have permission to remove admins.")
            return

        if not context.args:
            await update.message.reply_text("Please provide a user ID to remove from admins.")
            return

        try:
            admin_id = int(context.args[0])
            if admin_id in self.admin_ids:
                if len(self.admin_ids) <= 1:
                    await update.message.reply_text("❌ Cannot remove the last admin.")
                    return
                self.admin_ids.remove(admin_id)
                self.save_admins()
                await update.message.reply_text(f"✅ Removed user {admin_id} from admins.")
            else:
                await update.message.reply_text("❌ User is not an admin.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")

def main():
    bot = AnnouncementBot()
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("announce", bot.announce))
    application.add_handler(CommandHandler("edit", bot.edit_announce))
    application.add_handler(CommandHandler("listchannels", bot.list_channels))
    application.add_handler(CommandHandler("listadmins", bot.list_admins))
    application.add_handler(CommandHandler("addadmin", bot.add_admin))
    application.add_handler(CommandHandler("removeadmin", bot.remove_admin))
    application.add_handler(CommandHandler("preview", bot.preview))
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL | filters.ChatType.GROUP | filters.ChatType.SUPERGROUP, bot.register_channel))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))

    application.run_polling()

if __name__ == '__main__':
    main()
