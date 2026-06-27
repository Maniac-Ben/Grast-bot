"""
bot.py — Grast replay bot entry-point.

Listens for .rep uploads in any channel the bot can read, parses them with
screp, and posts an embed with player names, races, APM/EAPM, the map,
the game duration, and the (spoilered) winner/loser.
"""

import logging
import uuid

import discord

from config import DISCORD_TOKEN, TEMP_DIR
from embed_builder import build_embed
from parser import parse_replay

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("grast-bot")

intents = discord.Intents.default()
intents.message_content = True   # Required to read attachments
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    log.info(f"Logged in as {client.user} — listening for .rep uploads")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    rep_files = [
        att for att in message.attachments
        if att.filename.lower().endswith(".rep")
    ]
    if not rep_files:
        return

    for attachment in rep_files:
        await _handle_replay(message, attachment)


async def _handle_replay(message: discord.Message, attachment: discord.Attachment) -> None:
    uid = uuid.uuid4().hex[:8]
    rep_path = TEMP_DIR / f"{uid}_{attachment.filename}"

    async with message.channel.typing():
        try:
            await attachment.save(rep_path)
            result = await parse_replay(rep_path)
            await message.reply(
                embed=build_embed(attachment.filename, result),
                mention_author=False,
            )
        except FileNotFoundError as exc:
            log.error(f"screp binary missing: {exc}")
            await message.reply(
                "⚠️ The `screp` binary was not found. Check the build logs.",
                mention_author=False,
            )
        except ValueError as exc:
            log.error(f"Parsing failed: {exc}")
            await message.reply(
                f"❌ Could not parse `{attachment.filename}` — is it a valid "
                "Brood War replay?",
                mention_author=False,
            )
        except Exception as exc:
            log.exception(f"Unexpected error: {exc}")
            await message.reply(
                "💥 Something went wrong processing that replay.",
                mention_author=False,
            )
        finally:
            try:
                rep_path.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    if DISCORD_TOKEN == "YOUR_TOKEN_HERE":
        log.error("No Discord token set! Set the DISCORD_TOKEN environment variable.")
        raise SystemExit(1)
    client.run(DISCORD_TOKEN, log_handler=None)
