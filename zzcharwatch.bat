@echo off
setlocal
set "PROJ=D:\Unreal Games\IronBreach"
set "UE=A:\Unreal Engine\UE_5.8"
set "REQ=%PROJ%\Saved\zz_build_request.txt"
set "REP=%PROJ%\Saved\char_build_report.txt"
title IronBreach build watcher (Claude)
echo ================================================================
echo  IronBreach build watcher -- leave this window open.
echo  Claude drops Saved\zz_build_request.txt to trigger a build;
echo  results land in Saved\char_build_report.txt.
echo  Close this window whenever you want to stop.
echo ================================================================
:loop
if not exist "%REQ%" goto wait
set "MODE=build"
set /p MODE=<"%REQ%"
del "%REQ%" >nul 2>&1
set "M1=" & set "M2="
for /f "tokens=1,2" %%a in ("%MODE%") do (set "M1=%%a" & set "M2=%%b")
echo ==== %MODE% %date% %time% ==== > "%REP%"
echo [%time%] request: %MODE%
if /i "%M1%"=="audit" goto audit
if /i "%M1%"=="py" goto py
call "%UE%\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -project="%PROJ%\IronBreach.uproject" -WaitMutex >> "%REP%" 2>&1
set "BUILDEXIT=%ERRORLEVEL%"
echo ZZCHAR_BUILD_EXIT=%BUILDEXIT% >> "%REP%"
echo [%time%] build exit %BUILDEXIT%
if not "%BUILDEXIT%"=="0" goto finish
if /i not "%M1%"=="buildaudit" goto finish
:audit
"%UE%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "%PROJ%\IronBreach.uproject" -run=pythonscript -script="D:/Unreal Games/IronBreach/Scripts/ib_audit_character_flow.py" -stdout -FullStdOutLogOutput -unattended -nopause -nosplash >> "%REP%" 2>&1
echo ZZCHAR_AUDIT_EXIT=%ERRORLEVEL% >> "%REP%"
goto finish
:py
"%UE%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "%PROJ%\IronBreach.uproject" -run=pythonscript -script="D:/Unreal Games/IronBreach/Scripts/%M2%" -stdout -FullStdOutLogOutput -unattended -nopause -nosplash >> "%REP%" 2>&1
echo ZZCHAR_PY_EXIT=%ERRORLEVEL% >> "%REP%"
:finish
echo ZZCHAR_ALL_DONE >> "%REP%"
echo [%time%] done -- report written.
:wait
timeout /t 4 /nobreak >nul
goto loop
