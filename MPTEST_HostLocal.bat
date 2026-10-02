@echo off
setlocal
rem ============================================================================
rem  Iron Breach -- MP test rung 2, instance A (the HOST) on this machine.
rem    Launches the game with -nosteam so it listens on plain UDP 7777 (with Steam live the
rem    host listens on a Steam P2P socket and MPTEST_JoinLocal cannot reach it).
rem    In the window: Press Any Button -> SELECT OPERATIVE -> DEPLOY. That IS hosting.
rem    Then double-click MPTEST_JoinLocal.bat for instance B.
rem    Log: Saved\Logs\IronBreach.log (this instance) -- see Docs/MP_TEST_DAY_CHECKLIST.md §3.
rem  Portable: keep this file NEXT TO IronBreach.uproject (same UE lookup as PLAY_IronBreach.bat).
rem ============================================================================
set "PROJ=%~dp0IronBreach.uproject"
if not exist "%PROJ%" ( echo Put MPTEST_HostLocal.bat in the folder that contains IronBreach.uproject. & pause & exit /b 1 )

set "UEDIR="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=Join-Path $env:ProgramData 'Epic\UnrealEngineLauncher\LauncherInstalled.dat'; if (Test-Path $f) { (Get-Content $f -Raw | ConvertFrom-Json).InstallationList | Where-Object { $_.AppName -eq 'UE_5.8' } | Select-Object -First 1 -ExpandProperty InstallLocation }"`) do set "UEDIR=%%D"
if not defined UEDIR if exist "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "D:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=D:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=A:\Unreal Engine\UE_5.8"
rem Manual override if none of the above finds it: remove 'rem' and set your UE_5.8 folder.
rem set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR ( echo Could not find Unreal Engine 5.8. Edit this file and set UEDIR to your UE_5.8 folder. & pause & exit /b 1 )
if not exist "%UEDIR%\Engine\Binaries\Win64\UnrealEditor.exe" ( echo UnrealEditor.exe not found under "%UEDIR%". & pause & exit /b 1 )

echo Starting instance A (HOST): -nosteam, 1280x720 at the top-left. Press Any Button -^> SELECT OPERATIVE -^> DEPLOY.
start "IronBreach HOST (rung 2)" "%UEDIR%\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" -game -windowed -ResX=1280 -ResY=720 -WinX=40 -WinY=40 -NoSplash -nosteam -log
