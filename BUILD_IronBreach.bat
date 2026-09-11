@echo off
setlocal
rem ============================================================================
rem  Iron Breach -- compile the game code (run this after every git pull that touched Source/).
rem  Unreal does NOT rebuild on its own when source changes; stale Binaries = old menus, failed joins.
rem  CLOSE the Unreal editor and the game first (they lock the DLL). Portable like PLAY_IronBreach.bat.
rem ============================================================================
set "PROJ=%~dp0IronBreach.uproject"
if not exist "%PROJ%" ( echo Put BUILD_IronBreach.bat in the folder that contains IronBreach.uproject. & pause & exit /b 1 )
tasklist /FI "IMAGENAME eq UnrealEditor.exe" 2>nul | find /I "UnrealEditor.exe" >nul
if not errorlevel 1 ( echo Unreal is still running. Close the editor and the game, then run this again. & pause & exit /b 1 )

set "UEDIR="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=Join-Path $env:ProgramData 'Epic\UnrealEngineLauncher\LauncherInstalled.dat'; if (Test-Path $f) { (Get-Content $f -Raw | ConvertFrom-Json).InstallationList | Where-Object { $_.AppName -eq 'UE_5.8' } | Select-Object -First 1 -ExpandProperty InstallLocation }"`) do set "UEDIR=%%D"
if not defined UEDIR if exist "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "D:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=D:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR if exist "A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" set "UEDIR=A:\Unreal Engine\UE_5.8"
rem Manual override if none of the above finds it: remove 'rem' and set your UE_5.8 folder.
rem set "UEDIR=C:\Program Files\Epic Games\UE_5.8"
if not defined UEDIR ( echo Could not find Unreal Engine 5.8. Edit this file and set UEDIR to your UE_5.8 folder. & pause & exit /b 1 )

echo Building IronBreachEditor (Win64 Development) with %UEDIR% ...
echo This takes a few minutes the first time. Leave the window open.
call "%UEDIR%\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -project="%PROJ%" -WaitMutex
if errorlevel 1 ( echo. & echo BUILD FAILED -- scroll up for the first "error" line. & pause & exit /b 1 )
echo.
echo BUILD OK -- now double-click PLAY_IronBreach.bat.
pause
