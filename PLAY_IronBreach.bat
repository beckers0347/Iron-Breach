@echo off
setlocal
rem ============================================================================
rem  Iron Breach -- launch the game.
rem    Title screen -> SELECT OPERATIVE -> DEPLOY lands you in your own hosted world.
rem    Steam must already be running (sessions + invites go through Steam).
rem    In the world: F = Squad tab -> INVITE a friend, or JOIN a friend who is IN IRON BREACH.
rem  Portable: keep this file NEXT TO IronBreach.uproject. It finds UE 5.8 through the
rem  Epic Games Launcher's install list, so it works on any machine with UE 5.8 installed.
rem ============================================================================
set "PROJ=%~dp0IronBreach.uproject"
if not exist "%PROJ%" ( echo Put PLAY_IronBreach.bat in the folder that contains IronBreach.uproject. & pause & exit /b 1 )

set "UEDIR="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=Join-Path $env:ProgramData 'Epic\UnrealEngineLauncher\LauncherInstalled.dat'; if (Test-Path $f) { (Get-Content $f -Raw | ConvertFrom-Json).InstallationList | Where-Object { $_.AppName -eq 'UE_5.8' } | Select-Object -First 1 -ExpandProperty InstallLocation }"`) do set "UEDIR=%%D"
if not defined UEDIR if exist "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "D:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=D:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=A:\Unreal Engine\UE_5.8"
rem Manual override if none of the above finds it: remove 'rem' and set your UE_5.8 folder.
rem set "UEDIR=C:\Program Files\Epic Games\UE_5.8"

if not defined UEDIR ( echo Could not find Unreal Engine 5.8. Edit this file and set UEDIR to your UE_5.8 folder. & pause & exit /b 1 )
if not exist "%UEDIR%\Engine\Binaries\Win64\UnrealEditor.exe" ( echo UnrealEditor.exe not found under "%UEDIR%". & pause & exit /b 1 )

start "" "%UEDIR%\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJ%" -game -windowed -ResX=1600 -ResY=900 -WinX=100 -WinY=60 -NoSplash
