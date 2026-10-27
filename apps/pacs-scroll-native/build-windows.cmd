@echo off
setlocal
cd /d "%~dp0"
if not exist dist mkdir dist
cl /nologo /std:c++17 /EHsc /W4 /O2 /MT tests\engine_test.cpp /Fe:dist\engine-test.exe
if errorlevel 1 exit /b 1
dist\engine-test.exe
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /W4 /O2 /MT main.cpp /Fe:dist\PACSScroll.exe /link /SUBSYSTEM:WINDOWS user32.lib shell32.lib gdi32.lib gdiplus.lib
if errorlevel 1 exit /b 1
powershell -NoProfile -Command "(Get-FileHash dist/PACSScroll.exe -Algorithm SHA256).Hash.ToLower() + '  PACSScroll.exe' | Set-Content -Encoding ascii dist/SHA256SUMS.txt"
