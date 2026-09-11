@echo off
setlocal EnableDelayedExpansion
set GIT="D:\Git\cmd\git.exe"
set "PROJ=D:\Unreal Games\IronBreach"
set "REP=%PROJ%\Saved\char_push_report.txt"
set "RES=%PROJ%\Saved\zz_merge"
cd /d "%PROJ%"
echo ==== OPERATIVE FLOW COMMIT + MERGE origin/main %date% %time% ==== > "%REP%"
rem A stale .git\index.lock blocks every add+commit; clear it only when no git.exe is alive.
if exist ".git\index.lock" (
  tasklist /FI "IMAGENAME eq git.exe" 2>nul | find /I "git.exe" >nul
  if not errorlevel 1 (
    echo ABORT: .git\index.lock exists and git.exe is running -- close the editor / other git and rerun. >> "%REP%"
    goto :done
  )
  del ".git\index.lock"
  echo cleared stale .git\index.lock >> "%REP%"
)

rem ---- 1) stage the scoped file list, one path at a time, retrying transient sharing violations
set "ADDFAIL="
for %%P in ("Source/IronBreach/Player" "Source/IronBreach/Items/IBPlayerState.h" "Source/IronBreach/Items/IBPlayerState.cpp" "Source/IronBreach/UI/IBCharacterCreateScreen.h" "Source/IronBreach/UI/IBCharacterCreateScreen.cpp" "Source/IronBreach/UI/IBCharacterSelectScreen.h" "Source/IronBreach/UI/IBCharacterSelectScreen.cpp" "Source/IronBreach/UI/IBSheetDismissProcessor.h" "Source/IronBreach/UI/IBMainMenuWidget.h" "Source/IronBreach/UI/IBMainMenuWidget.cpp" "Source/IronBreach/UI/IBLobbyStripWidget.cpp" "Source/IronBreach/UI/IBPlayerBannerWidget.cpp" "Source/IronBreach/UI/IBFriendsScreen.cpp" "Source/IronBreach/Online/IBSessionSubsystem.h" "Source/IronBreach/Online/IBSessionSubsystem.cpp" "Docs/OPERATIVE_SELECT_WIRING.md" "Scripts/ib_audit_character_flow.py" "Scripts/ib_wire_menu_playerstate.py" "Content/FirstPerson/Blueprints/BP_FirstPersonGameMode.uasset" "Source/IronBreach/Classes" "Source/IronBreach/UI/IBKitHudWidget.h" "Source/IronBreach/UI/IBKitHudWidget.cpp" "Source/IronBreach/Progression/IBVaultSubsystem.h" "Source/IronBreach/Progression/IBVaultSubsystem.cpp" "Source/IronBreach/Progression/IBXPSubsystem.h" "Source/IronBreach/Progression/IBXPSubsystem.cpp" "Source/IronBreach/Items/IBInventoryComponent.h" "Source/IronBreach/Items/IBInventoryComponent.cpp" "Source/IronBreach/Infantry/IBCharacter_Infantry.h" "Source/IronBreach/Infantry/IBCharacter_Infantry.cpp" "Content/IronBreach/Classes" "Scripts/ib_create_class_kits.py" "Scripts/ib_create_kit_materials.py" "zzcharwatch.bat" "zzchargame.bat" "zzcharpush.bat" "zzcharmerge.bat") do (
  call :addretry "%%~P"
  if errorlevel 1 set "ADDFAIL=1"
)
if defined ADDFAIL (
  echo ABORT: some paths could not be staged after retries -- nothing committed. >> "%REP%"
  %GIT% reset -q >> "%REP%" 2>&1
  goto :done
)
%GIT% diff --cached --stat >> "%REP%" 2>&1
%GIT% commit -m "Operative select + creation flow: PRESS ANY BUTTON -> SELECT OPERATIVE (3 billets, forced intake on an empty roster) -> NEW OPERATIVE (callsign / combat trade / gender) -> menu. IBCharacterSubsystem + IBCharacters.sav, pure-C++ sheets in IBStyle (two-step decommission, SWITCH chip, travel guard, lobby-aware), operative identity replicated on IBPlayerState and pushed via the PlayerState from any controller; fireteam banners print the callsign with the trade color. BP_FirstPersonGameMode PlayerState -> BP_IBPlayerState (headless py). Live operative preview stage (mannequin + studio lights + scene capture) behind Destiny-style select/create layouts; placeholder title art removed behind the sheets. Deploy goes straight into your own listen-hosted world (no lobby/menu); the squad forms from the in-game Squad tab; session destroy is serialized before create/join. Class kits (data-driven, open design): IBOperativeKitComponent resolves the trade -> DA_Kit_<Trade> (Q kit ability / V movement tool; Dash, Grapple, Glide, ConeStrike, DeployZone or Blueprint effects), replicated AIBKitZone pylon (slow / mark, lands on the floor, M_IBKitZone glow), pure-C++ kit HUD chips. Per-operative progression: XP/ledger keys carry #OperativeId, IBVaultSubsystem restores/saves inventory + equipment per character, level-ups sync back to the roster. The picked body: infantry mesh swaps Manny/Quinn from the operative identity. Build watcher + audit/content scripts + wiring doc." -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01J4FnjxXmBXUCZH6zaN9Rnu" >> "%REP%" 2>&1
set "COMMITEXIT=%ERRORLEVEL%"
echo COMMIT_EXIT=%COMMITEXIT% >> "%REP%"
if not "%COMMITEXIT%"=="0" goto :done

