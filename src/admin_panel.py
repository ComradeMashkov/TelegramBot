import configparser
import json
import os
import random

from datetime import datetime, timedelta
from dotenv import load_dotenv
from phrases import MARKS, DICKS_PHRASES, SURPRISE_PHRASES, QUESTION_MARKS, DUMB_PHRASES
import requests
from telegram import Update
from telegram.ext import CallbackContext
from utils import *


load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
CATS_API_KEY=os.getenv('CATS_API_KEY')

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'config.json')

MUTED_USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'muted_users.json')


def is_user_admin(update: Update, context: CallbackContext) -> bool:
    """Check if the user is an admin or creator in the chat, including anonymous admins."""
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id
    
    # Get the list of chat administrators
    chat_admins = context.bot.get_chat_administrators(chat_id)
    
    # Check if the user is in the list of administrators
    for admin in chat_admins:
        # Check if the admin is anonymous or if the user ID matches
        if admin.user.id == user_id or admin.is_anonymous:
            return True
    
    return False

def is_user_muted(update: Update, context: CallbackContext) -> bool:
    muted_usernames = get_recent_muted_usernames(MUTED_USERS_FILE)

    user = update.message.from_user

    if user.username in muted_usernames:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
        return True

def set_frequency(update: Update, context: CallbackContext) -> None:
    """Set the reply frequency, restricted to admins."""
    if is_user_muted(update, context):
        return
    
    # Check if the user is an admin
    if not is_user_admin(update, context):
        update.message.reply_text("Ты вообще не админ нихуя.")
        return
    
    user = update.message.from_user

    chat_id = str(update.effective_chat.id)
    config = load_config(CONFIG_FILE)

    # Ensure frequency is provided and is valid float
    if len(context.args) == 1:
        try:
            new_frequency = float(context.args[0])
            if 0 <= new_frequency <= 1:
                if chat_id not in config:
                    config[chat_id] = {}
                config[chat_id]['chat_name'] = update.effective_chat.title
                config[chat_id]['reply_frequency'] = new_frequency
                save_config(CONFIG_FILE, config)
                update.message.reply_text(f"Соотношение ответов установлено на {new_frequency * 100:.0f}%.")
            else:
                update.message.reply_text("Частота должна быть от 0 до 1.")
        except (IndexError, ValueError):
            update.message.reply_text("Какая-то хуйня. Частота должна быть от 0 до 1.")
    else:
        update.message.reply_text("Использование: /setfreq <частота> (напр., /setfreq 0.3)")

    print(f"Command /setfreq is called by {user.name}")

def set_sticker_frequency(update: Update, context: CallbackContext) -> None:
    """Set the sticker reply frequency, restricted to admins."""
    if is_user_muted(update, context):
        return
    
    # Check if the user is an admin
    if not is_user_admin(update, context):
        update.message.reply_text("Ты вообще не админ нихуя.")
        return
    
    user = update.message.from_user

    chat_id = str(update.effective_chat.id)
    config = load_config(CONFIG_FILE)

    # Ensure frequency is provided and is a valid float
    if len(context.args) == 1:
        try:
            new_stick_frequency = float(context.args[0])
            if 0 <= new_stick_frequency <= 1:
                if chat_id not in config:
                    config[chat_id] = {}
                config[chat_id]['chat_name'] = update.effective_chat.title
                config[chat_id]['sticker_frequency'] = new_stick_frequency
                save_config(CONFIG_FILE, config)
                update.message.reply_text(f"Соотношение стикеров в ответах установлено на {new_stick_frequency * 100:.0f}%.")
            else:
                update.message.reply_text("Частота должна быть от 0 до 1.")
        except (IndexError, ValueError):
            update.message.reply_text("Какая-то хуйня. Частота должна быть от 0 до 1.")
    else:
        update.message.reply_text("Использование: /setstick <частота> (напр., /setstick 0.3)")
    
    print(f"Command /setstick is called by {user.name}")

