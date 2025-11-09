@echo off
REM CyTube Bot Daemon Controller for Windows
REM Usage: cytube_daemon.bat {start|stop|restart|status|foreground} [config.json]

setlocal

set ACTION=%1
set CONFIG=%2

if "%ACTION%"=="" (
    echo Usage: cytube_daemon.bat {start^|stop^|restart^|status^|foreground} [config.json]
    exit /b 1
)

if "%CONFIG%"=="" (
    set CONFIG=config.json
)

python cytube_daemon.py %ACTION% %CONFIG%

endlocal
