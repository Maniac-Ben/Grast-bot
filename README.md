# Grast Replay Bot 🏭✨🦠

A minimal Discord bot for **StarCraft: Brood War** replays. Drop a `.rep` file
in a channel and it replies with:

- player names and races
- APM / EAPM
- game duration
- map name
- winner / loser (hidden in a spoiler)

Parsing is done by [`screp`](https://github.com/icza/screp).

---

## Files

```
bot.py            # Discord events + replay handling
parser.py         # runs screp, extracts the stats
embed_builder.py  # builds the Discord reply
config.py         # token, paths, race emojis
build.sh          # downloads the screp binary (used by Railway)
Procfile          # worker process: build.sh then bot.py
requirements.txt
```

---

## Deploy on Railway

This uses Railway's default (Nixpacks/Railpack) builder — **no Dockerfile**.

1. Push these files to a GitHub repo (do **not** commit a token).
2. Railway → **New Project → Deploy from GitHub repo** → pick the repo.
3. **Settings → Build**: make sure the **Root Directory** is empty and there is
   **no Custom Build/Start Command** set. Railway reads the `Procfile`.
4. **Variables** tab → add `DISCORD_TOKEN` = your bot token.
5. Watch the deploy logs for:
   ```
   Downloading latest screp binary...
   screp v1.13.x ready
   Logged in as YourBot#1234 — listening for .rep uploads
   ```
6. Upload a `.rep` in Discord to test.

`build.sh` downloads `screp` automatically on each start, so you never commit
the binary.

---

## Run locally

1. `pip install -r requirements.txt`
2. Download `screp` for your OS from
   <https://github.com/icza/screp/releases> and put the binary
   (`screp` or `screp.exe`) next to `bot.py`.
3. Set your token: `set DISCORD_TOKEN=...` (Windows) /
   `export DISCORD_TOKEN=...` (macOS/Linux).
4. `python bot.py`

---

## Discord bot setup

1. <https://discord.com/developers/applications> → **New Application**.
2. **Bot** tab → enable **Message Content Intent**.
3. Copy the **Token** for `DISCORD_TOKEN`.
4. **OAuth2 → URL Generator**: scope `bot`; permissions **View Channels**,
   **Send Messages**, **Read Message History**, **Embed Links**. Open the URL
   and invite the bot.
