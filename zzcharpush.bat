@echo off
setlocal EnableDelayedExpansion
set GIT="D:\Git\cmd\git.exe"
set "PROJ=D:\Unreal Games\IronBreach"
set "UE=A:\Unreal Engine\UE_5.8"
set "REP=%PROJ%\Saved\char_push_report.txt"
set "UNM=%PROJ%\Saved\zz_unmerged.txt"
cd /d "%PROJ%"
echo ==== RESUME MERGE + BUILD + PUSH %date% %time% ==== > "%REP%"
echo (commit A is already in; this does merge -> build -> push. Leave open until ZZCHARPUSH DONE.) >> "%REP%"

rem editor lock guard: if a .uasset cannot be replaced, the Unreal editor is still open.
if exist ".git\MERGE_HEAD" ( %GIT% merge --abort >> "%REP%" 2>&1 & echo cleaned a prior half-merge >> "%REP%" )
if exist ".git\index.lock" (
  tasklist /FI "IMAGENAME eq git.exe" 2>nul | find /I "git.exe" >nul
  if not errorlevel 1 ( echo ABORT: git.exe running + lock. >> "%REP%" & goto :done )
  del ".git\index.lock" & echo cleared stale lock >> "%REP%"
)

rem 1) clean the content files Shane also changed (drop local 5.8 re-saves)
set "LOCKED="
for %%C in ("Content/BP_IronBreachGameMode.uasset" "Content/Characters/Infantry/ABP_Infantry.uasset" "Content/Characters/Infantry/BP_IBCharacter_Infantry.uasset" "Content/Characters/Infantry/Skins/Chaos/Chaos_Skin.uasset" "Content/Characters/Infantry/Skins/Chaos/Chaos_Skin_PhysicsAsset.uasset" "Content/Characters/Infantry/Skins/Chaos/tripo_mat_4243f06f.uasset" "Content/Characters/Kaiju/Anims/ABP_Kaiju.uasset" "Content/Characters/Kaiju/BP_KaijuSpawner.uasset" "Content/Characters/Kaiju/Blueprints/BP_Kaiju.uasset" "Content/Characters/Kaiju/DA_Kaiju_Alpha.uasset" "Content/Characters/Mannequins/Anims/Rifle/Jog/MF_Rifle_Jog_Fwd.uasset" "Content/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS.uasset" "Content/Characters/Mannequins/Anims/Rifle/Walk/MF_Rifle_Walk_Fwd.uasset" "Content/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.uasset" "Content/Characters/Mannequins/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd.uasset" "Content/Characters/Mannequins/Anims/Unarmed/MM_Idle.uasset" "Content/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.uasset" "Content/Characters/Mannequins/Meshes/SKM_Manny_Simple.uasset" "Content/Characters/Mannequins/Meshes/SK_Mannequin.uasset" "Content/LevelPrototyping/AIModels_District/SM_Stretcher.fbx" "Content/LevelPrototyping/AITextures/M_AI_GlowVein.uasset" "Content/LevelPrototyping/AITextures/M_AI_Water.uasset" "Content/LevelPrototyping/CarrowGateGarrison.umap" "Content/Weapons/Generated/Pistol/DA_Visual_Pistol_B.uasset" "Content/Weapons/Generated/Shotgun/DA_Visual_Shotgun_B.uasset" "Content/Weapons/Generated/Sniper/DA_Visual_Sniper_B.uasset" "Content/Weapons/InfantryWeapons/Amethyst_Arc/Amethyst_Arc.uasset") do ( %GIT% checkout -- "%%~C" 2>> "%REP%" || set "LOCKED=1" )
if defined LOCKED ( echo ABORT: could not replace a content .uasset -- the UNREAL EDITOR is still open. Close it fully, then run this again. >> "%REP%" & goto :done )

rem 2) fetch + merge
%GIT% fetch origin >> "%REP%" 2>&1
%GIT% merge --no-commit --no-ff origin/main >> "%REP%" 2>&1
if not exist ".git\MERGE_HEAD" ( echo ABORT: merge did not start ^(likely editor still holding a file^). Close Unreal and rerun. >> "%REP%" & goto :done )

rem 3) resolve the 3 source conflicts to OUR side (commit A holds the hand-merge)
for %%S in ("Source/IronBreach/Infantry/IBCharacter_Infantry.cpp" "Source/IronBreach/Infantry/IBCharacter_Infantry.h" "Source/IronBreach/Items/IBInventoryComponent.cpp") do ( %GIT% checkout --ours -- "%%~S" >> "%REP%" 2>&1 & %GIT% add -- "%%~S" >> "%REP%" 2>&1 )

rem 4) any other unmerged path -> take theirs
%GIT% diff --name-only --diff-filter=U > "%UNM%" 2>>"%REP%"
for /f "usebackq delims=" %%U in ("%UNM%") do ( %GIT% checkout --theirs -- "%%U" >> "%REP%" 2>&1 & %GIT% add -- "%%U" >> "%REP%" 2>&1 )
%GIT% diff --name-only --diff-filter=U > "%UNM%" 2>>"%REP%"
for %%Z in ("%UNM%") do set "USIZE=%%~zZ"
if not "!USIZE!"=="0" ( echo ABORT: unmerged remain: >> "%REP%" & type "%UNM%" >> "%REP%" & goto :done )

rem 5) commit the merge
%GIT% commit -m "Merge origin/main into operative flow + class kits. Shane upstream: third-person weapon mesh, interact + carry (M1 LANDFALL), M1/M2 mission directors, IBAnimInstance, scroll-wheel weapon switching, level/content updates. IBCharacter_Infantry hand-merged: keeps his TP-weapon/carry/interact AND restores the user-settings look/FOV/toggle-ADS + F->Squad bind an older upstream copy had dropped; operative body swap yields to a custom BP body and verifies skeleton + weapon socket first. IBInventoryComponent keeps his equip-debug logs." -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01J4FnjxXmBXUCZH6zaN9Rnu" >> "%REP%" 2>&1
set "MCE=!ERRORLEVEL!"
echo MERGE_COMMIT_EXIT=!MCE! >> "%REP%"
if not "!MCE!"=="0" ( echo ABORT: merge commit failed. >> "%REP%" & goto :done )
echo MERGE_DONE >> "%REP%"
%GIT% log --oneline -4 >> "%REP%" 2>&1

rem 6) BUILD to verify (editor must be closed)
echo ==== BUILD ==== >> "%REP%"
call "%UE%\Engine\Build\BatchFiles\Build.bat" IronBreachEditor Win64 Development -project="%PROJ%\IronBreach.uproject" -WaitMutex >> "%REP%" 2>&1
set "BE=!ERRORLEVEL!"
echo BUILD_EXIT=!BE! >> "%REP%"
if not "!BE!"=="0" ( echo ABORT: build failed -- NOT pushing. >> "%REP%" & goto :done )

rem 7) PUSH
echo ==== PUSH ==== >> "%REP%"
%GIT% push origin main >> "%REP%" 2>&1
set "PE=!ERRORLEVEL!"
echo PUSH_EXIT=!PE! >> "%REP%"
%GIT% log --oneline -3 >> "%REP%" 2>&1
:done
echo ZZCHARPUSH DONE >> "%REP%"
