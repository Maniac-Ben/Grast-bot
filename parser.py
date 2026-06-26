"""Runs screp and extracts only the minimal stats we care about:
name, race, APM, EAPM, and win/loss.

Brood War replays rarely carry a reliable winner flag, so — like the full
bot — the winner is inferred: whoever issued the "Leave Game" command lost.
That requires screp's command list, hence the `-cmds -computed` flags.
"""

import asyncio
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import config


@dataclass
class PlayerStats:
    name: str
    race: str
    apm: int
    eapm: int
    outcome: str  # "Win" | "Loss" | "Unknown"


@dataclass
class ReplayResult:
    players: list
    duration: str  # human-readable game length, e.g. "12:34"
    map_name: str  # the map the game was played on


# Brood War runs at ~23.81 frames/sec on Fastest (1 frame = 42 ms), which is
# the basis for the conventional "game length".
_FRAMES_PER_SECOND = 23.81


def _format_duration(frames) -> str:
    # Always MM:SS (a 72-minute game shows "72:34"), matching the in-game timer.
    try:
        total_seconds = int(int(frames) / _FRAMES_PER_SECOND)
    except (TypeError, ValueError, ZeroDivisionError):
        return "?"
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


_RACE_MAP = {
    "T": "Terran", "Terran": "Terran",
    "P": "Protoss", "Protoss": "Protoss", "Toss": "Protoss",
    "Z": "Zerg", "Zerg": "Zerg",
    "R": "Random", "Random": "Random",
}


def _race_name(raw) -> str:
    """Normalise screp's race value (dict, full name, or letter) to a word."""
    if isinstance(raw, dict):
        raw = raw.get("Name") or raw.get("ShortName", "")
    if not raw:
        return "Unknown"
    return _RACE_MAP.get(str(raw).strip().title(), str(raw).strip().title())


def _player_type(p: dict) -> str:
    t = p.get("Type", "")
    if isinstance(t, dict):
        t = t.get("Name", "")
    return t or ""


def _extract_cmds(data: dict) -> list:
    raw = data.get("Commands", {})
    if isinstance(raw, dict):
        return raw.get("Cmds", []) or []
    if isinstance(raw, list):
        return raw
    return []


def _determine_winner(players_raw: list, cmds: list) -> Optional[int]:
    """Index of the winning player in players_raw, or None if undetermined."""
    # 1) An explicit result field, if screp happens to provide one.
    for i, p in enumerate(players_raw):
        if not isinstance(p, dict):
            continue
        result = p.get("Result") or p.get("Win")
        if isinstance(result, dict):
            result = result.get("Name") or result.get("ID")
        if result in ("Win", "win", True, 1):
            return i

    # 2) Fallback: whoever issued "Leave Game" lost.
    if cmds:
        left = set()
        for cmd in cmds:
            if not isinstance(cmd, dict):
                continue
            ctype = cmd.get("Type", {})
            if isinstance(ctype, dict):
                ctype = ctype.get("Name", "")
            if ctype == "Leave Game":
                left.add(cmd.get("PlayerID", -1))

        remaining = [
            p.get("ID", i)
            for i, p in enumerate(players_raw)
            if isinstance(p, dict)
            and _player_type(p) in ("Human", "human", "h", "")
            and p.get("ID", i) not in left
        ]
        if len(remaining) == 1:
            for i, p in enumerate(players_raw):
                if isinstance(p, dict) and p.get("ID", i) == remaining[0]:
                    return i
    return None


def _parse_json(data: dict) -> "ReplayResult":
    header = data.get("Header", {}) or {}
    computed = data.get("Computed", {}) or {}
    players_raw = header.get("Players", []) or []
    descs = computed.get("PlayerDescs", []) or []
    cmds = _extract_cmds(data)

    winner_idx = _determine_winner(players_raw, cmds)

    stats = []
    for i, p in enumerate(players_raw):
        if not isinstance(p, dict):
            continue
        ptype = _player_type(p)
        # Keep humans/computers; skip observers and empty slots.
        if ptype and ptype not in ("Human", "human", "h", "Computer", "computer"):
            continue

        # APM/EAPM live in PlayerDescs, aligned positionally with players_raw
        # (this mirrors the proven full bot's indexing).
        desc = descs[i] if i < len(descs) and isinstance(descs[i], dict) else {}

        if winner_idx is None:
            outcome = "Unknown"
        elif i == winner_idx:
            outcome = "Win"
        else:
            outcome = "Loss"

        stats.append(PlayerStats(
            name=p.get("Name", f"Player {i + 1}"),
            race=_race_name(p.get("Race", "")),
            apm=desc.get("APM", 0),
            eapm=desc.get("EAPM", 0),
            outcome=outcome,
        ))

    duration = _format_duration(header.get("Frames", 0))

    # Map name lives in Header.Map; fall back to the map-data scenario name.
    raw_map = header.get("Map") or (data.get("MapData") or {}).get("Name") or ""
    # Drop control chars (e.g. trailing null bytes) and collapse whitespace.
    cleaned = "".join(ch for ch in str(raw_map) if ch >= " ")
    map_name = " ".join(cleaned.split()) or "Unknown map"

    return ReplayResult(players=stats, duration=duration, map_name=map_name)


def _run_screp(rep_path) -> dict:
    if not config.SCREP_BINARY.exists():
        raise FileNotFoundError(
            f"screp binary not found at {config.SCREP_BINARY}. On Railway, "
            "build.sh should download it; locally, place it next to bot.py."
        )
    # Make sure it's executable (Railway/Linux downloads can lose the bit).
    if sys.platform != "win32":
        mode = os.stat(config.SCREP_BINARY).st_mode
        os.chmod(config.SCREP_BINARY, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    result = subprocess.run(
        [str(config.SCREP_BINARY), "-cmds", "-computed", str(rep_path)],
        capture_output=True,
        text=True,
        timeout=config.SCREP_TIMEOUT,
    )
    if result.returncode != 0:
        raise ValueError(f"screp error: {result.stderr.strip()}")
    return json.loads(result.stdout)


async def parse_replay(rep_path) -> "ReplayResult":
    """Parse a .rep file off the event loop and return a ReplayResult."""
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, _run_screp, rep_path)
    return _parse_json(data)
