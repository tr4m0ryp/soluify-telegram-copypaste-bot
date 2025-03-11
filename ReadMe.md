# Telegram Copy & Paste Bot (Bot Version)

This project is a **Telegram bot** that can forward messages from one or more source chats to one or more destination chats. It supports **keywords** (for filtering), **blacklisting** (to skip messages containing certain words), and **signatures** (to append a line at the end of the forwarded message).

## 1. Requirements

1. **Python 3.7+**  
   Make sure you have Python 3.7 or newer installed on your system.
2. **Telegram API credentials**  
   - **API ID** and **API Hash** from [my.telegram.org](https://my.telegram.org)  
   - **Bot Token** from [@BotFather](https://t.me/BotFather) on Telegram.

## 2. Installation

1. **Clone or download** this repository (make sure you have the main script, e.g. `SoluifyCopierBot.py`).  
2. Install required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   The main dependencies are:
   - [Telethon](https://pypi.org/project/Telethon/) (for Telegram interactions)
   - [tqdm](https://pypi.org/project/tqdm/) (for progress bars/animations)
   - [cryptography](https://pypi.org/project/cryptography/) (for encrypting credentials)
   - [colorama](https://pypi.org/project/colorama/) (for colored terminal text)

## 3. Create Your Bot via BotFather

1. In Telegram, **start a chat** with [@BotFather](https://t.me/BotFather).
2. Send the command `/newbot`.
3. Choose a **name** and then a **username** for your bot (the username must end in `bot`).
4. **Copy** the Bot Token that BotFather gives you (something like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).

## 4. Prepare API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)  
2. Sign in with your **Telegram account**.  
3. Go to **API Development Tools** and create a new app.  
4. Copy the **API ID** and **API Hash** that it generates for you.

## 5. Run the Script

### 5.1 Basic Usage

1. Open a terminal in the folder where `SoluifyCopierBot.py` is located.
2. Start the script:
   ```bash
   python SoluifyCopierBot.py
   ```
3. You will be prompted to provide:
   - **API ID**  
   - **API Hash**  
   - **Bot Token**  
   - Optionally, you can **encrypt and save** these credentials locally for future runs (in a file called `credentials.json`). If you choose “yes,” the script will ask for a **password** to encrypt the file.  

### 5.2 Menu Overview

Once the bot is launched, you’ll see a menu like:

```
What do you want to do?
1. Chats List
2. Messages Forwarding (setup)
3. Edit Profile
4. Help
5. Exit
```

- **(1) Chats List**  
  Lists all chats/channels in which your bot is currently a member. It will print out **Chat ID** and **Title** for each chat.  
  - Note: A bot can only see chats you explicitly **invite** it to.  

- **(2) Messages Forwarding (setup)**  
  You can **create** or **use** an existing “profile” that tells the bot:
  1. **Source chat IDs**: Where to read messages from (the ID is typically a negative integer for groups or channels, e.g. `-1001234567890`).  
  2. **Destination chat IDs**: Where to forward those messages to.  
  3. **Keywords** (optional): If provided, only messages containing at least one keyword will be forwarded.  
  4. **Signature**: A small text appended to the message (e.g., “Forwarded by MyBot”).  
  5. **Blacklist**: Words that, if found in the message, cause it to be skipped.  

- **(3) Edit Profile**  
  If you have saved profiles (in `telegramconfiguration.json`), you can **edit** their source/destination IDs, keywords, etc.  

- **(4) Help**  
  Shows basic instructions.  

- **(5) Exit**  
  Safely stops the bot and optionally deletes any locally saved credentials if you don’t want them stored.

## 6. Making the Bot Work in Your Group

1. **Invite** the bot to your group or channel.  
2. **Promote** it to admin (or give it the rights to read and post messages). Otherwise, it may not see or forward any messages.  
3. Once the bot is in the group, you can use **chat IDs** shown by the “Chats List” option (menu item 1) as **source** or **destination** for forwarding.

## 7. Credentials Files Explanation

### 7.1 `credentials.json` (Encrypted)
- If you chose to save your credentials, an encrypted version of your **API ID**, **API Hash**, and **Bot Token** is stored here.  
- It will look like random gibberish (base64-encoded ciphertext).  
- When you re-run the script, it will ask you for the **same password** you used to encrypt it.

### 7.2 `telegramconfiguration.json`
- Stores your **profiles** (one or more sets of source chats, destination chats, signature, etc.).  
- An example structure:
  ```json
  {
    "MyFirstProfile": {
      "source_chat_ids": [-1001234567890],
      "destination_channel_ids": [-1009876543210],
      "keywords": ["urgent", "event"],
      "signature": "Forwarded by MyAwesomeBot",
      "blacklist": ["spam", "ignore"]
    }
  }
  ```

## 8. Deploying 24/7

Telegram doesn’t host your bot for you. You need to run this script on a server or machine that stays online. Some popular **free/low-cost** options:
- **Replit** (free tier, but might sleep after inactivity).
- **Railway.app** (free tier usage).
- **Fly.io** (free tier).
- **PythonAnywhere** (free tier, limited).
- A cheap **VPS** (Virtual Private Server) with your own environment (paid).

## 9. Troubleshooting

- **Bot cannot see chats**: Make sure the bot is **added** to the group/channel and has the correct permissions.  
- **FloodWaitError**: Telegram is rate-limiting the bot. The script will wait the required cooldown time automatically.  
- **RPCError**: Usually a temporary Telegram-side issue. Check your internet or try again later.  
- **Decryption fails**: Did you type the correct password to decrypt `credentials.json`?  
- **No messages forwarding**:  
  1. Check the group ID is correct.  
  2. Check that your bot is in the group(s).  
  3. If you have keywords, make sure your test messages actually match them.  
  4. If you have a blacklist, confirm you aren’t accidentally blacklisting everything.

---

### TR4M0RYP OUT!
