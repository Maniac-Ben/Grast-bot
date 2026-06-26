"""Builds the Discord embed from a parsed ReplayResult."""

import discord

import config


def build_embed(filename: str, result) -> discord.Embed:
    embed = discord.Embed(title=f"📊 {filename}", color=discord.Color.blue())

    players = result.players
    if not players:
        embed.description = "No players found in this replay."
        return embed

    # Map and game length shown under the title.
    embed.description = f"🗺️ **{result.map_name}**  ·  ⏱️ **{result.duration}**"

    for p in players:
        emoji = config.RACE_EMOJI.get(p.race, config.RACE_EMOJI["Unknown"])
        trophy = "🏆 " if p.outcome == "Win" else ""
        # Hide winner/loser in a spoiler tag (Discord's ||text|| syntax)
        outcome_spoiler = f"||{trophy}{p.outcome}||"
        embed.add_field(
            name=f"{p.name}  {emoji} {p.race}",
            value=f"APM **{p.apm}**  ·  EAPM **{p.eapm}**  ·  {outcome_spoiler}",
            inline=False,
        )

    if all(p.outcome == "Unknown" for p in players):
        embed.set_footer(text="Winner couldn't be determined from this replay.")

    return embed
