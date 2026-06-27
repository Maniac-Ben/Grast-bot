"""Runs screp on a .rep file and extracts only the minimal stats:
player names, races, APM, EAPM, win/loss, game duration, and map name.

Built and verified against real Brood War replays. Winner is taken from
screp's computed WinnerTeam, falling back to the Leave-Game command (the
player who quit lost).
"""

import asyncio
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass

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
    duration: str   # e.g. "5:35"
    map_name: str


# Brood War runs at ~23.81 frames/sec on Fastest.
_FRAMES_PER_SECOND = 23.81

_RACE_MAP = {
    "T": "Terran", "Terran": "Terran",
    "P": "Protoss", "Protoss": "Protoss", "Toss": "Protoss",
    "Z": "Zerg", "Zerg": "Zerg",
    "R": "Random", "Random": "Random",
}


def _race_name(raw) -> str:
    if isinstance(raw, dict):
        raw = raw.get("Name") or raw.get("ShortName", "")
    if not raw:
        return "Unknown"
    return _RACE_MAP.get(str(raw).strip().title(), str(raw).strip().title())


def _clean_text(raw) -> str:
    """Strip Brood War colour-control bytes (0x00–0x1F) and tidy whitespace."""
    cleaned = "".join(ch for ch in str(raw) if ch >= " ")
    return " ".join(cleaned.split())


def _format_duration(frames) -> str:
    # Always MM:SS (a 72-minute game shows "72:34"), matching the in-game timer.
    try:
        total_seconds = int(int(frames) / _FRAMES_PER_SECOND)
    except (TypeError, ValueError, ZeroDivisionError):
        return "?"
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _player_type(p: dict) -> str:
    t = p.get("Type", "")
    if isinstance(t, dict):
        t = t.get("Name", "")
    return t or ""


def _determine_winner(players_raw: list, computed: dict) -> int:
    """Return the winning player's Team number, or 0 if undetermined."""
    winner_team = computed.get("WinnerTeam", 0) or 0
    if winner_team:
        return winner_team

    # Fallback: whoever issued "Leave Game" lost.
    left = set()
    for cmd in computed.get("LeaveGameCmds", []) or []:
        if isinstance(cmd, dict):
            left.add(cmd.get("PlayerID", -1))
    if left:
        remaining = [
            p for p in players_raw
            if isinstance(p, dict) and p.get("ID") not in left
            and _player_type(p) in ("Human", "Computer", "")
        ]
        if len(remaining) == 1:
            return remaining[0].get("Team", 0)
    return 0


def _parse_json(data: dict) -> ReplayResult:
    header = data.get("Header", {}) or {}
    computed = data.get("Computed", {}) or {}
    players_raw = header.get("Players", []) or []
    descs = computed.get("PlayerDescs", []) or []

    # Map APM/EAPM by PlayerID (verified to match Player.ID on real replays).
    desc_by_id = {d.get("PlayerID"): d for d in descs if isinstance(d, dict)}

    winner_team = _determine_winner(players_raw, computed)

    stats = []
    for i, p in enumerate(players_raw):
        if not isinstance(p, dict):
            continue
        ptype = _player_type(p)
        if ptype and ptype not in ("Human", "Computer", ""):
            continue  # skip observers / empty slots

        desc = desc_by_id.get(p.get("ID"), {})
        team = p.get("Team", 0)
        if not winner_team:
            outcome = "Unknown"
        elif team == winner_team:
            outcome = "Win"
        else:
            outcome = "Loss"

        stats.append(PlayerStats(
            name=_clean_text(p.get("Name", f"Player {i + 1}")) or f"Player {i + 1}",
            race=_race_name(p.get("Race", "")),
            apm=desc.get("APM", 0),
            eapm=desc.get("EAPM", 0),
            outcome=outcome,
        ))

    duration = _format_duration(header.get("Frames", 0))
    map_name = _clean_text(header.get("Map", "")) or "Unknown map"
    return ReplayResult(players=stats, duration=duration, map_name=map_name)


def _run_screp(rep_path) -> dict:
    if not config.SCREP_BINARY.exists():
        raise FileNotFoundError(
            f"screp binary not found at {config.SCREP_BINARY}."
        )
    if sys.platform != "win32":
        mode = os.stat(config.SCREP_BINARY).st_mode
        os.chmod(config.SCREP_BINARY, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    result = subprocess.run(
        [str(config.SCREP_BINARY), "-computed", str(rep_path)],
        capture_output=True,
        text=True,
        timeout=config.SCREP_TIMEOUT,
    )
    if result.returncode != 0:
        raise ValueError(f"screp error: {result.stderr.strip()}")
    return json.loads(result.stdout)


async def parse_replay(rep_path) -> ReplayResult:
    """Parse a .rep file off the event loop and return a ReplayResult."""
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, _run_screp, rep_path)
    return _parse_json(data)
