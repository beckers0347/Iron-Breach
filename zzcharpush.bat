@echo off
setlocal EnableDelayedExpansion
set GIT="D:\Git\cmd\git.exe"
set "PROJ=D:\Unreal Games\IronBreach"
set "UE=A:\Unreal Engine\UE_5.8"
set "REP=%PROJ%\Saved\char_push_report.txt"
set "UNM=%PROJ%\Saved\zz_unmerged.txt"
cd /d "%PROJ%"
echo ==== MERGE + BUILD + PUSH %date% %time% ==== > "%REP%"
echo (leave this window open until it says ZZCHARPUSH DONE) >> "%REP%"

rem --- 0) stale index.lock (clear only if no git.exe alive)
if exist ".git\index.lock" (
  tasklist /FI "IMAGENAME eq git.exe" 2>nul | find /I "git.exe" >nul
  if not errorlevel 1 ( echo ABORT: .git\index.lock exists and git.exe is running -- close the editor/other git and rerun. >> "%REP%" & goto :done )
  del ".git\index.lock"
  echo cleared stale .git\index.lock >> "%REP%"
)

rem --- 1) stage the scoped file list (retry transient sync locks) -> commit A
set "ADDFAIL="
for %%P in ("Source/IronBreach/Player" "Source/IronBreach/Items/IBPlayerState.h" "Source/IronBreach/Items/IBPlayerState.cpp" "Source/IronBreach/UI/IBCharacterCreateScreen.h" "Source/IronBreach/UI/IBCharacterCreateScreen.cpp" "Source/IronBreach/UI/IBCharacterSelectScreen.h" "Source/IronBreach/UI/IBCharacterSelectScreen.cpp" "Source/IronBreach/UI/IBSheetDismissProcessor.h" "Source/IronBreach/UI/IBMainMenuWidget.h" "Source/IronBreach/UI/IBMainMenuWidget.cpp" "Source/IronBreach/UI/IBLobbyStripWidget.cpp" "Source/IronBreach/UI/IBPlayerBannerWidget.cpp" "Source/IronBreach/UI/IBFriendsScreen.cpp" "Source/IronBreach/Online/IBSessionSubsystem.h" "Source/IronBreach/Online/IBSessionSubsystem.cpp" "Docs/OPERATIVE_SELECT_WIRING.md" "Scripts/ib_audit_character_flow.py" "Scripts/ib_wire_menu_playerstate.py" "Content/FirstPerson/Blueprints/BP_FirstPersonGameMode.uasset" "Source/IronBreach/Classes" "Source/IronBreach/UI/IBKitHudWidget.h" "Source/IronBreach/UI/IBKitHudWidget.cpp" "Source/IronBreach/Progression/IBVaultSubsystem.h" "Source/IronBreach/Progression/IBVaultSubsystem.cpp" "Source/IronBreach/Progression/IBXPSubsystem.h" "Source/IronBreach/Progression/IBXPSubsystem.cpp" "Source/IronBreach/Items/IBInventoryComponent.h" "Source/IronBreach/Items/IBInventoryComponent.cpp" "Source/IronBreach/Infantry/IBCharacter_Infantry.h" "Source/IronBreach/Infantry/IBCharacter_Infantry.cpp" "Content/IronBreach/Classes" "Scripts/ib_create_class_kits.py" "Scripts/ib_create_kit_materials.py" "zzcharwatch.bat" "zzchargame.bat" "zzcharpush.bat") do ( call :addretry "%%~P" & if errorlevel 1 set "ADDFAIL=1" )
if defined ADDFAIL ( echo ABORT: staging failed after retries -- nothing committed. >> "%REP%" & %GIT% reset -q >> "%REP%" 2>&1 & goto :done )
%GIT% diff --cached --stat >> "%REP%" 2>&1
%GIT% commit -m "Operative select + creation flow + class kits: PRESS ANY BUTTON -> SELECT OPERATIVE (3 billets, live 3D preview, forced intake on empty roster) -> NEW OPERATIVE (callsign / trade / gender) -> straight into your own listen-hosted world. IBCharacterSubsystem + IBCharacters.sav; pure-C++ IBStyle sheets; operative identity replicated on IBPlayerState and pushed from any controller; banners show callsign + trade color. Class kits (data-driven, open design): IBOperativeKitComponent resolves trade -> DA_Kit_<Trade> (Q ability / V movement; Dash/Grapple/Glide/ConeStrike/DeployZone/Blueprint), replicated AIBKitZone pylon (slow/mark, floor-landing, M_IBKitZone glow), pure-C++ HUD chips. Per-operative progression: XP/ledger/vault keyed by #OperativeId, IBVaultSubsystem restores/saves loadout, level syncs to roster. Gender-driven infantry body swap (guards a custom BP body + skeleton/socket). BP_FirstPersonGameMode PlayerState -> BP_IBPlayerState." -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01J4FnjxXmBXUCZH6zaN9Rnu" >> "%REP%" 2>&1
set "CE=!ERRORLEVEL!"
echo COMMIT_A_EXIT=!CE! >> "%REP%"
if not "!CE!"=="0" ( echo ABORT: scoped commit failed. >> "%REP%" & goto :done )

