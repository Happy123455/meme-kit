#!/bin/zsh
# Double-click to preview and rate the camera effects. Keep this window open while reviewing; close it (or Ctrl+C) when done.
cd "${0:A:h}"
python3 tools/dashboard.py --camfx
