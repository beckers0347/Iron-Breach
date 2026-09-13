IRON BREACH -- SYNC PACK (2026-09-11, commit 1434fee)

WHAT THIS IS
  Connor's latest work is on GitHub, but Unreal does NOT recompile C++ when you pull --
  that is why you saw the old main menu last time. This pack pulls the repo AND puts the
  matching compiled game code in place (or compiles it for you if your engine differs).

HOW TO USE IT
  1. Close Unreal Editor AND the game.
  2. Unzip this WHOLE folder INTO your IronBreach project folder -- the one that contains
     IronBreach.uproject. Say yes to replacing files.
  3. Double-click  UPDATE_IronBreach.bat  and leave it open until it says "Up to date".
  4. Start Steam, then double-click  PLAY_IronBreach.bat.

WHAT IS NEW IN THIS ONE
  - THE WATCH: the deploy screen is now the CARROW-1 command deck -- a live planet outside
    the window with every sector pinned. Click a pin, read the mission card, DEPLOY. Double-
    click the Carrow pin (or VIEW MISSION) for the tactical breach board.
  - DEPLOY is no longer a countdown: it plays a 2.4 s drop and the whole squad travels
    together. Anyone can propose a breach; the host confirms.
  - Menus and the Bastion got a visual pass.
  - Steam net driver fix: the listen server was binding the wrong driver, so joining over
    the internet could not connect. Worth a real test -- host, invite, join.
  - Mechs: if one of the two crew disconnects, the hull survives, the gunner is promoted
    into the driver's seat and AI backfills the gun.

IF SOMETHING GOES WRONG
  Screenshot the first line that says "error" or "FAILED" and send it to Connor.
  Joining: have Iron Breach RUNNING before you accept a Steam invite, or just use the
  in-game Squad tab (F) and hit JOIN -- that avoids Steam's launcher entirely.
