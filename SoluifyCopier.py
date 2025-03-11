#!/usr/bin/env python3
# ==============================================================================
# Soluify  |  Your #1 IT Problem Solver  |  {telegram-copypaste-bot v2.0}
# ==============================================================================
#  __         _
# (_  _ |   .(_
# __)(_)||_||| \/
#              /
# © 2025 Soluify LLC
# ------------------------------------------------------------------------------
# Verbeterde versie voor gebruik met een Telegram-BOT account (d.m.v. bot_token).
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
import select
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError, ChatForwardsRestrictedError
from colorama import init, Fore, Style
from tqdm import tqdm
from tqdm.asyncio import tqdm as atqdm
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass

init(autoreset=True)

# ------------------------------------------------------------------------------
# Bestandsnamen en constants
# ------------------------------------------------------------------------------
CONFIG_FILE = 'telegramconfiguration.json'
CREDENTIALS_FILE = 'credentials.json'
LOG_FILE = 'soluify.log'
MAX_RETRIES = 3
RETRY_DELAY = 5

# ------------------------------------------------------------------------------
# Kleuren en gradients
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
# Kleurovergang in tekst
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
# Animatie functie
# ------------------------------------------------------------------------------
async def animated_transition(text, duration=0.5):
    emojis = ["✨", "🚀", "💫", "🌟", "💡", "🔮", "🎉"]
    for _ in range(int(duration * 10)):
        emoji = random.choice(emojis)
        print(f"\r{gradient_text(text, MAIN_COLOR_START, MAIN_COLOR_END, emoji)}", end="", flush=True)
        await asyncio.sleep(0.05)
    print()

