@echo off
REM Start the CyTube Bot
REM Usage: run_bot.bat <config_file>

if "%~1"=="" (
    echo Error: Config file required
    echo.
    echo Usage: run_bot.bat ^<config_file^>
    echo Example: run_bot.bat bots\echo\config.json
    echo.
    pause
    exit /b 1
)

if not exist "%~1" (
    echo Error: Config file not found: %~1
    echo.
    pause
    exit /b 1
)

echo Starting CyTube Bot with config: %~1
echo.
echo Press Ctrl+C to stop the bot
echo.

python -m lib.bot "%~1"
