import subprocess, unreal
r = subprocess.run(["taskkill", "/F", "/IM", "UnrealEditor.exe"], capture_output=True, text=True)
unreal.log(f"IBPY: KILL rc={r.returncode} {r.stdout.strip()} {r.stderr.strip()}")
