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
├── screp_setup.py    # Downloads/extracts the screp binary
├── requirements.txt
├── Dockerfile        # How Railway builds & runs the bot
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
2. Download the archive for your OS (the version number will differ):
   - Windows: `screp-vX.Y.Z-windows-amd64.zip`
   - Linux:   `screp-vX.Y.Z-linux-amd64.tar.gz`
3. Extract it. Inside you'll find `screp.exe` (Windows) or `screp` (Linux).
4. Put that binary in the project root (next to `bot.py`).

`config.py` picks the right filename automatically based on your OS.
(On Railway you skip this entirely — the Dockerfile downloads and extracts it for you at build time.)

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

The included **Dockerfile** handles everything: Railway builds it, the screp
binary is downloaded and baked into the image at build time, and the bot runs.
You do not install or configure screp yourself — and there's no start command
to set, because the Dockerfile defines it.

### Full Setup (4 parts)

```
═══════════════════════════════════════════════════════════════════════════
PART 1 — Create the Discord Bot
═══════════════════════════════════════════════════════════════════════════

1. Go to https://discord.com/developers/applications
   Click "New Application" → give it a name → "Create"

2. Open the "Bot" tab (left side)
   If you see "Add Bot", click it.

3. Under "Privileged Gateway Intents":
   Turn ON "Message Content Intent"
   Click "Save Changes"
   (Required — without it the bot can't see .rep attachments)

4. Click "Reset Token" → "Copy"
   Save this somewhere safe. Treat it like a password.
   Anyone with this token can control your bot.

5. Go to "OAuth2" tab → "URL Generator":
   - Scopes: check "bot"
   - Bot Permissions: check:
       • View Channels
       • Send Messages
       • Read Message History
       • Embed Links
   Copy the URL at the bottom

6. Paste that URL into your browser
   Choose your Discord server
   Click "Authorize"
   Your bot now appears in the server (offline until Part 4)


═══════════════════════════════════════════════════════════════════════════
PART 2 — Push the Project to GitHub
═══════════════════════════════════════════════════════════════════════════

1. Go to https://github.com/new
   Create a new repo named "bw-replay-bot"
   Leave it EMPTY (no README, no gitignore)
   Click "Create repository"

2. Open a terminal in the project folder (where bot.py is):

   $ git init
   $ git add .
   $ git commit -m "Minimal BW replay bot"
   $ git branch -M main
   $ git remote add origin https://github.com/YOUR_USERNAME/bw-replay-bot.git
   $ git push -u origin main

3. Refresh the GitHub page. Confirm:
   - All files are there
   - NO .env file visible
   - NO token anywhere in the code
   (.gitignore already prevents it, but double-check)


═══════════════════════════════════════════════════════════════════════════
PART 3 — Deploy on Railway
═══════════════════════════════════════════════════════════════════════════

1. Go to https://railway.app
   Sign in (GitHub sign-in is easiest)

2. Click "New Project" → "Deploy from GitHub repo"
   Authorize Railway if prompted
   Select "bw-replay-bot" repo
   Railway starts building automatically

3. Open the service (the live box)
   Click "Variables" tab → "New Variable"
   
   Name:  DISCORD_TOKEN
   Value: [paste the token from Part 1]
   
   Click "Add"
   Saving auto-triggers a redeploy

4. IMPORTANT — make sure Railway uses the Dockerfile:
   Go to "Settings" → "Build" and "Deploy" and check that:
     • Builder is "Dockerfile" (or left on the default auto-detect)
     • "Custom Build Command" is EMPTY
     • "Custom Start Command" is EMPTY
   If any of these are set (e.g. a leftover "bash build.sh && python bot.py"),
   clear them and save. The Dockerfile already defines how to build and run,
   so a custom command here will fight it and cause build errors.

5. Open "Deployments" tab → click the live deployment → "View Logs"
   
   During the BUILD you'll see:
   
   Downloading latest screp binary...
   ✓ screp v1.13.2 downloaded and ready
   
   Then once it starts:
   
   ✅ Logged in as YourBotName#1234 (instance ab12cd34)
   
   (The screp version and instance id will vary.)
   That means screp was baked in and the bot connected.
   You're done!


═══════════════════════════════════════════════════════════════════════════
PART 4 — Test It
═══════════════════════════════════════════════════════════════════════════

1. In Discord, go to a channel the bot can see

2. Upload any Brood War .rep file

3. Within 1–2 seconds, the bot replies with an embed showing:
   - Player names
   - Races (with emoji)
   - APM and EAPM
   - 🏆 next to the winner
   
   If it doesn't reply:
   - Make sure "Message Content Intent" is ON (Part 1, step 3)
   - Make sure the bot has "View Channels" & "Send Messages" in that channel
   - Check the Railway logs for an error


═══════════════════════════════════════════════════════════════════════════
KEY NOTES
═══════════════════════════════════════════════════════════════════════════

• You do NOT install screp on Railway.
  The Dockerfile bakes it into the image at build time.

• This is a "worker" — it connects OUT to Discord.
  No public URL or port needed. That's normal.

• Screp re-downloads on each restart.
  "Downloading latest screp binary..." in the logs is expected, not an error.

• Pushing to main on GitHub auto-redeploys on Railway.

• To update the bot code later:
  $ git add .
  $ git commit -m "fix: ..."
  $ git push
  Railway redeploys in ~30 seconds.
```

---

## Troubleshooting

| Problem                              | Fix                                                                 |
| ------------------------------------ | ------------------------------------------------------------------- |
| `screp binary not found`             | Locally: place `screp` in the project root. Railway: check the build logs for the screp download |
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
