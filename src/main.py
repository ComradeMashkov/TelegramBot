import configparser
import os
import phrases
import random

from admin_panel import *
from admin_panel import TOKEN, MUTED_USERS_FILE
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from utils import get_recent_muted_usernames


CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

STICKERS_FILE_PATH = 'assets/stickers/'
STICKERS_LIST = [STICKERS_FILE_PATH + sticker_rel_path for sticker_rel_path in os.listdir(STICKERS_FILE_PATH)]


def handle_comment(update: Update, context: CallbackContext) -> None:
    # Reload config to get the latest frequency
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    reply_frequency = float(config.get('settings', 'reply_frequency'))
    sticker_frequency = float(config.get('settings', 'sticker_frequency'))

    muted_usernames = get_recent_muted_usernames(MUTED_USERS_FILE)

    # Ensure that update.message is not None and it is not post
    if update.message and update.message.from_user.name != 'Telegram':
        # Get the user who sent the comment
        user = update.message.from_user

        if user.username in muted_usernames:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            return # Ignore further processing of this message
        
        # Generate a random number between 0 and 1
        chance_to_answer = random.random()

        reply_text = f"{random.choice(phrases.DECLINE_REPLIES)}{random.choice(phrases.MARKS)}"
        
        if chance_to_answer < reply_frequency:
            print(f"Answering for user: {user.name}, his message: \"{update.message.text}\"")

            chance_to_send_sticker = random.random()

            if chance_to_send_sticker < sticker_frequency:
                sticker_name = random.choice(STICKERS_LIST)
                with open(sticker_name, 'rb') as sticker_file:
                    context.bot.send_sticker(
                        chat_id=update.effective_chat.id,
                        sticker=InputFile(sticker_file),
                        reply_to_message_id=update.message.message_id  # Reply to the specific comment
                    )
            else:
                # Send a reply to the user who sent the comment
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=reply_text,  # Responding to the user with a personalized message
                    reply_to_message_id=update.message.message_id  # Reply to the specific comment
                )

def main():
    # Create an Updater object with your bot token
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register a handler for commands
    dispatcher.add_handler(CommandHandler('setfreq', set_frequency, pass_args=True))
    dispatcher.add_handler(CommandHandler('setstick', set_sticker_frequency, pass_args=True))
    dispatcher.add_handler(CommandHandler('mute', mute_user, pass_args=True))
    dispatcher.add_handler(CommandHandler('unmute', unmute_user, pass_args=True))
    dispatcher.add_handler(CommandHandler('cock', get_cock_size))
    dispatcher.add_handler(CommandHandler('cat', get_cat_picture))
    dispatcher.add_handler(CommandHandler('dumb', get_dumb_rating))

    # Register a handler for all text messages
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_comment))

    # Start the bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()