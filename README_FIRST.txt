IRON BREACH -- sync pack from Connor (build 57324df, 2026-09-06)

WHAT THIS DOES
  Gets your copy of the project to the exact same state as Connor's: latest code from GitHub
  plus the compiled game code (Unreal does NOT recompile on its own after a pull, which is
  why your game was showing the old main menu and could not join his world).

HOW TO USE (2 minutes)
  1. Close Unreal completely (editor AND game).
  2. Unzip this whole pack INTO your IronBreach project folder -- the folder that has
     IronBreach.uproject in it. Say YES if it asks to overwrite.
  3. Double-click  UPDATE_IronBreach.bat   -> pulls from GitHub and installs the compiled code.
  4. Make sure Steam is running, then double-click  PLAY_IronBreach.bat
  5. Press any button -> SELECT OPERATIVE -> DEPLOY. You land in your own world.
     Press F -> Squad tab -> Connor's row (IN IRON BREACH) -> JOIN.

  If you see the SELECT OPERATIVE sheet with the 3D preview after "Press Any Button", you are on
  the right build. If you still see the old banner menu (SQUAD / + / + / +), the update did not take.

WHAT IS IN HERE
  UPDATE_IronBreach.bat   run after every pull that touched Source\ (or whenever Connor says "update")
  PLAY_IronBreach.bat     launches the game windowed, straight to the title screen
  BUILD_IronBreach.bat    compiles the C++ yourself (needs Visual Studio 2022 w/ C++ game dev) --
                          UPDATE falls back to this automatically if your engine build differs
  _SyncPack\              Connor's compiled game code (UnrealEditor-IronBreach.dll + manifests)

These files live next to IronBreach.uproject and are NOT part of the git repo (they will show as
untracked -- that is fine, do not commit them).
