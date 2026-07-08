# Weapon Handling + Aim-Down-Sights — Editor Wiring

*Ported from the Unity WeaponRig/AdsSettings/WeaponViewProfile design to Unreal C++ (2026-07-07). The code is built and pushed; the steps below are the in-editor content that makes it play-ready.*

## What the code already does

- **`FIBAdsSettings`** (in `Combat/AdsSettings.h`) — per-weapon ADS tuning (zoom, sight distance, hip/ADS spread, move-speed, scope). Lives on `UWeaponDataAsset` as the `Ads` field. Existing weapon assets got sensible defaults automatically.
- **`UWeaponRigComponent`** (`Combat/WeaponRigComponent.*`) — poses a first-person weapon mesh under the camera. **Hip:** the weapon's `Grip` socket snaps to an authored hip anchor. **ADS:** the `Aim` socket is pulled onto the camera's forward axis, so sight alignment is exact for any weapon with zero rig tuning. Smoothly blends 0→1, driving FOV, spread, move-speed, and (for snipers) a scope-overlay signal.
- **`AIBCharacter_Infantry`** is now **first-person**: a `FirstPersonCamera` at eye height, an owner-only `WeaponMesh`, and the rig wired up in BeginPlay. Hold-to-aim is bound to an `AimAction`; look sensitivity scales with zoom; move-speed drops while aiming.
- **`UHitscanWeaponComponent`** reads the rig's current spread at fire time (hip loose, ADS tight), applied server-side so it stays authoritative.

## The core principle (so you fix problems the right way)

**If a weapon looks held wrong, you move the socket on the weapon mesh — never touch rig code or numbers.** Grip/Aim/Muzzle are authored on the mesh; the rig just aligns to them.

## Steps in the editor (~15 min)

### 1. Rebuild + open
The C++ is already compiled. Just open the project (`IronBreach.uproject`). If it asks to compile, say yes.

### 2. Create the Aim input action
- In `Content/Input/Actions/`, create an Input Action **`IA_Aim`** (Value Type: Digital/bool).
- Open **`Content/Input/IMC_Default`** → add a mapping for `IA_Aim` → bind to **Right Mouse Button** (and Gamepad Left Trigger if you want controller support).

### 3. Point the character at it
- Open the infantry player Blueprint (the one the game mode spawns — `BP_IBCharacter_Infantry` in `Content/Sandbox/`, the pawn you saw respawn in PIE).
- In Class Defaults → **Input** category → set **Aim Action** = `IA_Aim`. (Move/Look/Fire should already be set.)

### 4. Give it a weapon mesh + sockets
- Still on the infantry BP, select the **WeaponMesh** component → set **Static Mesh** = `Content/Weapons/Rifle/Meshes/SM_Rifle`.
- Open **SM_Rifle** in the Static Mesh editor → add three sockets:
  - **`Grip`** — at the trigger/grip, +X pointing down the barrel.
  - **`Aim`** — exactly at the rear sight / iron-sight notch, +X down the barrel. *This is the one that must be precise — it's what lands on screen centre when aiming.*
  - **`Muzzle`** — at the barrel tip (used later for muzzle flash / tracer origin).
- Socket names are configurable on the WeaponRig component if you prefer different names, but `Grip`/`Aim`/`Muzzle` are the defaults.

> If you skip the sockets, the weapon still works — it just aligns to the mesh root (looks roughly held, sights won't be perfectly centred). The rig logs a warning naming the missing sockets.

### 5. Tune per weapon (optional)
- Open **`Content/DA_EnemyRifle`** (or your player weapon DA) → the **ADS** section:
  - `Zoom Multiplier` — 1.35 rifle, 1.15 shotgun, 4+ sniper.
  - `Ads Time` — raise time in seconds (0.22 default).
  - `Aim Point Distance` — cm the weapon sits in front of the camera at ADS.
  - `Hip/Ads Spread Degrees` — accuracy cone; ADS should be much tighter.
  - `Move Speed Multiplier` — how much you slow while aiming.
  - Snipers: tick `Use Scope Overlay` + `Hide Weapon In Scope`.

### 6. Test
PIE (single player is fine). Hold RMB → weapon raises onto the sights, FOV zooms, movement slows, spread tightens. Release → returns to hip. Tune the hip anchor on the WeaponRig component and the `Aim` socket until it feels right.

## Notes / known gaps

- **Scope overlay** fires an event (`OnScopeOverlayChanged`) but there's no full-screen scope widget yet — wire a UMG widget to that event for snipers later.
- **First-person arms**: `SM_Rifle` alone floats without hands. Add an FP arms skeletal mesh + animation later; the rig poses whatever mesh you give it. For now the rifle-only viewmodel is enough to feel the ADS.
- **Networking**: the rig is local-cosmetic (each client poses its own viewmodel); spread is applied server-side; move-speed replicates via CMC. No replication work needed.
- The third-person body mesh is hidden for the owning player (`SetOwnerNoSee`) so you don't see your own body from inside the head — remote players still see your full character.

*Want me to drive any of these editor steps? The socket authoring and IA creation I can do via screen control — just say which.*
