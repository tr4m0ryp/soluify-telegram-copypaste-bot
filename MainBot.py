
#!/usr/bin/env python3
# ==============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {telegram-copypaste-bot v3.2}
# ==============================================================================
#  __         _
# (_  _ |   .(_
# __)(_)||_||| \/
#              /
# © 2025 Soluify LLC
# ------------------------------------------------------------------------------
# This improved version uses a user account as an intermediary to read messages
# from source channels/groups (which the bot cannot access) and then uses a bot
# account to forward the messages to destination chats.
#
# Additionally, it cleans the forwarded messages by removing any content starting
# with the unwanted footer "📹 YouTube". It also uses a background thread for
# exit command detection, which works reliably on Windows.
# ==============================================================================
import asyncio
import random
import re
import sys
import time
import json
import signal
import logging
import os
import threading
from datetime import datetime

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError, ChatForwardsRestrictedError
from colorama import init
from tqdm import tqdm
from tqdm.asyncio import tqdm as atqdm
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass

init(autoreset=True)

# ------------------------------------------------------------------------------
# Configuration files and constants
# ------------------------------------------------------------------------------
CONFIG_FILE = 'telegramconfiguration.json'
CREDENTIALS_FILE = 'credentials.json'
LOG_FILE = 'soluify.log'
MAX_RETRIES = 3
RETRY_DELAY = 5

# ------------------------------------------------------------------------------
# Colors and gradient settings
# ------------------------------------------------------------------------------
MAIN_COLOR_START = (147, 112, 219)  # Medium Purple
MAIN_COLOR_END = (0, 191, 255)      # Deep Sky Blue
ALERT_COLOR = (255, 69, 0)          # Red-Orange
SUCCESS_COLOR = (50, 205, 50)       # Lime Green
PROMPT_COLOR_START = (0, 255, 255)  # Cyan
PROMPT_COLOR_END = (135, 206, 250)  # Light Sky Blue

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
def setup_logger():
    logger = logging.getLogger('soluify')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.ERROR)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

# ------------------------------------------------------------------------------
# Gradient text function
# ------------------------------------------------------------------------------
def gradient_text(text, start_color, end_color, emoji=None):
    start_r, start_g, start_b = start_color
    end_r, end_g, end_b = end_color
    gradient = []
    length = len(text)
    for i, char in enumerate(text):
        r = start_r + (end_r - start_r) * i / (length or 1)
        g = start_g + (end_g - start_g) * i / (length or 1)
        b = start_b + (end_b - start_b) * i / (length or 1)
        gradient.append(f"\033[38;2;{int(r)};{int(g)};{int(b)}m{char}\033[0m")
    result = ''.join(gradient)
    if emoji:
        result += f" {emoji}"
    return result

# ------------------------------------------------------------------------------
# Animation function
# ------------------------------------------------------------------------------
async def animated_transition(text, duration=0.5):
    emojis = ["✨", "🚀", "💫", "🌟", "💡", "🔮", "🎉"]
    for _ in range(int(duration * 10)):
        emoji = random.choice(emojis)
        print(f"\r{gradient_text(text, MAIN_COLOR_START, MAIN_COLOR_END, emoji)}", end="", flush=True)
        await asyncio.sleep(0.05)
    print()

# ------------------------------------------------------------------------------
# Functions for encryption/decryption of credentials
# ------------------------------------------------------------------------------
def get_key(password):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'soluify_salt',  # In production, use a random salt
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_data(data, password):
    key = get_key(password)
    f = Fernet(key)
    return f.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data, password):
    key = get_key(password)
    f = Fernet(key)
    return json.loads(f.decrypt(encrypted_data).decode())

