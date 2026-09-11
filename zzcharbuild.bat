@echo off
set REP=D:\Unreal Games\IronBreach\Saved\char_build_report.txt
echo ==== CHARACTER FLOW BUILD %date% %time% ==== > "%REP%"
call "A:\Unreal Engine\UE_5.8\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -project="D:\Unreal Games\IronBreach\IronBreach.uproject" -WaitMutex >> "%REP%" 2>&1
set BUILDEXIT=%ERRORLEVEL%
echo ZZCHAR_BUILD_EXIT=%BUILDEXIT% >> "%REP%"
if not "%BUILDEXIT%"=="0" goto done
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -run=pythonscript -script="D:/Unreal Games/IronBreach/Scripts/ib_audit_character_flow.py" -stdout -FullStdOutLogOutput -unattended -nopause -nosplash >> "%REP%" 2>&1
echo ZZCHAR_AUDIT_EXIT=%ERRORLEVEL% >> "%REP%"
:done
echo ZZCHAR_ALL_DONE >> "%REP%"
