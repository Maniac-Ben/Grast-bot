"""Builds the Discord embed from a parsed ReplayResult."""

import discord

import config


def build_embed(filename: str, result) -> discord.Embed:
    embed = discord.Embed(title=f"📊 {filename}", color=discord.Color.blue())

    players = result.players
    if not players:
        embed.description = "No players found in this replay."
        return embed

    # Map name and game length under the title.
    embed.description = f"🗺️ **{result.map_name}**  ·  ⏱️ **{result.duration}**"

    for p in players:
        emoji = config.RACE_EMOJI.get(p.race, config.RACE_EMOJI["Unknown"])
        # Emoji-only spoiler so every box is the same width and gives nothing
        # away. Reveal shows 🏆 (win), 💀 (loss), or ❔ (undetermined).
        marker = {"Win": "🏆", "Loss": "💀", "Unknown": "❔"}.get(p.outcome, "❔")
        outcome = f"||{marker}||"
        embed.add_field(
            name=f"{p.name}  {emoji} {p.race}",
            value=f"APM **{p.apm}**  ·  EAPM **{p.eapm}**  ·  {outcome}",
            inline=False,
        )

    if all(p.outcome == "Unknown" for p in players):
        embed.set_footer(text="Winner couldn't be determined from this replay.")

    return embed
