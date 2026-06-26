"""Ensures the screp binary is present.

This replaces the old build.sh: the download logic now lives in Python so it
works the same whether it runs during a Docker build, at bot startup, or
locally — no shell, no curl, no tar required.
"""

import io
import json
import os
import stat
import sys
import tarfile
import urllib.request

import config

_API = "https://api.github.com/repos/icza/screp/releases/latest"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "bw-replay-bot"})
    return urllib.request.urlopen(req).read()


def ensure_screp() -> None:
    """Download the screp binary if it isn't already next to the app.

    On Linux (e.g. Railway) this fetches the latest release automatically.
    On Windows it can't auto-install, so it asks the user to place screp.exe.
    """
    target = config.SCREP_BINARY
    if target.exists():
        return  # already have it

    if sys.platform == "win32":
        raise FileNotFoundError(
            f"{target} not found. Download screp for Windows from "
            "https://github.com/icza/screp/releases (the windows-amd64 .zip), "
            "extract screp.exe, and place it next to bot.py."
        )

    print("Downloading latest screp binary...")
    release = json.loads(_fetch(_API))

    asset_url = next(
        (a["browser_download_url"] for a in release.get("assets", [])
         if "linux-amd64" in a.get("name", "") and a["name"].endswith(".tar.gz")),
        None,
    )
    if not asset_url:
        raise RuntimeError("No linux-amd64 screp asset in the latest release.")

    blob = _fetch(asset_url)
    tf = tarfile.open(fileobj=io.BytesIO(blob))
    member = next(
        (m for m in tf.getmembers()
         if m.isfile() and os.path.basename(m.name) == "screp"),
        None,
    ) or next((m for m in tf.getmembers() if m.isfile()), None)
    if member is None:
        raise RuntimeError("No binary found inside the screp tarball.")

    with tf.extractfile(member) as src, open(target, "wb") as dst:
        dst.write(src.read())
    os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"\u2713 screp {release.get('tag_name', '')} downloaded and ready")


if __name__ == "__main__":
    ensure_screp()