rem --- 2) clean the content files Shane also changed (drop local 5.8 re-saves; his versions win)
for %%C in ("Content/BP_IronBreachGameMode.uasset" "Content/Characters/Infantry/ABP_Infantry.uasset" "Content/Characters/Infantry/BP_IBCharacter_Infantry.uasset" "Content/Characters/Infantry/Skins/Chaos/Chaos_Skin.uasset" "Content/Characters/Infantry/Skins/Chaos/Chaos_Skin_PhysicsAsset.uasset" "Content/Characters/Infantry/Skins/Chaos/tripo_mat_4243f06f.uasset" "Content/Characters/Kaiju/Anims/ABP_Kaiju.uasset" "Content/Characters/Kaiju/BP_KaijuSpawner.uasset" "Content/Characters/Kaiju/Blueprints/BP_Kaiju.uasset" "Content/Characters/Kaiju/DA_Kaiju_Alpha.uasset" "Content/Characters/Mannequins/Anims/Rifle/Jog/MF_Rifle_Jog_Fwd.uasset" "Content/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS.uasset" "Content/Characters/Mannequins/Anims/Rifle/Walk/MF_Rifle_Walk_Fwd.uasset" "Content/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.uasset" "Content/Characters/Mannequins/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd.uasset" "Content/Characters/Mannequins/Anims/Unarmed/MM_Idle.uasset" "Content/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.uasset" "Content/Characters/Mannequins/Meshes/SKM_Manny_Simple.uasset" "Content/Characters/Mannequins/Meshes/SK_Mannequin.uasset" "Content/LevelPrototyping/AIModels_District/SM_Stretcher.fbx" "Content/LevelPrototyping/AITextures/M_AI_GlowVein.uasset" "Content/LevelPrototyping/AITextures/M_AI_Water.uasset" "Content/LevelPrototyping/CarrowGateGarrison.umap" "Content/Weapons/Generated/Pistol/DA_Visual_Pistol_B.uasset" "Content/Weapons/Generated/Shotgun/DA_Visual_Shotgun_B.uasset" "Content/Weapons/Generated/Sniper/DA_Visual_Sniper_B.uasset" "Content/Weapons/InfantryWeapons/Amethyst_Arc/Amethyst_Arc.uasset") do %GIT% checkout -- "%%~C" >> "%REP%" 2>&1

rem --- 3) fetch + merge (no commit)
%GIT% fetch origin >> "%REP%" 2>&1
%GIT% merge --no-commit --no-ff origin/main >> "%REP%" 2>&1
if not exist ".git\MERGE_HEAD" ( echo ABORT: merge did not start ^(see git output above^) -- scoped commit is in, nothing merged. >> "%REP%" & goto :done )

