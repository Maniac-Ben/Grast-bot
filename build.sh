#!/bin/bash
echo "Downloading latest screp binary..."
python3 << 'PYEOF'
import json, urllib.request, tarfile, io, os, stat, sys

API = "https://api.github.com/repos/icza/screp/releases/latest"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "bw-replay-bot"})
    return urllib.request.urlopen(req).read()

# 1) Find the linux-amd64 tarball in the latest release
release = json.loads(fetch(API))
asset_url = None
for a in release.get("assets", []):
    name = a.get("name", "")
    if "linux-amd64" in name and name.endswith(".tar.gz"):
        asset_url = a["browser_download_url"]
        break
if not asset_url:
    sys.exit("ERROR: no linux-amd64 screp asset in the latest release")

# 2) Download the tarball and extract the 'screp' binary from it
blob = fetch(asset_url)
tf = tarfile.open(fileobj=io.BytesIO(blob))
member = next((m for m in tf.getmembers()
               if m.isfile() and os.path.basename(m.name) == "screp"), None)
if member is None:  # fall back to first regular file in the archive
    member = next((m for m in tf.getmembers() if m.isfile()), None)
if member is None:
    sys.exit("ERROR: no binary found inside the screp tarball")

with tf.extractfile(member) as src, open("screp", "wb") as dst:
    dst.write(src.read())

# 3) Make it executable
os.chmod("screp", os.stat("screp").st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
print(f"\u2713 screp {release.get('tag_name', '')} downloaded and ready")
PYEOF
