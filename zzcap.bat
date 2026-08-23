@echo off
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -run=pythonscript -script="D:/Unreal Games/IronBreach/Scripts/ib_capture_map.py" -stdout -FullStdOutLogOutput -unattended -nopause -nosplash > "D:\Unreal Games\IronBreach\Saved\map_capture_report.txt" 2>&1
echo ZZCAP DONE >> "D:\Unreal Games\IronBreach\Saved\map_capture_report.txt"
