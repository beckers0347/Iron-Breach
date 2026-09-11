"""Commit + pull --rebase + push, run OUTSIDE Unreal.

The build watcher runs this inside UnrealEditor-Cmd, which holds .uasset handles --
a pull would then fail with "unable to unlink". So this only launches
Saved/zz_gitpush.bat detached; that script waits for Unreal to exit, then does the
git work (Windows git + git-lfs) and writes Saved/zz_push_report.txt.
"""
import subprocess, unreal
BAT = r"D:\Unreal Games\IronBreach\Saved\zz_gitpush.bat"
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
p = subprocess.Popen(["cmd.exe", "/c", BAT], close_fds=True,
                     creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                     cwd=r"D:\Unreal Games\IronBreach")
unreal.log(f"IBPY: git push script launched pid={p.pid} -- see Saved/zz_push_report.txt")
