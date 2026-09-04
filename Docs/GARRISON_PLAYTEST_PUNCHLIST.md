# Carrowgate Garrison — Playtest Readiness Punch List

*Audit performed by inspecting asset references directly (material assignments, texture maps, and — for the Animation Blueprint — the compiler warning strings UE bakes into the asset). Everything below is a verified finding, not a guess.*

---

## 1. Animation — the hand-grip bug is now diagnosed, not just described

This is the bug from the hand-IK debugging session that got left open ("Nope try again" / no resolution). Pulling the compiler warnings directly out of `ABP_InfantryTripo3D` gives the exact cause:

> `Node "Transform (Modify) Bone - Bone: RightHand" uses potentially thread-unsafe call "Get ThirdPersonWeaponMesh". Disable threaded update or use a thread-safe call.`
> `Node "Transform (Modify) Bone - Bone: RightHand" uses potentially thread-unsafe call "TryGetPawnOwner".`
> (Identical pair of warnings on the **LeftHand** node.)

**What this means:** somewhere during the hand-IK rewiring, the RightHand and LeftHand `Transform (Modify) Bone` nodes ended up with a *live* socket lookup wired directly into the AnimGraph — calling `Get ThirdPersonWeaponMesh` and `Try Get Pawn Owner` right there, instead of reading the `RightHandRot`/`LeftHandRot` variables that the EventGraph already computes safely every frame (via `Get Socket Rotation` + the `Combine Rotators` offset). Unreal's animation system runs the AnimGraph on a worker thread when it can, and object-pointer getters like these aren't guaranteed safe there — when the threaded path can't evaluate them reliably, the node falls back to stale or default data for that frame. **That's very likely the "sometimes fine, sometimes not" behavior seen in playtests** — it's not random, it's a threading race.

**The fix (editor work, not something I can do from here):**
1. Open `ABP_InfantryTripo3D` → AnimGraph.
2. Select the `Transform (Modify) Bone - Bone: RightHand` node. Trace what feeds its Rotation pin.
3. If you find a `Get Third Person Weapon Mesh` → `Get Socket Rotation`/`Get Socket Location` chain wired directly into that pin (rather than the `RightHandRot` variable), delete that chain and wire the pin to the `RightHandRot` variable instead — the one already being computed in the EventGraph.
4. Repeat for the `LeftHand` node with `LeftHandRot`.
5. While you're in there, check the two `Two Bone IK` nodes' Effector Location pins for the same pattern — the warnings only named the Transform (Modify) Bone nodes, but it's worth confirming the IK nodes are reading `RightHandLoc`/`LeftHandLoc` and not also holding a live call.
6. Compile — the two warnings should disappear from the Compiler Results panel. That's your confirmation the fix landed, independent of visual testing.
7. PIE test the idle "looking back and forth" state specifically, since that's where the bug was originally reported.

This is worth doing before any playtest — it's the single most visible bug in the build right now.

---

## 2. Textures — what's actually finished vs. placeholder

Checked every garrison prop's material assignment and every material's texture map count directly.

### The player character (highest priority)
**`Chaos_Armor_basecolor_Mat`** — the material every player sees on their own third-person body — has **only a base color texture**. No normal map, no roughness map, no metallic map. It'll read as flat and plastic-looking under any real lighting, especially compared to the NPCs (see below). This is the single most-seen surface in the game and it's the least finished one.

### NPCs — actually already done
Checked Rhodes, Bricks, Static, and Ms. Idris: each has a full 4-map set (BaseColor, Metallic, Normal, Roughness) from their Tripo3D generation. **These don't need texture work.** Worth knowing so effort doesn't get wasted re-doing something that's already finished.

### Garrison props — placeholder, and it shows
Checked all 11 core garrison props (`SM_Bunk`, `SM_Chair`, `SM_CommsConsole`, `SM_Desk`, `SM_Locker`, `SM_MessTable`, `SM_VendingMachine`, `SM_WeaponRack`, `SM_Dock_Crane`, `SM_Ship_Hull`, `SM_Truck_Cargo`). Eight of the eleven — bunk, chair, comms console, desk, locker, mess table, vending machine, weapon rack — all share **one single material**, `M_AI_Furniture`, which itself uses **one single base-color texture** (`T_Furniture_WoodMetal`) with roughness/metallic set to flat constants, not maps. That means a bunk, a desk, a locker, and a weapon rack all render with identical, un-textured-looking surfaces — no per-object variation, no surface detail at all. The crane, ship hull, and truck are in the same boat with their own one-texture-each materials (`M_AI_Crane`, `M_AI_Ship`, `M_AI_Vehicle`).

Everything here lives in a folder literally named `LevelPrototyping/AITextures` — this was always meant as placeholder work, not shipped quality.

### What's already properly built (don't touch)
The M1 District and M1 Landfall prop sets (bakery sign, deterrent emplacement, evac bus, siege gun, stretcher, tide-mark ring, the evacuee character) all have full basecolor/metallic/normal/roughness/rm texture sets already. Only the *garrison's own* original prop set and the player's own armor are unfinished.

---

## 3. Recommended order

1. **Fix the hand-IK thread-safety wiring** (§1) — five-minute editor fix, resolves a real, previously-unexplained bug.
2. **Texture the player's own armor** (§2) — highest visibility, currently the worst-looking asset in the build.
3. **Texture the 8 shared-material garrison props**, or at minimum give the weapon rack, desk, and comms console (the ones players interact with directly) their own dedicated maps before the rest.
4. Crane / ship hull / truck are set-dressing in the background — lower priority for a first playtest pass.

Let me know if you want help with anything beyond this list — I can't paint textures or author animation curves myself, but I can keep auditing, write any further C++ hooks needed, or check specific fixes once you've made them.
