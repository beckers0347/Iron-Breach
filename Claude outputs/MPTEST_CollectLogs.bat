@echo off
setlocal EnableDelayedExpansion
rem ============================================================================
rem  Iron Breach -- gather the MP test evidence after a session (both machines run this).
rem    Usage:  MPTEST_CollectLogs.bat host      (on Connor's machine)
rem            MPTEST_CollectLogs.bat client    (on Shane's machine)
rem    Copies Saved\Logs\IronBreach*.log (+ backups from relaunches) and any fresh crash folders
rem    into Saved\MPTest\<date>_<role>_<pc>\ and writes summary.txt with the lines that matter
rem    (net driver, joins, session status, link failures, [Mission] [Watch] [Mech], vault, errors).
rem    Zip that folder and send it over. Docs/MP_TEST_DAY_CHECKLIST.md §5 explains the lines.
rem ============================================================================
set "ROOT=%~dp0"
set "ROLE=%~1"
if not defined ROLE set "ROLE=unknown"
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HHmm'"`) do set "STAMP=%%T"
set "OUT=%ROOT%Saved\MPTest\%STAMP%_%ROLE%_%COMPUTERNAME%"
mkdir "%OUT%" 2>nul

echo Collecting into %OUT%
if exist "%ROOT%Saved\Logs\IronBreach*.log" copy /Y "%ROOT%Saved\Logs\IronBreach*.log" "%OUT%\" >nul
if exist "%ROOT%Saved\Logs\IronBreach-backup-*.log" copy /Y "%ROOT%Saved\Logs\IronBreach-backup-*.log" "%OUT%\" >nul
rem crash folders from today only (the rest are history)
for /f "usebackq delims=" %%C in (`powershell -NoProfile -Command "Get-ChildItem -Directory '%ROOT%Saved\Crashes' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-12) } | ForEach-Object { $_.FullName }"`) do (
  xcopy /E /I /Q "%%C" "%OUT%\Crashes\%%~nxC" >nul
)

set "SUM=%OUT%\summary.txt"
echo ==== IRON BREACH MP TEST -- %ROLE% on %COMPUTERNAME% -- %date% %time% ==== > "%SUM%"
set "GIT="
for %%G in (git.exe) do if not "%%~$PATH:G"=="" set "GIT=%%~$PATH:G"
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set "GIT=C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "D:\Git\cmd\git.exe" set "GIT=D:\Git\cmd\git.exe"
if defined GIT (
  echo --- build on this machine >> "%SUM%"
  "!GIT!" -C "%ROOT%." log -1 --oneline >> "%SUM%" 2>&1
  "!GIT!" -C "%ROOT%." status --short -- Source >> "%SUM%" 2>&1
)
if exist "%ROOT%Binaries\Win64\UnrealEditor-IronBreach.dll" (
  echo --- game DLL >> "%SUM%"
  for %%F in ("%ROOT%Binaries\Win64\UnrealEditor-IronBreach.dll") do echo %%~tF  %%~zF bytes >> "%SUM%"
)

for %%L in ("%OUT%\IronBreach*.log") do (
  echo. >> "%SUM%"
  echo ======== %%~nxL ======== >> "%SUM%"
  echo --- net driver / transport >> "%SUM%"
  findstr /L /I /C:"SteamNetDriver_0 bound" /C:"IpNetDriver_0 listening" /C:"Mounting Engine plugin SocketSubsystemSteamIP" /C:"LogSockets" /C:"bIsLanMatch" "%%~L" >> "%SUM%"
  echo --- session beats >> "%SUM%"
  findstr /L /I /C:"Session status:" /C:"IBHost:" /C:"IBJoin:" /C:"tearing down the stale" /C:"Invite accepted" /C:"JoinSearchResult" "%%~L" >> "%SUM%"
  echo --- joins / leaves / failures >> "%SUM%"
  findstr /L /I /C:"Join succeeded" /C:"UNetConnection::Close" /C:"NetworkFailure" /C:"network failure" /C:"travel failure" /C:"dropping the stale local session" /C:"ConnectionTimeout" /C:"ConnectionLost" /C:"operative on station" /C:"PawnLeavingGame" /C:"Logout" "%%~L" >> "%SUM%"
  echo --- mission / watch / mech / vault >> "%SUM%"
  findstr /L /C:"[Mission]" /C:"[Watch]" /C:"[Mech]" /C:"Vault:" /C:"Kit:" "%%~L" >> "%SUM%"
  echo --- errors >> "%SUM%"
  findstr /L /I /C:"Ensure condition failed" /C:"Assertion failed" /C:"Fatal error" /C:"LogOutputDevice: Error" /C:"Error:" "%%~L" | findstr /L /V /I /C:"LogShaderCompilers" /C:"M_AI_Foam" >> "%SUM%"
)

echo.
echo Done. Summary: %SUM%
echo Zip the folder %OUT% and send it over.
start "" "%OUT%"
pause
