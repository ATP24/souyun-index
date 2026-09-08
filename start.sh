#!/bin/bash
cd "$(dirname "$0")"
echo "=============================================="
echo " 搜韵网收录诗文出处循证系统 (souyun-index) v2.0.0"
echo "=============================================="
python3 -m pip install -r requirements.txt >/dev/null 2>&1
python3 src/server.py
