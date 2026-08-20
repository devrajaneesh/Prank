# Telegram Numerology & Astrology Prank Bot

This project is a small Telegram bot written in Python. It collects a user's name and their partner's name, displays three fake loading messages, and then returns the requested joke prediction. It stores data only in memory, so no database is required.

> **Use responsibly:** The result is explicitly labeled as a prank. Run it only with people who are likely to understand the joke, and avoid using relationship-related jokes with anyone who may take them seriously.

## What the bot does

| User action | Bot response |
| --- | --- |
| `/start` | Resets the current flow and shows the welcome message with a **Start Prediction** button. |
| **Start Prediction** | Asks for the user's name. |
| User enters a name | Asks for the partner's name. |
| User enters a partner's name | Shows fake astrology, numerology, and planetary-alignment loading messages, then reveals the prank. |
| **🔄 Try Again** | Clears the in-memory data and starts again from the welcome screen. |
| `/cancel` | Cancels the current flow and clears the in-memory data. |

The bot uses `python-telegram-bot` 22.8, whose current documentation provides the asynchronous `ApplicationBuilder` style used here.[2] The bot uses polling because it is the simplest beginner setup: the Python process stays running and receives Telegram updates through the library's polling runner.[3]

## Project files

| File | Purpose |
| --- | --- |
| `bot.py` | Complete bot implementation. |
| `requirements.txt` | Pinned Python dependency. |
| `Dockerfile` | Optional container deployment configuration. |
| `.env.example` | Example environment-variable file. |
| `.gitignore` | Prevents local secrets and Python cache files from being committed. |

## 1. Create the Telegram bot and token

Open Telegram and message [@BotFather](https://t.me/BotFather). Send `/newbot`, follow the prompts, and copy the token it provides. Telegram's official tutorial explains that the token authenticates the bot and should be treated like a password.[1]

Do not paste the token into `bot.py`, commit it to Git, or share it in screenshots. This project reads it from the `BOT_TOKEN` environment variable instead.

## 2. Run locally

Create a folder and place `bot.py`, `requirements.txt`, `.env.example`, and `.gitignore` in it. Then open a terminal in that folder.

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
export BOT_TOKEN="PASTE_YOUR_BOT_TOKEN_HERE"
python bot.py
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
python bot.py
```

When the terminal shows that the bot has started, open the bot's Telegram chat and send `/start`. Keep the terminal open while testing. Press `Ctrl+C` to stop it.

The token is not written to disk by these commands. If you prefer a persistent local environment file, copy `.env.example` to `.env`, install `python-dotenv`, and add `load_dotenv()` near the top of `bot.py`; the current version intentionally avoids that extra dependency to keep the beginner setup minimal.

## 3. Try the conversation

Send `/start` and press **Start Prediction**. Enter any name, enter a partner's name, and wait for the three fake loading messages. The final message includes the partner name in the requested joke and a **🔄 Try Again** button.

Sending `/start` at any time resets the conversation. Sending `/cancel` clears the current in-memory values and ends the conversation. Since there is no database, all active conversation data is lost if the Python process stops or restarts.

## 4. Deployment choices

The included code is a polling worker, so it needs a process that remains running while the bot is online. Choose the simplest option that fits your needs.

| Approach | Tradeoffs | Cost | Setup complexity |
| --- | --- | --- | --- |
| Run `python bot.py` on your own computer | Easiest to understand, but the bot goes offline when the computer is shut down or the process stops. | Usually no additional hosting cost. | Very low |
| Deploy the included Dockerfile to a long-running worker/container service | Keeps the bot online independently of your computer. You must add `BOT_TOKEN` as a secret and use a service that supports a continuously running worker. | Depends on the hosting provider and its plan. | Low to medium |

### Generic container deployment

Build the image from the project directory:

```bash
docker build -t telegram-prank-bot .
```

Run it by passing the token as an environment variable:

```bash
docker run --rm -e BOT_TOKEN="PASTE_YOUR_BOT_TOKEN_HERE" telegram-prank-bot
```

For a hosted deployment, create a long-running worker or container service, add a secret named `BOT_TOKEN`, and use either the included `Dockerfile` or the start command below:

```text
python bot.py
```

Do not put the token in a public repository, Dockerfile, or command history that other people can access. If a token is exposed, revoke it through @BotFather and create a replacement.

## Optional: configure the bot command menu

Telegram can show commands in a bot's command menu. In @BotFather, open `/mybots`, select your bot, choose **Edit Bot**, then **Edit Commands**, and enter:

```text
start - Start or restart the prank prediction
cancel - Cancel the current prediction
```

The command handlers are already implemented in `bot.py`; this step only improves the Telegram user interface.

## Troubleshooting

If the program exits with `BOT_TOKEN is not set`, set the environment variable in the same terminal session that runs `python bot.py`. If the bot does not respond, confirm that the process is still running, that you opened the correct bot chat, and that the token belongs to that bot.

If Telegram reports that the token is invalid, obtain a new token from @BotFather and replace the environment variable. Never send the token to anyone for debugging.

If a user sends `/start` while entering a name, the conversation is reset because `/start` is registered as an entry point with re-entry enabled. If a user sends `/cancel`, the bot clears the current in-memory values and ends that conversation.

## References

[1]: https://core.telegram.org/bots/tutorial "Telegram: From BotFather to Hello World"

[2]: https://docs.python-telegram-bot.org/en/v22.8/ "python-telegram-bot v22.8 documentation"

[3]: https://docs.python-telegram-bot.org/en/v22.8/telegram.ext.application.html#telegram.ext.Application.run_polling "python-telegram-bot v22.8: Application.run_polling"
