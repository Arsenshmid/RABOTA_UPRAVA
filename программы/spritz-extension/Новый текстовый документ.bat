@echo off
chcp 65001 >nul
setlocal

set "TARGET=%~dp0spritz-extension"

echo Создаю: "%TARGET%"
mkdir "%TARGET%" 2>nul

for %%F in (manifest.json popup.html popup.js popup.css content.js background.js) do (
    type nul > "%TARGET%\%%F"
)

echo.
echo Готово. Файлы здесь:
echo %TARGET%
echo.
explorer "%TARGET%"
pause