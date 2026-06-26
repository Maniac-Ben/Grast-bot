# BW Replay Stats Bot 🏭✨🦠

A minimal Discord bot that parses Brood War `.rep` replays and posts an embed
with each player's **name, race, APM, EAPM**, and **win/loss**.

Parsing is done by [`screp`](https://github.com/icza/screp) — no AI, no charts.

---

## Project Structure

```
bw_replay_bot/
├── bot.py            # Discord events & message handling
├── parser.py         # screp subprocess call + JSON → dataclasses
├── embed_builder.py  # discord.Embed construction
├── config.py         # Settings (token, paths, race emoji, …)
├── requirements.txt
├── build.sh          # Downloads the Linux screp binary (used on Railway)
├── procfile          # Worker process for Railway
└── temp/             # Auto-created; holds replays during processing
```

---

## Quick Start (local)

### 1. Install Python dependencies

Requires **Python 3.11+**.

```bash
pip install -r requirements.txt
```

### 2. Download the `screp` binary

`screp` is the Go tool that parses the replay files.

1. Go to <https://github.com/icza/screp/releases>
2. Download `screp_windows_amd64.exe` (Windows) or `screp_linux_amd64` (Linux)
3. Put it in the project root and rename it to `screp.exe` (Windows) or `screp` (Linux)

`config.py` picks the right filename automatically based on your OS.

### 3. Create a Discord bot

1. Go to <https://discord.com/developers/applications> → **New Application**
2. **Bot** tab → **Add Bot** → enable **Message Content Intent**
3. Copy the **Token**
4. **OAuth2 → URL Generator**: scopes `bot`, `applications.commands`;
   permissions `Send Messages`, `Read Message History`, `Embed Links`,
   `Read Messages/View Channels`
5. Open the generated URL to invite the bot to your server

### 4. Set your token

Windows:

```bash
set DISCORD_TOKEN=your-token-here
```

macOS / Linux:

```bash
export DISCORD_TOKEN=your-token-here
```

(Or edit `DISCORD_TOKEN` in `config.py` directly — fine for testing, not for
anything you'll push to GitHub.)

### 5. Run

```bash
python bot.py
```

Now upload any `.rep` file in a channel the bot can see — no commands needed.

---

## Deploy to Railway

The `build.sh` + `procfile` handle screp for you: on Railway, `build.sh`
downloads the Linux `screp` binary at startup, so you don't commit or configure
anything binary-related.

1. **Push to GitHub.** Make sure `.env` / your token is *not* committed
   (`.gitignore` already excludes `.env`). The token goes in Railway instead.
2. **Railway → New Project → Deploy from GitHub repo**, pick this repo.
3. **Variables tab:** add `DISCORD_TOKEN` = your bot token.
4. **Start command:** Railway should pick up the `procfile`. If it doesn't,
   set the start command manually to:

   ```
   bash build.sh && python bot.py
   ```

5. **Deployments → View Logs** and look for `✅ Logged in as ...`.

This bot is a worker — it connects out to Discord and needs no public URL or
port. Pushing to `main` redeploys automatically.

---

## Troubleshooting

| Problem                              | Fix                                                                 |
| ------------------------------------ | ------------------------------------------------------------------- |
| `screp binary not found`             | Download `screp` into the project root (local), or check `build.sh` ran (Railway) |
| `Improper token` / `401 Unauthorized`| `DISCORD_TOKEN` is missing or wrong                                  |
| `PrivilegedIntentsRequired`          | Enable **Message Content Intent** in the Discord dev portal         |
| Bot is online but ignores replays    | Re-invite it with View Channels / Read Message History / Send Messages |
| `Could not parse replay`             | File may be corrupt or from an unsupported version                  |

---

## Notes

- **EAPM** comes straight from screp's effective-actions algorithm.
- **Winner** is detected by screp ("largest remaining team wins"). When it
  can't tell, the bot shows `Unknown` and notes it in the footer.
- Observers and empty slots are filtered out.
- Multiple `.rep` files in one message are each parsed and answered separately.
