@echo off
REM Start a CyTube Bot
REM Usage: run_bot.bat <bot_script> <config_file>

if "%~1"=="" (
    echo Error: Bot script required
    echo.
    echo Usage: run_bot.bat ^<bot_script^> ^<config_file^>
    echo Example: run_bot.bat bots\echo\bot.py bots\echo\config.json
    echo.
    pause
    exit /b 1
)

if "%~2"=="" (
    echo Error: Config file required
    echo.
    echo Usage: run_bot.bat ^<bot_script^> ^<config_file^>
    echo Example: run_bot.bat bots\echo\bot.py bots\echo\config.json
    echo.
    pause
    exit /b 1
)

if not exist "%~1" (
    echo Error: Bot script not found: %~1
    echo.
    pause
    exit /b 1
)

if not exist "%~2" (
    echo Error: Config file not found: %~2
    echo.
    pause
    exit /b 1
)

echo Starting CyTube Bot: %~1
echo Config: %~2
echo.
echo Press Ctrl+C to stop the bot
echo.

python "%~1" "%~2"
