#!/bin/bash
# usage: run_gen.sh p06_lighting[,p07...]
cd /x/IronBreach; rm -f Saved/rungen_done.txt
IB_GEN_SCRIPTS="$1" C:/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe "X:/IronBreach/IronBreach.uproject" -ExecutePythonScript="X:/IronBreach/Scripts/ib_run_gen.py" -stdout -FullStdOutLogOutput -unattended -nosplash > Saved/rungen.log 2>&1
ls Saved/rungen_done.txt; grep -a "RUNGEN\|\[Thornfield\].*\(VERIFY\|ERROR\|SUMMARY\)" Saved/rungen.log | sed 's/^\[[^]]*\]\[[^]]*\]//' | cut -c1-240
