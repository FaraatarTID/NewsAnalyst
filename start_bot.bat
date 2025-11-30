@echo off
REM Daily News Analyst - Local Bot Launcher
REM Double-click this file to start the bot

title Daily News Analyst Bot

echo ========================================
echo   Daily News Analyst - Local Bot
echo ========================================
echo.
echo Starting bot...
echo Press Ctrl+C to stop the bot
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the bot
python run_local_bot.py

REM If the bot exits, pause to show any error messages
echo.
echo ========================================
echo Bot stopped.
echo ========================================
pause
