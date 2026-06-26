import os
import sys
from pathlib import Path

# --- Discord ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_TOKEN_HERE")

# --- Paths ---
BASE_DIR = Path(__file__).parent
_screp_name = "screp.exe" if sys.platform == "win32" else "screp"
SCREP_BINARY = BASE_DIR / _screp_name   # Path to the screp binary
TEMP_DIR = BASE_DIR / "temp"            # Temp dir for downloaded replays
TEMP_DIR.mkdir(exist_ok=True)

# --- Replay parsing ---
SCREP_TIMEOUT = 15  # Seconds before the screp subprocess times out

# --- Races ---
RACE_EMOJI = {
    "Terran": "🏭",
    "Protoss": "✨",
    "Zerg": "🦠",
    "Random": "🎲",
    "Unknown": "❓",
}
