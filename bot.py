"""Minimal Brood War replay stats bot.

Drop a .rep file in any channel the bot can see and it replies with each
player's name, race, APM, EAPM, and win/loss. Parsing is done by screp."""

import discord

import config
from parser import parse_replay
from embed_builder import build_embed

intents = discord.Intents.default()
intents.message_content = True  # needed to read attachments
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    rep_files = [a for a in message.attachments if a.filename.lower().endswith(".rep")]
    if not rep_files:
        return

    for att in rep_files:
        # Unique temp name avoids collisions if two replays share a filename.
        tmp_path = config.TEMP_DIR / f"{att.id}_{att.filename}"
        try:
            await att.save(tmp_path)
            players = await parse_replay(tmp_path)
            await message.reply(embed=build_embed(att.filename, players))
        except FileNotFoundError:
            await message.reply(
                "❌ screp binary not found — make sure it downloaded (Railway) "
                "or is in the project root (local)."
            )
        except Exception as e:
            await message.reply(f"❌ Couldn't parse `{att.filename}`: `{e}`")
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    if config.DISCORD_TOKEN in (None, "", "YOUR_TOKEN_HERE"):
        raise SystemExit(
            "DISCORD_TOKEN is not set. Set the environment variable "
            "(or edit config.py) before running."
        )
    client.run(config.DISCORD_TOKEN)
