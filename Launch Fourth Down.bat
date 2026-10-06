@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 -m fourth_down %*
    goto done
)
where python >nul 2>&1
if %errorlevel% equ 0 (
    python -m fourth_down %*
    goto done
)
echo Python 3.10 or newer is required. Install Python, then run this launcher again.
echo No additional packages are needed for the local app.
:done
pause