# ------------------------------------------------------------------------------
# Store/read bot credentials (for bot client) – these can be encrypted if desired
# ------------------------------------------------------------------------------
def store_credentials():
    print(gradient_text("LET OP: You are about to enter your Telegram Bot API credentials.", ALERT_COLOR, ALERT_COLOR, "🚨"))
    print(gradient_text("Keep these credentials safe. Your bot token is like a key!", ALERT_COLOR, ALERT_COLOR))
    proceed = input(gradient_text("Do you want to continue? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    if proceed.lower() != 'y':
        print(gradient_text("Operation cancelled. Exiting.", MAIN_COLOR_START, MAIN_COLOR_END))
        sys.exit(0)
    api_id = getpass.getpass(gradient_text("Enter your Bot API ID: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    api_hash = getpass.getpass(gradient_text("Enter your Bot API Hash: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    bot_token = getpass.getpass(gradient_text("Enter your Bot Token (e.g. 123456:ABC-...): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    save_choice = input(gradient_text("Do you want to save these credentials for future use? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    print(gradient_text("For security reasons, saving credentials is not always recommended.", ALERT_COLOR, ALERT_COLOR, "⚠️"))
    if save_choice.lower() == 'y':
        password = getpass.getpass(gradient_text("Choose a strong password to encrypt your credentials: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
        credentials = {
            'api_id': api_id,
            'api_hash': api_hash,
            'bot_token': bot_token
        }
        encrypted_data = encrypt_data(credentials, password)
        with open(CREDENTIALS_FILE, 'wb') as f:
            f.write(encrypted_data)
        print(gradient_text("Credentials saved and encrypted.", SUCCESS_COLOR, SUCCESS_COLOR, "🔐"))
    else:
        print(gradient_text("Credentials will not be permanently saved.", MAIN_COLOR_START, MAIN_COLOR_END))
    return save_choice.lower() == 'y', api_id, api_hash, bot_token

def read_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        return None, None, None
    password = getpass.getpass(gradient_text("Enter your password to decrypt your bot credentials: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    try:
        with open(CREDENTIALS_FILE, 'rb') as f:
            encrypted_data = f.read()
        credentials = decrypt_data(encrypted_data, password)
        print(gradient_text("Credentials decrypted! Welcome back!", SUCCESS_COLOR, SUCCESS_COLOR, "🎉"))
        return credentials['api_id'], credentials['api_hash'], credentials['bot_token']
    except Exception as e:
        logger.error(f"Error reading credentials: {e}")
        print(gradient_text(f"Error decrypting credentials: {e}", ALERT_COLOR, ALERT_COLOR))
        return None, None, None

# ------------------------------------------------------------------------------
# Function to get user account credentials for reading messages
# ------------------------------------------------------------------------------
def get_user_credentials():
    print(gradient_text("Enter your USER credentials (for reading messages).", MAIN_COLOR_START, MAIN_COLOR_END, "👤"))
    user_api_id = getpass.getpass(gradient_text("Enter your User API ID: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    user_api_hash = getpass.getpass(gradient_text("Enter your User API Hash: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    phone_number = input(gradient_text("Enter your phone number (e.g. +123456789): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    return user_api_id, user_api_hash, phone_number

# ------------------------------------------------------------------------------
# Exit listener function (runs in a separate thread)
# ------------------------------------------------------------------------------
def exit_listener(forwarder):
    # Wait for user input; if "exit" is typed, stop forwarding.
    while forwarder.running:
        line = input()
        if line.strip().lower() == "exit":
            forwarder.running = False
            break

# ------------------------------------------------------------------------------
# Class for message forwarding using two clients:
# reader_client (user account) to fetch messages, sender_client (bot) to send messages.
# Now with text cleaning to remove unwanted footers.
# ------------------------------------------------------------------------------
class TelegramForwarder:
    def __init__(self, reader_client, sender_client):
        self.reader = reader_client
        self.sender = sender_client
        self.running = False
        self.blacklist = []

    async def ensure_connections(self):
        for client in (self.reader, self.sender):
            if not client.is_connected():
                try:
                    await client.connect()
                except Exception as e:
                    logger.error(f"Error connecting client: {e}")
                    return False
        return True

    async def list_chats(self):
        """
        Lists chats from the reader client (user account) which has access to more chats.
        """
        if not await self.ensure_connections():
            return
        dialogs = await self.reader.get_dialogs()
        filename = "chats_of_reader.txt"
        with open(filename, "w") as chats_file, tqdm(
            total=len(dialogs),
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
            ncols=75
        ) as pbar:
            for dialog in dialogs:
                chat_info = f"Chat ID: {dialog.id}, Title: {dialog.title}"
                print(gradient_text(chat_info, MAIN_COLOR_START, MAIN_COLOR_END))
                chats_file.write(chat_info + "\n")
                pbar.update(1)
        print(gradient_text("Chat list written to file!", SUCCESS_COLOR, SUCCESS_COLOR, "🎉"))

    async def forward_messages_to_channels(self, source_chat_ids, destination_channel_ids, keywords, signature):
        """
        Forwards messages from source chats (fetched by the user account)
        to destination chats (sent by the bot). Unwanted footer text starting with
        "📹 YouTube" is removed before sending.
        """
        if not await self.ensure_connections():
            return
        self.running = True
        # Start the exit listener in a background thread.
        thread = threading.Thread(target=exit_listener, args=(self,))
        thread.daemon = True
        thread.start()
        # Initialize last_message_ids for each source chat.
        last_message_ids = {}
        for chat_id in source_chat_ids:
            msgs = await self.reader.get_messages(chat_id, limit=1)
            last_message_ids[chat_id] = msgs[0].id if msgs else 0
        while self.running:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(gradient_text(f"[{timestamp}] Checking for new messages...", MAIN_COLOR_START, MAIN_COLOR_END, "👀"))
            try:
                for chat_id in source_chat_ids:
                    messages = await self.reader.get_messages(chat_id, min_id=last_message_ids[chat_id], limit=None)
                    for message in reversed(messages):
                        should_forward = False
                        if keywords:
                            if message.text and any(keyword.lower() in message.text.lower() for keyword in keywords):
                                should_forward = True
                        else:
                            should_forward = True
                        if message.text and any(bad.lower() in message.text.lower() for bad in self.blacklist):
                            should_forward = False
                        if should_forward:
                            if message.text:
                                clean_text = message.text
                                if "📹 YouTube" in clean_text:
                                    clean_text = clean_text.split("📹 YouTube")[0].strip()
                                if clean_text:
                                    for dest_id in destination_channel_ids:
                                        await self.sender.send_message(dest_id, clean_text + f"\n\n**{signature}**")
                            if message.media:
                                media_path = await self.reader.download_media(message.media)
                                if message.text:
                                    clean_text = message.text
                                    if "📹 YouTube" in clean_text:
                                        clean_text = clean_text.split("📹 YouTube")[0].strip()
                                    caption_text = f"{clean_text}\n\n**{signature}**" if clean_text else f"**{signature}**"
                                else:
                                    caption_text = f"**{signature}**"
                                for dest_id in destination_channel_ids:
                                    await self.sender.send_file(dest_id, media_path, caption=caption_text)
                            print(gradient_text(f"[{timestamp}] Message forwarded!", SUCCESS_COLOR, SUCCESS_COLOR, "✅"))
                            last_message_ids[chat_id] = max(last_message_ids[chat_id], message.id)
            except FloodWaitError as e:
                logger.error(f"Flood wait error: {e}. Waiting {e.seconds} seconds.")
                print(gradient_text(f"Flood wait error: {e}. Pausing for {e.seconds} seconds...", ALERT_COLOR, ALERT_COLOR))
                await asyncio.sleep(e.seconds)
            except RPCError as e:
                logger.error(f"RPC error: {e}")
                print(gradient_text(f"RPC error: {e}. Check your connection and try again.", ALERT_COLOR, ALERT_COLOR))
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(gradient_text(f"Unexpected error: {e}", ALERT_COLOR, ALERT_COLOR))
            await asyncio.sleep(5)

# ------------------------------------------------------------------------------
# Profile management (load/save/edit)
# ------------------------------------------------------------------------------
def load_profiles():
    try:
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_profile(profile_name, config):
    profiles = load_profiles()
    profiles[profile_name] = config
    with open(CONFIG_FILE, 'w') as file:
        json.dump(profiles, file, indent=4)

def edit_profile(profile_name):
    profiles = load_profiles()
    if profile_name not in profiles:
        print(gradient_text(f"Profile '{profile_name}' not found.", ALERT_COLOR, ALERT_COLOR))
        return
    config = profiles[profile_name]
    print(gradient_text(f"Editing profile: {profile_name}", MAIN_COLOR_START, MAIN_COLOR_END))
    config['source_chat_ids'] = input(gradient_text("Source chat IDs (comma separated): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['source_chat_ids'] = [int(chat_id.strip()) for chat_id in config['source_chat_ids']]
    config['destination_channel_ids'] = input(gradient_text("Destination chat IDs (comma separated): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['destination_channel_ids'] = [int(chat_id.strip()) for chat_id in config['destination_channel_ids']]
    config['keywords'] = input(gradient_text("Keywords for filtering (optional, comma separated): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['keywords'] = [kw.strip() for kw in config['keywords'] if kw.strip()]
    config['signature'] = input(gradient_text("Signature to append under each message: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    config['blacklist'] = input(gradient_text("Blacklisted words (comma separated, or leave empty): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['blacklist'] = [w.strip().lower() for w in config['blacklist'] if w.strip()]
    profiles[profile_name] = config
    save_profile(profile_name, config)
    print(gradient_text(f"Profile '{profile_name}' updated!", SUCCESS_COLOR, SUCCESS_COLOR, "✅"))

# ------------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------------
async def graceful_shutdown(credentials_saved):
    if credentials_saved:
        print(gradient_text("Your encrypted credentials will be kept for future use.", MAIN_COLOR_START, MAIN_COLOR_END, "🔒"))
    else:
        print(gradient_text("Cleaning up temporary data...", MAIN_COLOR_START, MAIN_COLOR_END, "🧹"))
    action = "KEEP" if credentials_saved else "DELETE"
    print(gradient_text(f"You have chosen to {action} your credentials on exit.", ALERT_COLOR, ALERT_COLOR, "⚠️"))
    confirm = input(gradient_text("Are you sure? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    if confirm.lower() == 'y':
        if not credentials_saved:
            try:
                os.remove(CREDENTIALS_FILE)
                os.remove('session_bot.session')
                os.remove('session_user.session')
                print(gradient_text("Credentials and session files removed.", SUCCESS_COLOR, SUCCESS_COLOR, "✅"))
            except:
                pass
        print(gradient_text("Soluify signing off. Goodbye!", SUCCESS_COLOR, SUCCESS_COLOR, "🌙"))
    else:
        print(gradient_text("Operation cancelled. No changes made to credentials.", MAIN_COLOR_START, MAIN_COLOR_END))
    input(gradient_text("Press Enter to exit...", PROMPT_COLOR_START, PROMPT_COLOR_END))

async def display_help():
    help_text = """
    🌟 Telegram Copy & Paste Bot (Hybrid Version) - Help 🌟
    =======================================================
    
    1. List Chats:
       - Displays all chats/channels the USER account can see.
         Use this to obtain source chat IDs.
    
    2. Message Forwarding:
       - Forwards messages from source chats (read by the USER account)
         to destination chats (sent by the BOT account).
       - Unwanted footer text (starting with "📹 YouTube") is removed.
       - Optionally filter by keywords, append a signature, or skip blacklisted words.
    
    3. Edit Profile:
       - Modify existing configuration profiles.
    
    4. Help:
       - This help screen.
    
    5. Exit:
       - Safely close the program (with an option to delete credentials).
    
    Tips:
    - Ensure the USER account is added to the source groups/channels.
    - The BOT account should have rights to post in the destination chats.
    """
    print(gradient_text(help_text, MAIN_COLOR_START, MAIN_COLOR_END))
    input(gradient_text("Press Enter to return to the main menu...", PROMPT_COLOR_START, PROMPT_COLOR_END))

# ------------------------------------------------------------------------------
# Fancy matrix animation for startup
# ------------------------------------------------------------------------------
async def matrix_effect(logo_frames):
    logo_width = max(len(line) for line in logo_frames)
    logo_height = len(logo_frames)
    matrix = [[' ' for _ in range(logo_width)] for _ in range(logo_height)]
    matrix_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()_+-=[]{}|;:,.<>?"
    for frame in atqdm(range(50), desc="Loading", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}", ncols=75):
        print("\033[H\033[J", end="")  # Clear screen
        for col in range(logo_width):
            if random.random() < 0.2:
                matrix[0][col] = random.choice(matrix_chars)
            for row in range(logo_height - 1, 0, -1):
                matrix[row][col] = matrix[row-1][col]
            if matrix[0][col] != ' ':
                matrix[0][col] = random.choice(matrix_chars)
        for row in range(logo_height):
            line = ''
            for col in range(logo_width):
                if col < len(logo_frames[row]) and logo_frames[row][col] != ' ':
                    char = logo_frames[row][col]
                    color = (
                        int(147 + (0 - 147) * frame / 49),
                        int(112 + (191 - 112) * frame / 49),
                        int(219 + (255 - 219) * frame / 49)
                    )
                else:
                    char = matrix[row][col]
                    color = (147, 112, 219) if random.random() < 0.5 else (0, 191, 255)
                line += gradient_text(char, color, color)
            print(line)
        await asyncio.sleep(0.1)

# ------------------------------------------------------------------------------
# Helper function for new configuration
# ------------------------------------------------------------------------------
def get_new_config():
    source_chat_ids = input(gradient_text("Source chat IDs (comma separated): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    source_chat_ids = [int(chat_id.strip()) for chat_id in source_chat_ids]
    destination_channel_ids = input(gradient_text("Destination chat IDs (comma separated): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    destination_channel_ids = [int(chat_id.strip()) for chat_id in destination_channel_ids]
    keywords = input(gradient_text("Keywords for filtering (leave empty for all): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    keywords = [kw.strip() for kw in keywords if kw.strip()]
    signature = input(gradient_text("Signature to append under each message: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    blacklist = input(gradient_text("Blacklisted words (comma separated, or empty): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    blacklist = [w.strip().lower() for w in blacklist if w.strip()]
    save_choice = input(gradient_text("Save this config as a profile? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    if save_choice.lower() == 'y':
        profile_name = input(gradient_text("Name for this profile: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
        save_profile(profile_name, {
            'source_chat_ids': source_chat_ids,
            'destination_channel_ids': destination_channel_ids,
            'keywords': keywords,
            'signature': signature,
            'blacklist': blacklist
        })
    return source_chat_ids, destination_channel_ids, keywords, signature, blacklist

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
async def main():
    logo_frames = [
        "  _____  ___   _      __ __  ____  _____  __ __ ",
        " / ___/ /   \\ | T    |  T  Tl    j|     ||  T  T",
        "(   \\_ Y     Y| |    |  |  | |  T |   __j|  |  |",
        " \\__  T|  O  || l___ |  |  | |  | |  l_  |  ~  |",
        " /  \\ ||     ||     T|  :  | |  | |   _] l___, |",
        " \\    |l     !|     |l     | j  l |  T   |     !",
        "  \\___j \\___/ l_____j \\__,_j|____jl__j   l____/ "
    ]
    copypaste_art = [
        "   ___                          ___              _         ",
        "  / __\\  ___   _ __   _   _    / _ \\  __ _  ___ | |_   ___ ",
        " / /    / _ \\ | '_ \\ | | | |  / /_)/ / _` |/ __|| __| / _ \\",
        "/ /___ | (_) || |_) || |_| | / ___/ | (_| |\\__ \\| |_ |  __/",
        "\\____/  \\___/ | .__/  \\__, | \\/      \\__,_||___/ \\__| \\___|",
        "              |_|     |___/                                "
    ]
    combined_art = logo_frames + [""] + copypaste_art
    await matrix_effect(combined_art)
    print("\033[H\033[J", end="")  # Clear screen
    for line in combined_art:
        print(gradient_text(line, MAIN_COLOR_START, MAIN_COLOR_END))
    intro_text = gradient_text("""
Welcome to the Soluify Telegram Copy & Paste Bot (Hybrid Version)!
==================================================================
1. Log in with your Bot API credentials (with BOT token).
2. Choose whether to use a USER account as intermediary for reading messages.
3. Create (optional) profiles (combinations of source/destination + filters).
4. Sit back and let the bot forward messages!
""", MAIN_COLOR_START, MAIN_COLOR_END)
    print(intro_text)
    # Get bot credentials
    api_id, api_hash, bot_token = read_credentials()
    credentials_saved = False
    if not api_id or not api_hash or not bot_token:
        print(gradient_text("Let's get your Telegram Bot credentials!", MAIN_COLOR_START, MAIN_COLOR_END, "🚀"))
        credentials_saved, api_id, api_hash, bot_token = store_credentials()
    # Create the bot client (for sending messages)
    sender_client = TelegramClient('session_bot', int(api_id), api_hash)
    await sender_client.start(bot_token=bot_token)
    # Ask whether to use a user account for reading messages
    use_user = input(gradient_text("Do you want to use a USER account as intermediary for reading messages? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).strip().lower() == 'y'
    if use_user:
        user_api_id, user_api_hash, phone_number = get_user_credentials()
        reader_client = TelegramClient('session_user', int(user_api_id), user_api_hash)
        await reader_client.start(phone=phone_number)
    else:
        reader_client = sender_client
    # Initialize the forwarder with both clients
    forwarder = TelegramForwarder(reader_client, sender_client)
    while True:
        print(gradient_text("\nWhat would you like to do?", MAIN_COLOR_START, MAIN_COLOR_END, "🕵️"))
        print(gradient_text("1. List Chats", PROMPT_COLOR_START, PROMPT_COLOR_END, "📋"))
        print(gradient_text("2. Set Up Message Forwarding", PROMPT_COLOR_START, PROMPT_COLOR_END, "⚙️"))
        print(gradient_text("3. Edit Profile", PROMPT_COLOR_START, PROMPT_COLOR_END, "✏️"))
        print(gradient_text("4. Help", PROMPT_COLOR_START, PROMPT_COLOR_END, "❓"))
        print(gradient_text("5. Exit", PROMPT_COLOR_START, PROMPT_COLOR_END, "👋"))
        choice = input(gradient_text("Choose (1-5): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
        try:
            if choice == "1":
                await animated_transition("Fetching chats...")
                await forwarder.list_chats()
            elif choice == "2":
                profiles = load_profiles()
                if profiles:
                    use_profile = input(gradient_text("Use a saved profile? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
                    if use_profile.lower() == 'y':
                        print(gradient_text("Available profiles:", MAIN_COLOR_START, MAIN_COLOR_END, "🎭"))
                        for idx, profile_name in enumerate(profiles):
                            print(gradient_text(f"{idx + 1}. {profile_name}", MAIN_COLOR_START, MAIN_COLOR_END))
                        profile_idx = int(input(gradient_text("Select profile number: ", PROMPT_COLOR_START, PROMPT_COLOR_END))) - 1
                        profile_name = list(profiles.keys())[profile_idx]
                        config = profiles[profile_name]
                        forwarder.blacklist = config.get('blacklist', [])
                        await animated_transition("Message forwarding started...")
                        await forwarder.forward_messages_to_channels(
                            source_chat_ids=config['source_chat_ids'],
                            destination_channel_ids=config['destination_channel_ids'],
                            keywords=config['keywords'],
                            signature=config['signature']
                        )
                    else:
                        s_ids, d_ids, kws, sig, blist = get_new_config()
                        forwarder.blacklist = blist
                        await animated_transition("Message forwarding started...")
                        await forwarder.forward_messages_to_channels(s_ids, d_ids, kws, sig)
                else:
                    s_ids, d_ids, kws, sig, blist = get_new_config()
                    forwarder.blacklist = blist
                    await animated_transition("Message forwarding started...")
                    await forwarder.forward_messages_to_channels(s_ids, d_ids, kws, sig)
            elif choice == "3":
                profiles = load_profiles()
                if profiles:
                    print(gradient_text("Available profiles:", MAIN_COLOR_START, MAIN_COLOR_END, "🎭"))
                    for idx, profile_name in enumerate(profiles):
                        print(gradient_text(f"{idx + 1}. {profile_name}", MAIN_COLOR_START, MAIN_COLOR_END))
                    profile_idx = int(input(gradient_text("Select profile number to edit: ", PROMPT_COLOR_START, PROMPT_COLOR_END))) - 1
                    profile_name = list(profiles.keys())[profile_idx]
                    edit_profile(profile_name)
                else:
                    print(gradient_text("No profiles found. Create one under 'Message Forwarding'.", ALERT_COLOR, ALERT_COLOR))
            elif choice == "4":
                await display_help()
            elif choice == "5":
                await graceful_shutdown(credentials_saved)
                break
            else:
                print(gradient_text("Invalid choice. Please try again.", ALERT_COLOR, ALERT_COLOR, "❌"))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(gradient_text(f"Unexpected error: {e}. Retrying after a short pause...", ALERT_COLOR, ALERT_COLOR))
            await asyncio.sleep(5)

# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
