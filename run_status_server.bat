@echo off
REM Start the CyTube Bot Web Status Server
REM Usage: run_status_server.bat [port]

set PORT=%1
if "%PORT%"=="" set PORT=5000

echo Starting CyTube Bot Status Server on port %PORT%...
echo.
echo Open your browser to: http://127.0.0.1:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.

python web\status_server.py --port %PORT%
