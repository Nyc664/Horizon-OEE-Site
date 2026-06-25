@echo off
title Testar Horizon OEE Seguro
echo Testando backend local...
echo.
curl http://127.0.0.1:8000/api/health
echo.
pause