rem ---- 2) merge origin/main (no commit) and drop in the pre-resolved infantry/inventory files
%GIT% fetch origin >> "%REP%" 2>&1
echo FETCH_EXIT=%ERRORLEVEL% >> "%REP%"
%GIT% merge --no-commit --no-ff origin/main >> "%REP%" 2>&1
echo MERGE_EXIT=%ERRORLEVEL% >> "%REP%"
if not exist ".git\MERGE_HEAD" (
  echo ABORT: merge did not start ^(see git output above^) -- scoped commit is in, nothing merged. >> "%REP%"
  goto :done
)
copy /Y "%RES%\IBCharacter_Infantry.cpp" "Source\IronBreach\Infantry\IBCharacter_Infantry.cpp" >> "%REP%" 2>&1
copy /Y "%RES%\IBCharacter_Infantry.h" "Source\IronBreach\Infantry\IBCharacter_Infantry.h" >> "%REP%" 2>&1
copy /Y "%RES%\IBInventoryComponent.cpp" "Source\IronBreach\Items\IBInventoryComponent.cpp" >> "%REP%" 2>&1
set "ADDFAIL="
for %%P in ("Source/IronBreach/Infantry/IBCharacter_Infantry.cpp" "Source/IronBreach/Infantry/IBCharacter_Infantry.h" "Source/IronBreach/Items/IBInventoryComponent.cpp") do (
  call :addretry "%%~P"
  if errorlevel 1 set "ADDFAIL=1"
)
if defined ADDFAIL (
  echo ABORT: resolved files could not be staged -- merge left open for a human. >> "%REP%"
  goto :done
)
%GIT% diff --name-only --diff-filter=U > "%PROJ%\Saved\zz_unmerged.txt" 2>>"%REP%"
for %%S in ("%PROJ%\Saved\zz_unmerged.txt") do set "USIZE=%%~zS"
if not "%USIZE%"=="0" (
  echo ABORT: unmerged paths remain -- merge left open for a human: >> "%REP%"
  type "%PROJ%\Saved\zz_unmerged.txt" >> "%REP%"
  goto :done
)
%GIT% commit -m "Merge origin/main (Shane: TP weapon mesh, interact/carry, M1/M2 mission directors, weapon-slot scroll) into the operative flow + class kits. Infantry: keeps the user-settings look/FOV/toggle-ADS and the F -> Squad bind that upstream had dropped from an older copy of the file; operative body swap now yields to a custom BP body and checks skeleton + weapon socket first." -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01J4FnjxXmBXUCZH6zaN9Rnu" >> "%REP%" 2>&1
echo MERGE_COMMIT_EXIT=%ERRORLEVEL% >> "%REP%"
%GIT% log --oneline -4 >> "%REP%" 2>&1
%GIT% status --short >> "%REP%" 2>&1
goto :done

:addretry
set "N=0"
:addagain
%GIT% add -- "%~1" >> "%REP%" 2>&1
if not errorlevel 1 exit /b 0
set /a N+=1
if %N% GEQ 6 (
  echo ADD FAILED after %N% tries: %~1 >> "%REP%"
  exit /b 1
)
timeout /t 3 /nobreak >nul
goto :addagain

:done
echo ZZCHARPUSH DONE >> "%REP%"
