@echo off
"A:\Unreal Engine\UE_5.8\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -project="D:\Unreal Games\IronBreach\IronBreach.uproject" -WaitMutex > "D:\Unreal Games\IronBreach\Saved\loot_build_report.txt" 2>&1 & echo ZZBUILD DONE >> "D:\Unreal Games\IronBreach\Saved\loot_build_report.txt"
