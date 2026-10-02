@echo off
setlocal EnableDelayedExpansion
title Iron Breach -- MAKE the sync pack for Shane
rem ============================================================================
rem  Iron Breach -- build the sync pack Shane unzips into his project (Connor's machine only).
rem  Run it AFTER a green build (BUILD_IronBreach.bat / the build watcher) and AFTER the push,
rem  with Unreal closed. It:
rem    1) refuses if Source\ has uncommitted C++ (the DLL would not match what Shane pulls)
rem    2) copies the compiled game code into _SyncPack\Binaries\Win64\
rem    3) stamps UPDATE_IronBreach.bat  PREBUILT_COMMIT=<current short commit>
rem    4) stamps README_FIRST.txt's first line with the commit + date
rem    5) zips BUILD/PLAY/UPDATE .bat + README_FIRST.txt + _SyncPack\  ->  IronBreach_SyncPack.zip
rem  Send IronBreach_SyncPack.zip to Shane; he unzips over his project and runs UPDATE_IronBreach.bat.
rem ============================================================================
set "ROOT=%~dp0"
cd /d "%ROOT%"
if not exist "%ROOT%IronBreach.uproject" ( echo Put MAKE_SyncPack.bat next to IronBreach.uproject. & pause & exit /b 1 )
set "FORCE="
if /i "%~1"=="--force" set "FORCE=1"

set "GIT="
for %%G in (git.exe) do if not "%%~$PATH:G"=="" set "GIT=%%~$PATH:G"
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set "GIT=C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "D:\Git\cmd\git.exe" set "GIT=D:\Git\cmd\git.exe"
if not defined GIT ( echo git.exe not found -- the pack needs the commit id. & pause & exit /b 1 )

set "COMMIT="
for /f "usebackq delims=" %%H in (`call "!GIT!" rev-parse --short HEAD`) do set "COMMIT=%%H"
if not defined COMMIT ( echo Could not read the current commit. & pause & exit /b 1 )

rem ---- 1) the DLL must be built from committed C++ ---------------------------------
set "DIRTY="
for /f "usebackq delims=" %%S in (`call "!GIT!" status --porcelain -- Source`) do set "DIRTY=1"
if defined DIRTY if not defined FORCE (
  echo.
  echo  Source\ has UNCOMMITTED changes. Shane pulls commits, not your working tree, so a DLL
  echo  built from this tree would not match his source. Commit + push first, then run this again.
  echo  ^(MAKE_SyncPack.bat --force to override on purpose.^)
  echo.
  "!GIT!" status --short -- Source
  pause
  exit /b 1
)
for /f "usebackq delims=" %%A in (`call "!GIT!" status -sb`) do ( set "LINE=%%A" & goto :gotstatus )
:gotstatus
echo !LINE! | find /I "ahead" >nul && (
  echo.
  echo  WARNING: this branch is AHEAD of origin/main -- push before sending the pack, or Shane's pull
  echo  will not contain the commit this DLL was built from. Continuing anyway.
  echo.
)

rem ---- 2) compiled game code --------------------------------------------------------------
set "BIN=%ROOT%Binaries\Win64"
if not exist "%BIN%\UnrealEditor-IronBreach.dll" ( echo No Binaries\Win64\UnrealEditor-IronBreach.dll -- build first. & pause & exit /b 1 )
for %%P in ("%BIN%\UnrealEditor-IronBreach-*.dll") do (
  echo  NOTE: hot-reload patch DLLs exist ^(%%~nxP^). The pack takes the base DLL; if you built with the
  echo  editor open, close it and rebuild so the base DLL is the newest code.
)
if not exist "%ROOT%_SyncPack\Binaries\Win64" mkdir "%ROOT%_SyncPack\Binaries\Win64"
copy /Y "%BIN%\UnrealEditor-IronBreach.dll" "%ROOT%_SyncPack\Binaries\Win64\" >nul || ( echo copy failed & pause & exit /b 1 )
copy /Y "%BIN%\UnrealEditor.modules"        "%ROOT%_SyncPack\Binaries\Win64\" >nul || ( echo copy failed & pause & exit /b 1 )
copy /Y "%BIN%\IronBreachEditor.target"     "%ROOT%_SyncPack\Binaries\Win64\" >nul || ( echo copy failed & pause & exit /b 1 )

rem ---- 3) + 4) stamps ---------------------------------------------------------------------
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd'"`) do set "TODAY=%%T"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p='%ROOT%UPDATE_IronBreach.bat'; $t=Get-Content $p -Raw; $t=$t -replace 'set \"PREBUILT_COMMIT=[0-9a-fA-F]+\"','set \"PREBUILT_COMMIT=%COMMIT%\"'; [IO.File]::WriteAllText($p,$t)" || ( echo could not stamp UPDATE_IronBreach.bat & pause & exit /b 1 )
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p='%ROOT%README_FIRST.txt'; $t=Get-Content $p -Raw; $t=$t -replace '^IRON BREACH -- sync pack from Connor \(build [0-9a-fA-F]+, [0-9-]+\)','IRON BREACH -- sync pack from Connor (build %COMMIT%, %TODAY%)'; [IO.File]::WriteAllText($p,$t)" || ( echo could not stamp README_FIRST.txt & pause & exit /b 1 )

rem ---- 5) zip -------------------------------------------------------------------------------
del /Q "%ROOT%IronBreach_SyncPack.zip" 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Compress-Archive -Path '%ROOT%BUILD_IronBreach.bat','%ROOT%PLAY_IronBreach.bat','%ROOT%UPDATE_IronBreach.bat','%ROOT%README_FIRST.txt','%ROOT%_SyncPack' -DestinationPath '%ROOT%IronBreach_SyncPack.zip' -CompressionLevel Optimal" || ( echo zip failed & pause & exit /b 1 )

echo.
echo  ==========================================================
echo   IronBreach_SyncPack.zip  --  build %COMMIT%, %TODAY%
for %%Z in ("%ROOT%IronBreach_SyncPack.zip") do echo   %%~zZ bytes
echo   Send it to Shane: unzip INTO the project folder, run UPDATE_IronBreach.bat with Unreal closed.
echo  ==========================================================
echo.
pause
