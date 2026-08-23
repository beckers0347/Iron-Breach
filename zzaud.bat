@echo off
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -run=pythonscript -script="D:/Unreal Games/IronBreach/Scripts/ib_create_audio_assets.py" -stdout -FullStdOutLogOutput -unattended -nopause -nosplash > "D:\Unreal Games\IronBreach\Saved\audio_pass_report.txt" 2>&1
echo ZZAUD DONE >> "D:\Unreal Games\IronBreach\Saved\audio_pass_report.txt"
