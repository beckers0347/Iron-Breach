#!/bin/bash
# usage: run_cap.sh tag
cd /x/IronBreach; IB_TF_TAG="$1" C:/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe "X:/IronBreach/IronBreach.uproject" -ExecutePythonScript="X:/IronBreach/Scripts/ib_capture_thornfield.py" -stdout -FullStdOutLogOutput -unattended -nosplash > Saved/tf_cap.log 2>&1
ls Saved/ThornfieldShots/$1
