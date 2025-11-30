@echo off
REM Add Daily News Analyst Bot to Windows Startup
REM Run this script as Administrator

echo ========================================
echo   Adding Bot to Windows Startup
echo ========================================
echo.

REM Get the current directory
set "SCRIPT_DIR=%~dp0"
set "BAT_FILE=%SCRIPT_DIR%start_bot.bat"

REM Get the Startup folder path
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Create a shortcut in the Startup folder
echo Creating shortcut in Startup folder...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_FOLDER%\Daily News Analyst Bot.lnk'); $Shortcut.TargetPath = '%BAT_FILE%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'Daily News Analyst Bot - Auto Start'; $Shortcut.Save()"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS!
    echo ========================================
    echo.
    echo The bot has been added to Windows Startup.
    echo It will automatically start when you log in.
    echo.
    echo Shortcut location:
    echo %STARTUP_FOLDER%\Daily News Analyst Bot.lnk
    echo.
) else (
    echo.
    echo ========================================
    echo FAILED!
    echo ========================================
    echo.
    echo Could not create startup shortcut.
    echo Please try running this script as Administrator.
    echo.
)

pause
