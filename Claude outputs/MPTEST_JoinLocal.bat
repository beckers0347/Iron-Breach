@echo off
setlocal
rem ============================================================================
rem  Iron Breach -- MP test rung 2, instance B (the CLIENT) on this machine.
rem    Connects straight to the host started by MPTEST_HostLocal.bat (127.0.0.1) with -nosteam.
rem    Start it AFTER the host has landed in its world (after DEPLOY), or the connect times out.
rem    Direct connect skips the title screen, so the operative you last used on the sheet is
rem    the one this client brings (same roster file as instance A -- both players will share
rem    a callsign on one machine; that is expected here and only here).
rem    To test the late-join path: quit this, let the host trigger the kaiju, run this again.
rem    Log: Saved\Logs\IronBreach_2.log (the host already holds IronBreach.log).
rem  Portable: keep this file NEXT TO IronBreach.uproject (same UE lookup as PLAY_IronBreach.bat).
rem ============================================================================
set "PROJ=%~dp0IronBreach.uproject"
if not exist "%PROJ%" ( echo Put MPTEST_JoinLocal.bat in the folder that contains IronBreach.uproject. & pause & exit /b 1 )
set "HOST=%~1"
if not defined HOST set "HOST=127.0.0.1"

set "UEDIR="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=Join-Path $env:ProgramData 'Epic\UnrealEngineLauncher\LauncherInstalled.dat'; if (Test-Path $f) { (Get-Content $f -Raw | ConvertFrom-Json).InstallationList | Where-Object { $_.AppName -eq 'UE_5.8' } | Select-Object -First 1 -ExpandProperty InstallLocation }"`) do set "UEDIR=%%D"
if not defined UEDIR if exist "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "D:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=D:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=A:\Unreal Engine\UE_5.8"
rem Manual override if none of the above finds it: remove 'rem' and set your UE_5.8 folder.
rem set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR ( echo Could not find Unreal Engine 5.8. Edit this file and set UEDIR to your UE_5.8 folder. & pause & exit /b 1 )
if not exist "%UEDIR%\Engine\Binaries\Win64\UnrealEditor.exe" ( echo UnrealEditor.exe not found under "%UEDIR%". & pause & exit /b 1 )

echo Starting instance B (CLIENT): connecting to %HOST% with -nosteam, 1280x720 at the top-right.
echo (Pass a LAN address as the first argument to join another machine's -nosteam host instead.)
start "IronBreach CLIENT (rung 2)" "%UEDIR%\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" %HOST% -game -windowed -ResX=1280 -ResY=720 -WinX=1340 -WinY=40 -NoSplash -nosteam -log