# ------------------------------------------------------------------------------
# Functies voor encryptie/decryptie van credentials
# ------------------------------------------------------------------------------
def get_key(password):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'soluify_salt',  # In productie gebruik je een random salt
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
# Opslaan / lezen van credentials (API ID, API Hash, bot token)
# ------------------------------------------------------------------------------
def store_credentials():
    print(gradient_text("LET OP: Je gaat je API-gegevens voor Telegram Bot invoeren.", ALERT_COLOR, ALERT_COLOR, "🚨"))
    print(gradient_text("Houd deze gegevens veilig. Je bot-token is als een sleutel!", ALERT_COLOR, ALERT_COLOR))

    proceed = input(gradient_text("Wil je doorgaan? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    if proceed.lower() != 'y':
        print(gradient_text("Operatie geannuleerd. Script wordt afgesloten.", MAIN_COLOR_START, MAIN_COLOR_END))
        sys.exit(0)

    # Prompt for credentials
    api_id = getpass.getpass(gradient_text("Voer je API ID in: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    api_hash = getpass.getpass(gradient_text("Voer je API Hash in: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    bot_token = getpass.getpass(gradient_text("Voer je Bot Token in (bijv. 123456:ABC-...): ", PROMPT_COLOR_START, PROMPT_COLOR_END))

    save_choice = input(gradient_text("Wil je je gegevens opslaan voor toekomstig gebruik? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    print(gradient_text("Vanuit veiligheidsperspectief is opslaan niet altijd aangeraden.", ALERT_COLOR, ALERT_COLOR, "⚠️"))

    if save_choice.lower() == 'y':
        password = getpass.getpass(gradient_text("Kies een sterk wachtwoord om je gegevens te versleutelen: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
        credentials = {
            'api_id': api_id,
            'api_hash': api_hash,
            'bot_token': bot_token
        }
        encrypted_data = encrypt_data(credentials, password)
        with open(CREDENTIALS_FILE, 'wb') as f:
            f.write(encrypted_data)
        print(gradient_text("Gegevens opgeslagen en versleuteld.", SUCCESS_COLOR, SUCCESS_COLOR, "🔐"))
    else:
        print(gradient_text("Gegevens worden niet permanent opgeslagen.", MAIN_COLOR_START, MAIN_COLOR_END))

    return save_choice.lower() == 'y', api_id, api_hash, bot_token

def read_credentials():
    if not os.path.exists(CREDENTIALS_FILE):
        return None, None, None

    password = getpass.getpass(gradient_text("Voer je wachtwoord in om de bot-gegevens te ontsleutelen: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    try:
        with open(CREDENTIALS_FILE, 'rb') as f:
            encrypted_data = f.read()
        credentials = decrypt_data(encrypted_data, password)
        print(gradient_text("Credentials gedecodeerd! Welkom terug!", SUCCESS_COLOR, SUCCESS_COLOR, "🎉"))
        return credentials['api_id'], credentials['api_hash'], credentials['bot_token']
    except Exception as e:
        logger.error(f"Error reading credentials: {e}")
        print(gradient_text(f"Fout bij het ontsleutelen: {e}", ALERT_COLOR, ALERT_COLOR))
        return None, None, None

# ------------------------------------------------------------------------------
# Class voor message forwarding
# ------------------------------------------------------------------------------
class TelegramForwarder:
    def __init__(self, client):
        self.client = client
        self.running = False
        self.blacklist = []

    async def connect_with_retry(self):
        for attempt in range(MAX_RETRIES):
            try:
                await self.client.connect()
                print(gradient_text("Succesvol verbonden met Telegram (Bot).", SUCCESS_COLOR, SUCCESS_COLOR, "✅"))
                return True
            except Exception as e:
                logger.error(f"Connectie poging {attempt + 1} mislukt: {e}")
                print(gradient_text(f"Connectie poging {attempt + 1} mislukt. Opnieuw proberen in {RETRY_DELAY} seconden...", ALERT_COLOR, ALERT_COLOR))
                await asyncio.sleep(RETRY_DELAY)
        print(gradient_text(f"Geen verbinding na {MAX_RETRIES} pogingen. Check je internet/Bot-token.", ALERT_COLOR, ALERT_COLOR))
        return False

    async def list_chats(self):
        """
        Geeft een lijst van de chats/kanalen waar de bot inzit.
        Let op: een bot ziet alleen groepen/kanalen waar hij aan toegevoegd is.
        """
        if not await self.connect_with_retry():
            return

        dialogs = await self.client.get_dialogs()
        filename = f"chats_of_bot.txt"
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

        print(gradient_text("Lijst van beschikbare chats is weggeschreven!", SUCCESS_COLOR, SUCCESS_COLOR, "🎉"))

    async def forward_messages_to_channels(self, source_chat_ids, destination_channel_ids, keywords, signature):
        """
        Forwardt berichten van de source chats naar de destination kanalen/groepen.
        - keywords: Optioneel filter (alleen berichten met deze woorden).
        - signature: Tekst die onder elk bericht wordt geplakt.
        - blacklist: Woorden die niet in de tekst mogen voorkomen (anders skip).
        """
        if not await self.connect_with_retry():
            return

        self.running = True
        # We halen alvast de laatste message ID op, zodat we niet alles opnieuw doorsturen.
        last_message_ids = {}
        for chat_id in source_chat_ids:
            msgs = await self.client.get_messages(chat_id, limit=1)
            last_message_ids[chat_id] = msgs[0].id if msgs else 0

        while self.running:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(gradient_text(f"[{timestamp}] Bot checkt nieuwe berichten...", MAIN_COLOR_START, MAIN_COLOR_END, "👀"))
            print(gradient_text("Typ 'exit' om het doorsturen te stoppen en terug te keren naar het hoofdmenu.", MAIN_COLOR_START, MAIN_COLOR_END))

            # Check of de gebruiker 'exit' heeft getypt (in de console)
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = input().strip()
                if line.lower() == 'exit':
                    print(gradient_text("Beëindigen van message forwarding...", MAIN_COLOR_START, MAIN_COLOR_END))
                    self.running = False
                    break

            try:
                for chat_id in source_chat_ids:
                    messages = await self.client.get_messages(chat_id, min_id=last_message_ids[chat_id], limit=None)

                    for message in reversed(messages):
                        should_forward = False
                        # Als er keywords zijn opgegeven, checken we of minimaal één van deze woorden in de tekst staat
                        if keywords:
                            if message.text and any(keyword.lower() in message.text.lower() for keyword in keywords):
                                should_forward = True
                        else:
                            should_forward = True

                        # Check de blacklist
                        if message.text and any(bad.lower() in message.text.lower() for bad in self.blacklist):
                            should_forward = False

                        if should_forward:
                            if message.text:
                                # Tekstbericht
                                for dest_id in destination_channel_ids:
                                    await self.client.send_message(dest_id, message.text + f"\n\n**{signature}**")
                            if message.media:
                                # Mediabericht: downloaden en opnieuw versturen
                                media_path = await self.client.download_media(message.media)
                                for dest_id in destination_channel_ids:
                                    caption_text = f"{message.text}\n\n**{signature}**" if message.text else f"**{signature}**"
                                    await self.client.send_file(dest_id, media_path, caption=caption_text)

                            print(gradient_text(f"[{timestamp}] Bericht doorgestuurd!", SUCCESS_COLOR, SUCCESS_COLOR, "✅"))
                            last_message_ids[chat_id] = max(last_message_ids[chat_id], message.id)

            except FloodWaitError as e:
                logger.error(f"Flood wait error: {e}. Wachten {e.seconds} seconden.")
                print(gradient_text(f"Flood wait error: {e}. Even {e.seconds} seconden pauze...", ALERT_COLOR, ALERT_COLOR))
                await asyncio.sleep(e.seconds)
            except RPCError as e:
                logger.error(f"RPC error: {e}")
                print(gradient_text(f"RPC error: {e}. Check je verbinding en probeer het opnieuw.", ALERT_COLOR, ALERT_COLOR))
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(gradient_text(f"Onverwachte fout: {e}", ALERT_COLOR, ALERT_COLOR))

            await asyncio.sleep(5)

# ------------------------------------------------------------------------------
# Profiel-management (opslaan / laden)
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
        print(gradient_text(f"Profiel '{profile_name}' niet gevonden.", ALERT_COLOR, ALERT_COLOR))
        return

    config = profiles[profile_name]
    print(gradient_text(f"Profiel bewerken: {profile_name}", MAIN_COLOR_START, MAIN_COLOR_END))

    config['source_chat_ids'] = input(gradient_text("Bron-chat ID's (komma-gescheiden): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['source_chat_ids'] = [int(chat_id.strip()) for chat_id in config['source_chat_ids']]

    config['destination_channel_ids'] = input(gradient_text("Doel-chat ID's (komma-gescheiden): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['destination_channel_ids'] = [int(chat_id.strip()) for chat_id in config['destination_channel_ids']]

    config['keywords'] = input(gradient_text("Keywords om te filteren (optioneel, komma-gescheiden): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['keywords'] = [kw.strip() for kw in config['keywords'] if kw.strip()]

    config['signature'] = input(gradient_text("Handtekening voor onder elk bericht: ", PROMPT_COLOR_START, PROMPT_COLOR_END))

    config['blacklist'] = input(gradient_text("Blacklisted woorden (komma-gescheiden, of leeg): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    config['blacklist'] = [w.strip().lower() for w in config['blacklist'] if w.strip()]

    profiles[profile_name] = config
    save_profile(profile_name, config)
    print(gradient_text(f"Profiel '{profile_name}' is aangepast!", SUCCESS_COLOR, SUCCESS_COLOR, "✅"))

# ------------------------------------------------------------------------------
# Hulpfuncties
# ------------------------------------------------------------------------------
async def graceful_shutdown(credentials_saved):
    if credentials_saved:
        print(gradient_text("Je versleutelde inloggegevens blijven bewaard voor de volgende keer.", MAIN_COLOR_START, MAIN_COLOR_END, "🔒"))
    else:
        print(gradient_text("Gekoppelde data wordt opgeruimd...", MAIN_COLOR_START, MAIN_COLOR_END, "🧹"))

    action = "BEHOUDEN" if credentials_saved else "VERWIJDEREN"
    print(gradient_text(f"Je hebt aangegeven de credentials te {action} bij afsluiten.", ALERT_COLOR, ALERT_COLOR, "⚠️"))
    confirm = input(gradient_text(f"Weet je het zeker? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))

    if confirm.lower() == 'y':
        if not credentials_saved:
            try:
                os.remove(CREDENTIALS_FILE)
                os.remove('session_bot.session')
                print(gradient_text("Credentials en sessiebestand verwijderd.", SUCCESS_COLOR, SUCCESS_COLOR, "✅"))
            except:
                pass
        print(gradient_text("Soluify sluit af. Tot ziens!", SUCCESS_COLOR, SUCCESS_COLOR, "🌙"))
    else:
        print(gradient_text("Operatie geannuleerd. Er is niets veranderd aan de credentials.", MAIN_COLOR_START, MAIN_COLOR_END))
        if credentials_saved:
            # Als we eerst ja hadden gekozen maar nu nee, laten we het credentials-bestand gewoon staan.
            print(gradient_text("Credentials blijven behouden.", SUCCESS_COLOR, SUCCESS_COLOR))

    input(gradient_text("Druk op Enter om af te sluiten...", PROMPT_COLOR_START, PROMPT_COLOR_END))

async def display_help():
    help_text = """
    🌟 Telegram Copy & Paste Bot (BOT-versie) - Help 🌟
    ==================================================

    1. Chats Lijst
       - Toont alle chats/kanalen waar deze bot in zit. 
         Let op: een bot kan alleen chats zien waar hij aan is toegevoegd.

    2. Messages Forwarding
       - Stel in vanaf welke bron-chat(s) naar welke doel-chat(s) berichten gekopieerd worden.
       - Kies optioneel keywords, signatures en blacklist.

    3. Profiel Bewerken
       - Pas bestaande config-profielen aan (handig als je meerdere sets bron/doel + filters hebt).

    4. Help
       - Dit scherm.

    5. Afsluiten
       - Sluit het programma veilig af (optie om credentials te verwijderen).

    Tip:
    - Voeg deze bot toe als beheerder in de groep(s) waar hij berichten moet lezen en/of posten.
    - Keywords filtert alleen berichten die die woorden bevatten.
    - Blacklist negeert berichten met bepaalde woorden.
    - Signature wordt onderaan elk bericht geplakt.

    Veel succes!
    """
    print(gradient_text(help_text, MAIN_COLOR_START, MAIN_COLOR_END))
    input(gradient_text("Druk op Enter om terug te keren naar het hoofdmenu...", PROMPT_COLOR_START, PROMPT_COLOR_END))

# ------------------------------------------------------------------------------
# Fancy matrix-animatie voor het starten
# ------------------------------------------------------------------------------
async def matrix_effect(logo_frames):
    logo_width = max(len(line) for line in logo_frames)
    logo_height = len(logo_frames)
    matrix = [[' ' for _ in range(logo_width)] for _ in range(logo_height)]
    matrix_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()_+-=[]{}|;:,.<>?"

    for frame in atqdm(range(50), desc="Loading", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}", ncols=75):
        print("\033[H\033[J", end="")  # Clear screen

        # Update matrix
        for col in range(logo_width):
            if random.random() < 0.2:  # Chance op nieuwe "drup"
                matrix[0][col] = random.choice(matrix_chars)

            for row in range(logo_height - 1, 0, -1):
                matrix[row][col] = matrix[row-1][col]

            if matrix[0][col] != ' ':
                matrix[0][col] = random.choice(matrix_chars)

        # Print matrix + logo overlay
        for row in range(logo_height):
            line = ''
            for col in range(logo_width):
                if col < len(logo_frames[row]) and logo_frames[row][col] != ' ':
                    char = logo_frames[row][col]
                    # Eenvoudige kleurovergang
                    color = (
                        int(147 + (0 - 147) * frame / 49),
                        int(112 + (191 - 112) * frame / 49),
                        int(219 + (255 - 219) * frame / 49)
                    )
                else:
                    char = matrix[row][col]
                    # Random bluish/purple tint
                    if random.random() < 0.5:
                        color = (147, 112, 219)
                    else:
                        color = (0, 191, 255)
                line += gradient_text(char, color, color)
            print(line)

        await asyncio.sleep(0.1)

# ------------------------------------------------------------------------------
# Hulpfunctie voor nieuwe config
# ------------------------------------------------------------------------------
def get_new_config():
    source_chat_ids = input(gradient_text("Bron-chat ID's (komma-gescheiden): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    source_chat_ids = [int(chat_id.strip()) for chat_id in source_chat_ids]
    destination_channel_ids = input(gradient_text("Doel-chat ID's (komma-gescheiden): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    destination_channel_ids = [int(chat_id.strip()) for chat_id in destination_channel_ids]
    keywords = input(gradient_text("Keywords om te filteren (leeg voor alles): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    keywords = [kw.strip() for kw in keywords if kw.strip()]
    signature = input(gradient_text("Handtekening voor onder elk bericht: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    blacklist = input(gradient_text("Blacklist woorden (komma-gescheiden, of leeg): ", PROMPT_COLOR_START, PROMPT_COLOR_END)).split(',')
    blacklist = [w.strip().lower() for w in blacklist if w.strip()]
    save_choice = input(gradient_text("Config als profiel opslaan? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
    if save_choice.lower() == 'y':
        profile_name = input(gradient_text("Naam voor dit profiel: ", PROMPT_COLOR_START, PROMPT_COLOR_END))
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

    # Matrix-effect bij het opstarten
    await matrix_effect(combined_art)

    # Schoon einde (laatste weergave)
    print("\033[H\033[J", end="")  # Clear screen
    for line in combined_art:
        print(gradient_text(line, MAIN_COLOR_START, MAIN_COLOR_END))

    intro_text = gradient_text("""
Welkom bij de Soluify Telegram Copy & Paste Bot (BOT-versie)!
===============================================================
1. Log in met je API-gegevens + BOT-token (veilig opgeslagen als je wilt).
2. Laat de bot joinen in groepen/kanalen die je wilt monitoren en forwarden.
3. Creëer (optioneel) meerdere profielen (combinaties van bron/doel + filters).
4. Klaar? Ga achterover leunen en laat onze bot berichten doorzetten!
""", MAIN_COLOR_START, MAIN_COLOR_END)
    print(intro_text)

    # Probeer bestaande credentials te laden
    api_id, api_hash, bot_token = read_credentials()
    credentials_saved = False

    if not api_id or not api_hash or not bot_token:
        print(gradient_text("We gaan je Telegram Bot-credentials opvragen!", MAIN_COLOR_START, MAIN_COLOR_END, "🚀"))
        credentials_saved, api_id, api_hash, bot_token = store_credentials()

    # Maak de Telethon client aan
    # Session wordt "session_bot" genoemd om het duidelijk te maken dat 't een bot is
    client = TelegramClient('session_bot', api_id, api_hash).start(bot_token=bot_token)
    forwarder = TelegramForwarder(client)

    while True:
        print(gradient_text("\nWat wil je doen?", MAIN_COLOR_START, MAIN_COLOR_END, "🕵️"))
        print(gradient_text("1. Chats Lijst", PROMPT_COLOR_START, PROMPT_COLOR_END, "📋"))
        print(gradient_text("2. Messages Forwarding (opzetten)", PROMPT_COLOR_START, PROMPT_COLOR_END, "⚙️"))
        print(gradient_text("3. Profiel Bewerken", PROMPT_COLOR_START, PROMPT_COLOR_END, "✏️"))
        print(gradient_text("4. Help", PROMPT_COLOR_START, PROMPT_COLOR_END, "❓"))
        print(gradient_text("5. Afsluiten", PROMPT_COLOR_START, PROMPT_COLOR_END, "👋"))

        choice = input(gradient_text("Kies (1-5): ", PROMPT_COLOR_START, PROMPT_COLOR_END))

        try:
            if choice == "1":
                await animated_transition("Chats worden opgehaald...")
                await forwarder.list_chats()

            elif choice == "2":
                profiles = load_profiles()
                if profiles:
                    use_profile = input(gradient_text("Wil je een bewaard profiel gebruiken? (y/n): ", PROMPT_COLOR_START, PROMPT_COLOR_END))
                    if use_profile.lower() == 'y':
                        print(gradient_text("Beschikbare profielen:", MAIN_COLOR_START, MAIN_COLOR_END, "🎭"))
                        for idx, profile_name in enumerate(profiles):
                            print(gradient_text(f"{idx + 1}. {profile_name}", MAIN_COLOR_START, MAIN_COLOR_END))
                        profile_idx = int(input(gradient_text("Kies profielenummer: ", PROMPT_COLOR_START, PROMPT_COLOR_END))) - 1
                        profile_name = list(profiles.keys())[profile_idx]
                        config = profiles[profile_name]
                        forwarder.blacklist = config.get('blacklist', [])
                        await animated_transition("Bericht-doorstuur gestart...")
                        await forwarder.forward_messages_to_channels(
                            source_chat_ids=config['source_chat_ids'],
                            destination_channel_ids=config['destination_channel_ids'],
                            keywords=config['keywords'],
                            signature=config['signature']
                        )
                    else:
                        s_ids, d_ids, kws, sig, blist = get_new_config()
                        forwarder.blacklist = blist
                        await animated_transition("Bericht-doorstuur gestart...")
                        await forwarder.forward_messages_to_channels(s_ids, d_ids, kws, sig)
                else:
                    s_ids, d_ids, kws, sig, blist = get_new_config()
                    forwarder.blacklist = blist
                    await animated_transition("Bericht-doorstuur gestart...")
                    await forwarder.forward_messages_to_channels(s_ids, d_ids, kws, sig)

            elif choice == "3":
                profiles = load_profiles()
                if profiles:
                    print(gradient_text("Beschikbare profielen:", MAIN_COLOR_START, MAIN_COLOR_END, "🎭"))
                    for idx, profile_name in enumerate(profiles):
                        print(gradient_text(f"{idx + 1}. {profile_name}", MAIN_COLOR_START, MAIN_COLOR_END))
                    profile_idx = int(input(gradient_text("Nummer van profiel dat je wilt bewerken: ", PROMPT_COLOR_START, PROMPT_COLOR_END))) - 1
                    profile_name = list(profiles.keys())[profile_idx]
                    edit_profile(profile_name)
                else:
                    print(gradient_text("Geen profielen gevonden. Maak eerst een nieuw profiel onder 'Messages Forwarding'.", ALERT_COLOR, ALERT_COLOR))

            elif choice == "4":
                await display_help()

            elif choice == "5":
                await graceful_shutdown(credentials_saved)
                break

            else:
                print(gradient_text("Ongeldige keuze. Probeer opnieuw.", ALERT_COLOR, ALERT_COLOR, "❌"))

        except Exception as e:
            logger.error(f"Onverwachte fout: {e}")
            print(gradient_text(f"Onverwachte fout: {e}. Even wachten en opnieuw proberen...", ALERT_COLOR, ALERT_COLOR))
            await asyncio.sleep(5)

# ------------------------------------------------------------------------------
# Startpunt
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
