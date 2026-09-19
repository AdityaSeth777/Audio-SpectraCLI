@echo off
REM Double-click launcher for Windows - opens a console and runs launch.py.
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    REM A previous run already set up a local venv with everything installed.
    set PYTHON=.venv\Scripts\python.exe
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% == 0 (
        set PYTHON=python
    ) else (
        where py >nul 2>nul
        if %ERRORLEVEL% == 0 (
            set PYTHON=py
        ) else (
            echo Python was not found on PATH. Install Python 3 from https://python.org and try again.
            pause
            exit /b 1
        )
    )
)

%PYTHON% launch.py
pause
