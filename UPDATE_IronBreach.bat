@echo off
setlocal EnableDelayedExpansion
title Iron Breach -- UPDATE (pull latest + game code)
set "ROOT=%~dp0"
set "PROJ=%ROOT%IronBreach.uproject"
set "PACK=%ROOT%_SyncPack"
rem The compiled code in _SyncPack was built from this commit (no C++ has changed since).
set "PREBUILT_COMMIT=57324df"

echo.
echo  ==========================================================
echo   IRON BREACH -- update this project to the latest build
echo  ==========================================================
echo.
if not exist "%PROJ%" (
  echo  This pack must be unzipped INTO your IronBreach project folder
  echo  ^(the one that contains IronBreach.uproject^). Then run it again.
  echo.
  pause
  exit /b 1
)
tasklist /FI "IMAGENAME eq UnrealEditor.exe" 2>nul | find /I "UnrealEditor.exe" >nul
if not errorlevel 1 (
  echo  Unreal is still running. Close the editor AND the game, then run this again.
  echo.
  pause
  exit /b 1
)
cd /d "%ROOT%"

rem ---------------------------------------------------------------- git ----
set "GIT="
for %%G in (git.exe) do if not "%%~$PATH:G"=="" set "GIT=%%~$PATH:G"
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set "GIT=C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if not defined GIT if exist "D:\Git\cmd\git.exe" set "GIT=D:\Git\cmd\git.exe"
if not defined GIT for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%~D\resources\app\git\cmd\git.exe" set "GIT=%%~D\resources\app\git\cmd\git.exe"

echo  [1/3] Pulling the latest from GitHub...
if not defined GIT (
  echo        git.exe was not found on this PC -- skipping the pull.
  echo        Pull with GitHub Desktop, then run this file again.
) else (
  "!GIT!" pull --no-rebase origin main
  if errorlevel 1 (
    echo.
    echo        PULL FAILED -- usually uncommitted local changes, a conflict, or Unreal still open
    echo        ^("unable to unlink" = a file is locked by the editor/game^).
    echo        Send Connor a screenshot of the lines above.
    echo.
    pause
    exit /b 1
  )
  echo        now at:
  "!GIT!" log -1 --oneline
)

rem ---------------------------------------------------------- game code ----
echo.
echo  [2/3] Game code ^(compiled C++^)...
set "UEDIR="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=Join-Path $env:ProgramData 'Epic\UnrealEngineLauncher\LauncherInstalled.dat'; if (Test-Path $f) { (Get-Content $f -Raw | ConvertFrom-Json).InstallationList | Where-Object { $_.AppName -eq 'UE_5.8' } | Select-Object -First 1 -ExpandProperty InstallLocation }"`) do set "UEDIR=%%D"
if not defined UEDIR if exist "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "D:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=D:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=A:\Unreal Engine\UE_5.8"
if not defined UEDIR (
  echo        Could not find Unreal Engine 5.8 on this PC. Edit this file and set UEDIR to your UE_5.8 folder.
  echo.
  pause
  exit /b 1
)
echo        engine: !UEDIR!

set "ENGID="
set "PACKID="
for /f "tokens=2 delims=:, " %%B in ('findstr /C:"BuildId" "!UEDIR!\Engine\Binaries\Win64\UnrealEditor.modules"') do set "ENGID=%%~B"
for /f "tokens=2 delims=:, " %%B in ('findstr /C:"BuildId" "%PACK%\Binaries\Win64\UnrealEditor.modules"') do set "PACKID=%%~B"

set "USE_PREBUILT=0"
if defined ENGID if "!ENGID!"=="!PACKID!" set "USE_PREBUILT=1"
if "!USE_PREBUILT!"=="1" if defined GIT (
  rem only reuse Connor's compiled code if the C++ on disk is the C++ it was built from
  "!GIT!" diff --quiet %PREBUILT_COMMIT% HEAD -- Source
  if errorlevel 1 set "USE_PREBUILT=0"
)

if "!USE_PREBUILT!"=="1" (
  echo        Your engine matches Connor's ^(build !ENGID!^) -- installing his compiled game code.
  if not exist "%ROOT%Binaries\Win64" mkdir "%ROOT%Binaries\Win64"
  copy /Y "%PACK%\Binaries\Win64\UnrealEditor-IronBreach.dll" "%ROOT%Binaries\Win64\" >nul
  copy /Y "%PACK%\Binaries\Win64\UnrealEditor.modules" "%ROOT%Binaries\Win64\" >nul
  copy /Y "%PACK%\Binaries\Win64\IronBreachEditor.target" "%ROOT%Binaries\Win64\" >nul
  del /Q "%ROOT%Binaries\Win64\UnrealEditor-IronBreach-*.dll" 2>nul
  del /Q "%ROOT%Binaries\Win64\UnrealEditor-IronBreach.pdb" 2>nul
  del /Q "%ROOT%Binaries\Win64\*.patch_*" 2>nul
  echo        done.
) else (
  echo        Compiling the game code on this PC ^(engine build !ENGID! vs pack !PACKID!, or the C++ differs^).
  echo        Needs Visual Studio 2022 with "Game development with C++". This takes a few minutes -- leave it open.
  call "!UEDIR!\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -project="%PROJ%" -WaitMutex
  if errorlevel 1 (
    echo.
    echo        BUILD FAILED -- scroll up to the first line that says "error" and send Connor a screenshot.
    echo.
    pause
    exit /b 1
  )
)

echo.
echo  [3/3] Up to date. Start Steam if it is not running, then double-click PLAY_IronBreach.bat.
echo.
pause
