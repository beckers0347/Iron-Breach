"""Separate a garrison tool's own result from engine noise in a commandlet log.

Plain Python -- runs anywhere, does not need Unreal:

    python Scripts/ib_classify_commandlet_log.py <commandlet.log> [--json out.json]

Why: every commandlet on the current map ends "Failure - 23 error(s)", because
the engine hits a handled ensure while registering Primary Asset Types, before
any Python runs:

    Ensure condition failed: AssetBaseClassLoaded ... AssetManagerTypes.cpp:82
    Failed to load class /Script/GameFeatures.GameFeatureData for Primary Asset Type GameFeatureData!

Config/DefaultGame.ini (from fed25b7) lists a GameFeatureData PrimaryAssetTypesToScan
row while the GameFeatures plugin is not enabled in IronBreach.uproject. The
ensure's banner, message and callstack are each logged as an "Error:" line, and
that is the whole 23. None of it comes from the garrison scripts.

This splits the log at the "Running Python script" line, groups error lines by
signature on each side, and reports the script's own completion marker, so a
tool result can be judged on its own evidence.
"""
import re, sys, json
from collections import Counter

SCRIPT_START = re.compile(r"LogPythonScriptCommandlet: Display: Running Python script: (.+)")
SCRIPT_OK = re.compile(r"LogPythonScriptCommandlet: Display: Python script executed successfully")
SUMMARY = re.compile(r"(Success|Failure) - (\d+) error\(s\), (\d+) warning\(s\)")
ERROR = re.compile(r"\]\[\s*\d+\](\w+): (?:Display: )?Error: (.*)")
WARN = re.compile(r"\]\[\s*\d+\](\w+): (?:Display: )?Warning: (.*)")
TOOL_MARK = re.compile(r"GARRISON (INVENTORY|LAYOUT|PROBE)[: ]|SUPPORT PROBE:")
ENSURE_GFD = ("GameFeatureData", "AssetBaseClassLoaded", "Handled ensure", "Stack:", "[Callstack]")


def signature(category, text):
    text = re.sub(r"0x[0-9a-fA-F]+", "0x..", text)
    text = re.sub(r"\d+", "#", text)
    if category == "LogOutputDevice":
        return "LogOutputDevice (ensure/callstack block)"
    return "%s: %s" % (category, text[:120])


def classify(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    start = next((i for i, l in enumerate(lines) if SCRIPT_START.search(l)), None)
    ok = any(SCRIPT_OK.search(l) for l in lines)
    summary = None
    for l in lines:
        m = SUMMARY.search(l)
        if m:
            summary = {"result": m.group(1), "errors": int(m.group(2)), "warnings": int(m.group(3))}
    before, during, warn_before, warn_during = Counter(), Counter(), Counter(), Counter()
    gfd_block = 0
    tool_lines = []
    for i, l in enumerate(lines):
        if "LogInit: Display:" in l:          # the end-of-run recap repeats earlier lines
            continue
        m = ERROR.search(l)
        if m:
            sig = signature(m.group(1), m.group(2))
            (before if start is None or i < start else during)[sig] += 1
            if m.group(1) == "LogOutputDevice":
                gfd_block += 1
        w = WARN.search(l)
        if w:
            (warn_before if start is None or i < start else warn_during)[signature(w.group(1), w.group(2))] += 1
        if start is not None and i >= start and TOOL_MARK.search(l):
            tool_lines.append(l.strip()[:300])
    gfd = any("GameFeatureData" in l for l in lines)
    return {
        "log": path,
        "script": SCRIPT_START.search(lines[start]).group(1) if start is not None else None,
        "script_reported_success": ok,
        "commandlet_summary": summary,
        "errors_before_script": dict(before), "errors_during_script": dict(during),
        "warnings_before_script": dict(warn_before), "warnings_during_script": dict(warn_during),
        "gamefeaturedata_ensure_present": gfd,
        "ensure_block_error_lines": gfd_block,
        "tool_marker_lines": tool_lines[-12:],
        "conclusion": (
            "Engine errors before the script: %d (GameFeatureData ensure block: %s). Errors while the script "
            "ran: %d. Judge the tool by its own tool_status.json and markers, not by the commandlet's "
            "Success/Failure line." % (sum(before.values()), "yes" if gfd else "no", sum(during.values()))),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    result = classify(sys.argv[1])
    if "--json" in sys.argv:
        with open(sys.argv[sys.argv.index("--json") + 1], "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))
