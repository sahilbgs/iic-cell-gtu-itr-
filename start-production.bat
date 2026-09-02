@echo off
cd /d "%~dp0"

echo [1/2] Starting IIC Production Server (Waitress)...
start "IIC Production Server" cmd /k ".\venv\Scripts\python.exe -m waitress --host=0.0.0.0 --port=5000 app:app"

echo [2/2] Waiting for server to initialize...
timeout /t 5 /nobreak >nul

echo Starting Cloudflare Tunnel (mywebsite -> iic-gtu-itr.aceglory.in)...
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel run mywebsite"