rem --- 4) resolve the 3 source conflicts to OUR side (commit A already holds the hand-merge)
for %%S in ("Source/IronBreach/Infantry/IBCharacter_Infantry.cpp" "Source/IronBreach/Infantry/IBCharacter_Infantry.h" "Source/IronBreach/Items/IBInventoryComponent.cpp") do ( %GIT% checkout --ours -- "%%~S" >> "%REP%" 2>&1 & %GIT% add -- "%%~S" >> "%REP%" 2>&1 )

rem --- 5) any other unmerged path: content -> take theirs (Shane owns content)
%GIT% diff --name-only --diff-filter=U > "%UNM%" 2>>"%REP%"
for /f "usebackq delims=" %%U in ("%UNM%") do ( %GIT% checkout --theirs -- "%%U" >> "%REP%" 2>&1 & %GIT% add -- "%%U" >> "%REP%" 2>&1 )

rem --- 6) verify nothing is left unmerged
%GIT% diff --name-only --diff-filter=U > "%UNM%" 2>>"%REP%"
for %%Z in ("%UNM%") do set "USIZE=%%~zZ"
if not "!USIZE!"=="0" ( echo ABORT: unmerged paths remain -- left open for a human: >> "%REP%" & type "%UNM%" >> "%REP%" & goto :done )

rem --- 7) commit the merge
%GIT% commit -m "Merge origin/main into operative flow + class kits. Shane upstream: third-person weapon mesh, interact + carry (M1 LANDFALL), M1/M2 mission directors, IBAnimInstance, scroll-wheel weapon switching, level/content updates. IBCharacter_Infantry hand-merged: keeps his TP-weapon/carry/interact AND restores the user-settings look/FOV/toggle-ADS + F->Squad bind that an older upstream copy had dropped; operative body swap now yields to a custom BP body and verifies skeleton + weapon socket first. IBInventoryComponent keeps his equip-debug logs." -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01J4FnjxXmBXUCZH6zaN9Rnu" >> "%REP%" 2>&1
set "MCE=!ERRORLEVEL!"
echo MERGE_COMMIT_EXIT=!MCE! >> "%REP%"
if not "!MCE!"=="0" ( echo ABORT: merge commit failed. >> "%REP%" & goto :done )
echo MERGE_DONE >> "%REP%"
%GIT% log --oneline -4 >> "%REP%" 2>&1

rem --- 8) BUILD to verify (needs the editor CLOSED; a locked DLL fails here and blocks the push)
echo ==== BUILD ==== >> "%REP%"
call "%UE%\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -project="%PROJ%\IronBreach.uproject" -WaitMutex >> "%REP%" 2>&1
set "BE=!ERRORLEVEL!"
echo BUILD_EXIT=!BE! >> "%REP%"
if not "!BE!"=="0" ( echo ABORT: build failed -- NOT pushing. Close the Unreal editor if it is open, then run this again. >> "%REP%" & goto :done )

rem --- 9) PUSH (reached only when the build succeeded)
echo ==== PUSH ==== >> "%REP%"
%GIT% push origin main >> "%REP%" 2>&1
set "PE=!ERRORLEVEL!"
echo PUSH_EXIT=!PE! >> "%REP%"
%GIT% log --oneline -3 >> "%REP%" 2>&1
goto :done

:addretry
set "N=0"
:addagain
%GIT% add -- "%~1" >> "%REP%" 2>&1
if not errorlevel 1 exit /b 0
set /a N+=1
if %N% GEQ 6 ( echo ADD FAILED after %N% tries: %~1 >> "%REP%" & exit /b 1 )
timeout /t 3 /nobreak >nul
goto :addagain

:done
echo ZZCHARPUSH DONE >> "%REP%"
