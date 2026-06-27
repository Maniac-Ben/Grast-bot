#!/bin/bash
# Downloads the latest screp binary into the project root.
# Uses Python (always present) instead of curl, and the real versioned
# tarball asset (the old screp_linux_amd64 URL no longer exists).
echo "Downloading latest screp binary..."
python3 << 'PYEOF'
import json, urllib.request, tarfile, io, os, stat, sys
API = "https://api.github.com/repos/icza/screp/releases/latest"
def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "grast-bot"})).read()
rel = json.loads(fetch(API))
url = next((a["browser_download_url"] for a in rel.get("assets", [])
           if "linux-amd64" in a.get("name", "") and a["name"].endswith(".tar.gz")), None)
if not url:
    sys.exit("No linux-amd64 screp asset found")
tf = tarfile.open(fileobj=io.BytesIO(fetch(url)))
m = next((x for x in tf.getmembers() if x.isfile() and os.path.basename(x.name) == "screp"), None)
with tf.extractfile(m) as s, open("screp", "wb") as d:
    d.write(s.read())
os.chmod("screp", os.stat("screp").st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
print(f"screp {rel.get('tag_name','')} ready")
PYEOF
