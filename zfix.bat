@echo off
setlocal
set GIT="D:\Git\cmd\git.exe"
set PROJ=D:\Unreal Games\IronBreach
set UE=A:\Unreal Engine\UE_5.8
set REP=%PROJ%\Saved\ib_fix_report.txt
cd /d "%PROJ%"
echo ==== CANNON FIX BUILD+PUSH %date% %time% ==== > "%REP%"

call "%UE%\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -Project="%PROJ%\IronBreach.uproject" -WaitMutex >> "%REP%" 2>&1
echo BUILD_EXIT=%ERRORLEVEL% >> "%REP%"
if not "%ERRORLEVEL%"=="0" goto done

%GIT% add Source/IronBreach/Mech/IBMech_Base.cpp >> "%REP%" 2>&1
%GIT% commit -m "[mech] cannon damage now goes through IDamageableInterface with the real hit result - generic ApplyDamage bypassed kaiju armor AND organ weak points, so the anti-kaiju weapon skipped the entire boss phase design. Non-damageable actors keep the generic fallback. Closes the ub-13 caveat from KAIJU_FIGHT_WIRING" >> "%REP%" 2>&1
%GIT% pull --no-rebase --no-edit origin main >> "%REP%" 2>&1
%GIT% push origin main >> "%REP%" 2>&1
echo --- FINAL --- >> "%REP%"
%GIT% rev-parse --short HEAD >> "%REP%" 2>&1
%GIT% rev-parse --short origin/main >> "%REP%" 2>&1

:done
echo ==== done %date% %time% ==== >> "%REP%"
del "%~f0"
