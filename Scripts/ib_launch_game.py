"""Launch IronBreach (-game) from the headless watcher and return immediately.
Kills a running -game instance first (the DLL must be free for builds anyway).
Reads extra launch args from Saved/zz_launch_args.txt when present (one line)."""
import subprocess, os, unreal
UE = r"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
PROJ = r"D:\Unreal Games\IronBreach\IronBreach.uproject"
subprocess.run(["taskkill", "/F", "/IM", "UnrealEditor.exe"], capture_output=True)
extra = []
argf = r"D:\Unreal Games\IronBreach\Saved\zz_launch_args.txt"
if os.path.exists(argf):
    extra = open(argf).read().split()
args = [UE, PROJ, "-game", "-windowed", "-ResX=1600", "-ResY=900", "-WinX=100", "-WinY=60", "-NoSplash", "-log"] + extra
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
p = subprocess.Popen(args, close_fds=True, creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP, cwd=r"D:\Unreal Games\IronBreach")
unreal.log(f"IBPY: LAUNCHED game pid={p.pid} args={extra}")