def mute_user(update: Update, context: CallbackContext) -> None:
    """Mute a user based on the /mute command, restricted to admins."""
    if is_user_muted(update, context):
        return

    if not is_user_admin(update, context):
        update.message.reply_text("Ты вообще не админ нихуя.")
        return
    
    if len(context.args) != 2:
        update.message.reply_text("Использование: /mute @имя_пользователя <минуты>.")
        return
    
    username = context.args[0].lstrip('@')

    try:
        minutes = int(context.args[1])
        if minutes <= 0:
            update.message.reply_text("Длительность должна быть целым положительным числом.")
            return
    except ValueError:
        update.message.reply_text("Какая-то хуйня. Введи нормальное число.")
        return
    
    # Load the list of muted users
    muted_users = load_muted_users(MUTED_USERS_FILE)

    # Add or update the username in the list with expiration time
    expiration_time = (datetime.utcnow() + timedelta(minutes=minutes)).isoformat()
    muted_users = {user['username']: user['expires_at'] for user in muted_users}
    muted_users[username] = expiration_time
    save_muted_users(MUTED_USERS_FILE, [{'username': user, 'expires_at': expires_at} for user, expires_at in muted_users.items()])

    update.message.reply_text(f"Ебальничек прикрыл? @{username} замучен на {minutes} мин.")

    print(f"Command /mute is called by {update.message.from_user.name}")

def unmute_user(update: Update, context: CallbackContext) -> None:
    """Unmute a user based on the /unmute command, restricted to admins."""
    if is_user_muted(update, context):
        return

    if not is_user_admin(update, context):
        update.message.reply_text("Ты вообще не админ нихуя.")
        return
    
    if not context.args:
        update.message.reply_text("А где ник пользователя? Использование: /unmute @имя_пользователя.")
        return
    
    # Extract the username to unmute
    username_to_unmute = context.args[0].lstrip('@')

    # Check if the username is valid
    if not username_to_unmute:
        update.message.reply_text("Какая-то хуйня. Использование: /unmute @имя_пользователя.")
        return
    
    # Load the muted users from the JSON file
    try:
        with open(MUTED_USERS_FILE, 'r') as f:
            muted_users = json.load(f)
    except FileNotFoundError:
        muted_users = []

    # Find the user in the muted list
    user_to_unmute = next((user for user in muted_users if user['username'] == username_to_unmute), None)

    # Check if the user is actually muted
    if user_to_unmute:
        muted_users.remove(user_to_unmute)
        # Save the updated muted users list back to the JSON file
        save_muted_users(MUTED_USERS_FILE, muted_users)

        update.message.reply_text(f"Ебальничек открыл? @{username_to_unmute} размучен.")
    else:
        update.message.reply_text(f"Пользователь @{username_to_unmute} не в муте. Может исправить это?")

    print(f"Command /unmute is called by {update.message.from_user.name}")


def get_cock_size(update: Update, context: CallbackContext) -> None:
    """Get cock size in cm."""
    if is_user_muted(update, context):
        return
    
    MINIMUM_SIZE = 3.0
    MAXIMUM_SIZE = 50.0
    cock_size = random.uniform(MINIMUM_SIZE, MAXIMUM_SIZE)
    cock_size = round(cock_size, 1)
    
    reply_text =  f"{random.choice(SURPRISE_PHRASES)}{random.choice(QUESTION_MARKS)} {random.choice(DICKS_PHRASES)} имеет размер аж {cock_size} см{random.choice(MARKS)}"

    update.message.reply_text(reply_text)

    print(f"Command /cock is called by {update.message.from_user.name}.")

def get_cat_picture(update: Update, context: CallbackContext) -> None:
    """Get random cat picture."""
    response = load_cat_picture(CATS_API_KEY, 1, False).text
    data = json.loads(response)
    image_url = data[0]['url']

    if is_user_muted(update, context):
        return
    
    update.message.reply_photo(image_url)

    print(f"Command /cat is called by {update.message.from_user.name}")

def get_dumb_rating(update: Update, context: CallbackContext) -> None:
    """Generate a random dumb rating for a user."""
    if update.message.reply_to_message:
        replied_user = update.message.reply_to_message.from_user
        if replied_user.username and not replied_user.is_bot:
            # Generating dumb rating
            rating = random.randint(0, 11)

            reply_text = f"Оценка тупости @{replied_user.username}: {rating}/10. {random.choice(DUMB_PHRASES[rating])}"
            update.message.reply_text(reply_text)
        else:
            update.message.reply_text("Ты не можешь использовать эту команду на группу или бота, ебанат.")
    else:
        update.message.reply_text("Используй команду /dumb в ответ на сообщение пользователя, ебанат.")

    print(f"Command /dumb is called by {update.message.from_user.name}")