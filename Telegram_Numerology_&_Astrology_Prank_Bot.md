# Telegram Numerology & Astrology Prank Bot

This project is a simple Python Telegram prank bot. It collects a user's name and partner's name, displays three fake loading messages, and returns the requested joke prediction. It does not use a database.

The Render version uses an HTTPS webhook served by Flask and Gunicorn. Render's free web-service tier is suitable for occasional use, but it can spin down after inactivity and may take a short time to wake up. Telegram sends updates to the public webhook URL through HTTPS, and the bot registers that URL automatically using Render's `RENDER_EXTERNAL_URL` variable.[1] [2] [3]

> **Use responsibly:** The result is clearly labeled as a prank. Use it only with people who are likely to understand the joke, and avoid relationship-related jokes with anyone who may take them seriously.

## Bot flow

| User action | Bot response |
| --- | --- |
| `/start` | Clears the current in-memory flow and shows the welcome message with a **Start Prediction** button. |
| **Start Prediction** | Asks for the user's name. |
| User enters a name | Asks for the partner's name. |
| User enters a partner's name | Shows fake astrology, numerology, and planetary-alignment messages, then reveals the prank. |
| **🔄 Try Again** | Clears the current in-memory data and starts again. |
| `/cancel` | Cancels the flow and clears the current in-memory data. |

## Project files

| File | Purpose |
| --- | --- |
| `bot.py` | Flask webhook service and Telegram conversation logic. |
| `bot_polling.py` | Original long-polling version for running locally when preferred. |
| `requirements.txt` | Python dependencies for the webhook service. |
| `render.yaml` | Free Render Web Service configuration. |
| `Dockerfile` | Optional Docker configuration for other hosts. |
| `.env.example` | Example token variable; it contains no real secret. |
| `.gitignore` | Keeps local secrets and Python cache files out of Git. |

## Deploy on free Render

### Important limitation

Render's free instance type is available for web services, but not for background workers. The webhook version therefore runs as a **Web Service**, not a paid always-on worker.[4] Free web services may spin down after inactivity and can restart at any time, so the first Telegram message after a quiet period may take longer than usual.[5]

### Step 1: Create or obtain the Telegram bot token

Open Telegram and message [@BotFather](https://t.me/BotFather). Send `/newbot`, follow the prompts, and copy the token. Telegram states that the token authenticates the bot and should be treated like a password.[6]

Never commit the token to GitHub or send it in this chat. You will enter it privately in Render as an environment variable named `BOT_TOKEN`.

### Step 2: Put the project in GitHub

Create a new GitHub repository, such as `telegram-prank-bot`, and upload the contents of this folder to the repository's root. The repository should contain at least:

```text
bot.py
bot_polling.py
requirements.txt
render.yaml
.gitignore
```

Do not upload a `.env` file containing your real token. The provided `.gitignore` already excludes `.env`.

### Step 3: Create the Render service

Open the [Render Dashboard](https://dashboard.render.com), select **New**, and choose **Web Service**. Connect the GitHub repository containing this project.[1]

You can configure the fields manually as follows, or use the included `render.yaml` as a Blueprint:

| Render setting | Value |
| --- | --- |
| Service type | Web Service |
| Runtime | Python |
| Plan | Free |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 0 bot:app` |
| Health check path | `/health` |
| Environment variable | Key: `BOT_TOKEN`; Value: your private BotFather token |

Render web services must bind to `0.0.0.0` and the port supplied by the `PORT` environment variable. The included start command does this.[2]

### Step 4: Add the private token

Before or during deployment, open the service's **Environment** page and add:

```text
Key: BOT_TOKEN
Value: your BotFather token
```

Save and deploy. Render documents environment variables as the recommended way to keep API keys and other credentials out of source code.[3]

The `render.yaml` file marks `BOT_TOKEN` with `sync: false`, so Render should prompt you for the value rather than storing a token in the repository. Never replace that with a hardcoded token.

### Step 5: Test the deployment

After Render shows the service as live, open the service URL in a browser. You should see:

```text
Telegram prank bot is running.
```

You can also open `/health`. A healthy response looks similar to:

```json
{"ok":true,"telegram_ready":true}
```

Then open your Telegram bot and send `/start`. The application registers its webhook automatically at:

```text
https://your-service-name.onrender.com/telegram-webhook
```

Telegram's `setWebhook` method sends JSON updates to an HTTPS URL and can include a secret header. This project verifies the `X-Telegram-Bot-Api-Secret-Token` header before accepting an update.[7]

## Local testing

For local testing of the webhook server itself, install the dependencies and set the token:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BOT_TOKEN="PASTE_YOUR_BOT_TOKEN_HERE"
python bot.py
```

This starts the Flask app on port `10000`, but Telegram cannot send webhooks to a local computer unless it has a public HTTPS URL. For the easiest local Telegram test, use the included polling version instead:

```bash
python bot_polling.py
```

The polling version requires only `BOT_TOKEN` and does not need a public URL. Stop either local process with `Ctrl+C`.

## Troubleshooting

If Render's logs say `BOT_TOKEN is not set`, add the environment variable in the Render service settings and redeploy. If the service returns `telegram_ready: false`, wait for the deployment to finish and refresh the health URL.

If the bot does not respond after deployment, inspect the Render logs for `Telegram webhook registered`. Confirm that the webhook URL uses the Render `onrender.com` HTTPS address and that the token belongs to the bot you are messaging. Telegram does not deliver updates through `getUpdates` while a webhook is configured, because the two update methods are mutually exclusive.[7]

If you previously ran the polling version with the same token, the webhook registration performed by the Render version replaces polling mode automatically. To return to polling mode locally, stop the Render service temporarily or remove the webhook with the Bot API before running `bot_polling.py`.

If the free Render service has been idle, its first response may be delayed while the service wakes. This is an expected free-tier limitation, not a Telegram conversation error.[5]

## References

[1]: https://render.com/docs/web-services "Render Web Services"

[2]: https://render.com/docs/web-services#port-binding "Render Web Services: Port binding"

[3]: https://render.com/docs/configure-environment-variables "Render Environment Variables and Secrets"

[4]: https://render.com/pricing "Render Pricing"

[5]: https://render.com/docs/free "Render Free Services"

[6]: https://core.telegram.org/bots/tutorial "Telegram: From BotFather to Hello World"

[7]: https://core.telegram.org/bots/api#setwebhook "Telegram Bot API: setWebhook"
