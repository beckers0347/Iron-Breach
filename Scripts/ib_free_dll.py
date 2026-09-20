"""Free Binaries/Win64/UnrealEditor-IronBreach.dll so the linker can overwrite it.
A crashed -game run (or its CrashReportClient) keeps the module mapped and LNK1104s the build."""
import subprocess, unreal
for image in ("CrashReportClient.exe", "CrashReportClientEditor.exe", "UnrealEditor.exe"):
    r = subprocess.run(["taskkill", "/F", "/IM", image], capture_output=True, text=True)
    unreal.log(f"IBPY: kill {image} rc={r.returncode} {r.stdout.strip()}{r.stderr.strip()}")
