@echo off
setlocal enabledelayedexpansion
py -m PyInstaller ^
    --onefile ^
    --name=backtrack ^
    --windowed ^
    main.py
pause
