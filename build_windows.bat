@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   Fidel LKPR Updater - Windows build
echo ==========================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11+ from python.org.
  pause
  exit /b 1
)
py -m pip install --upgrade pip
py -m pip install --upgrade pyinstaller
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
py -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --add-data "assets;assets" ^
  --icon "assets\app_icon.ico" ^
  --name FidelLKPRUpdater updater.py
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)
echo.
echo Portable app created: dist\FidelLKPRUpdater.exe
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
  "%ISCC%" installer.iss
  if errorlevel 1 (
    echo Inno Setup compilation failed.
    pause
    exit /b 1
  )
  echo Installer created in installer\
) else (
  echo Inno Setup 6 not found. Portable EXE is ready; install Inno Setup 6 to build Setup.exe.
)
pause
