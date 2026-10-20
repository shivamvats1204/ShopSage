@echo off
cd /d "%~dp0"
echo ShopSage opens at http://127.0.0.1:8890
echo Keep this window open. Press Ctrl+C to stop.
python run.py %*
if errorlevel 1 (
  echo Install Python 3.10 or newer, or choose another port with --port 8891.
  pause
)
