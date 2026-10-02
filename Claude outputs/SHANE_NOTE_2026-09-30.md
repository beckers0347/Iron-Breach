Hey Shane, I pushed to main (e106831). Pull when you get a sec; it merged clean with your garrison work.

Good news first: tonight a second game instance joined over the network for the first time. Both players
boarded the mech, swapped seats, and when the gunner got out the AI took over the gun. Host 6/6, client 13/13.

Four things I need from you:

1. BP_Mech. Your Sep 4 commit "Updated Textures" (46f1cca) deleted the whole old mech folder: BP_Mech,
   ABP_Mech, SK_Mech, the Nightshade/Starter skins and the physics assets. Nothing replaced it, so there was
   no mech to test with. I restored that set on main (e106831, same files as before your commit). If you
   deleted it on purpose or have a newer BP_Mech on the new Starter_Mech packs, say so and we'll revert it.
   One fix needed either way: BP_Mech still calls "UpdateMechProximity" on the infantry BP, which doesn't
   exist anymore, so it shows Blueprint compile errors. Delete that node and recompile.

2. Please reparent BP_FirstPersonPlayerController to IBPlayerController (Class Settings > Parent Class).
   Until then, the code that saves the mech when a pilot disconnects never runs.

3. Your DefaultGame.ini change added a GameFeatureData asset-manager row, but the GameFeatures plugin isn't
   enabled on my side, so every launch now logs an ensure ("Failed to load class
   /Script/GameFeatures.GameFeatureData"). Either enable the plugin or drop that row. Your call.

4. Astra has been planning a layout pass on CarrowGateGarrison, and you're placing buildings in it too.
   It's one binary file, so whoever saves second wipes the other's changes. Let's agree who owns that map
   before anyone saves it.

Next: a two-PC session over Steam, so we can drive the mech and shoot at the same time and watch CONCORD
go up. That needs both of us.
