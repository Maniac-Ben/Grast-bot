#!/bin/bash
echo "Downloading latest screp binary..."
python3 << 'EOF'
import urllib.request
import os
import stat

url = "https://github.com/icza/screp/releases/latest/download/screp_linux_amd64"
filename = "screp"

urllib.request.urlretrieve(url, filename)
# Make it executable
os.chmod(filename, os.stat(filename).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
print("✓ screp downloaded and ready")
EOF

