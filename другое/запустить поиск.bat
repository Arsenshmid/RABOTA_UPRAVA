@echo off
chcp 65001 >nul
py -m pip install requests
py "%~dp0poisk_nto_2gis.py"
pause
