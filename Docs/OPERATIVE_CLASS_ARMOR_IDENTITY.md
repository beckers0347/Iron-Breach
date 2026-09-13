# Operative Class Armor Identity — visual kit v1

*Written 2026-09-12. Reference: `Source/IronBreach/Player/IBCharacterTypes.h`
(the actual `ClassColor()` / `ClassName()` / `ClassRoleLine()` / `ClassDescription()`
functions the game already ships) and `Docs/OPERATIVE_SELECT_WIRING.md` (trade
color used for HUD chips, rim lights, banner bars). This doc doesn't invent
new lore or colors -- it takes what's already coded and turns it into a
concrete "what to add to the armor" spec.*

## Why this approach

Three concept images came in, all built off the same base trooper suit --
same proportions, same plating language, just different helmets/finish. That's
the right instinct: one shared silhouette read from a distance (this is a
squad shooter, you ID a teammate's class from their back at 20m, not their
face), with class identity carried entirely by **color + a small number of
attached details**, not a different suit per class. So this spec is a set of
add-ons that layer onto ANY of the three base meshes, not a redesign of them.

**Proposed base -> class mapping** (my read of the 3 images against the
already-written role descriptions below -- flag if this is wrong, it's an
easy swap since the add-on kit is base-independent):

| Image | Read | Best fit |
|---|---|---|
| Heavier plating, weathered/cracked texture, dual thigh holsters, bulkier gear load | Front-line, most battle-worn | **Breaker** |
| Rounder helmet, smoothest plating, most visible glowing chest/knee lights (reads "resonant/humming") | Field-shaping, sonic-warfare | **Bellringer** |
| Angular multi-lens/compound-eye visor, most sensor-like helmet silhouette | "Sees it first," intel-focused | **Picket** |

## The shared grammar (applies to all 3)

Every class gets the exact same THREE attachment zones so the read stays
consistent no matter which base mesh it's on:

1. **Visor/optic strip** -- recolor the existing eye-glow to the trade color.
2. **Chest core light** -- the small chest emitter already on all 3 bases
   recolors to the trade color (this is the "at a glance across the room"
   tell -- it's front-facing and always visible).
2. **Shoulder pauldron insert** -- a small geometric badge/plate on the
   left pauldron only (keeps the right shoulder clean for weapon stock
   clearance), trade-colored, shape unique per class (below).
3. **Back/hip kit-tool silhouette** -- a physical prop clipped to the back
   or hip that reads as *what their kit ability actually does* -- this is
   the one teammates see constantly since you spend the whole match looking
   at backs, so it carries the most weight.

## Breaker -- "HOLD THE DOOR" · VANGUARD

> First through the breach, last off the line. Front anchor; breaks kaiju
> armor seams open for the fireteam.

- **Trade color:** breach red-orange -- engine value `(0.80, 0.32, 0.16)`
  linear, ~`#E8966F` as a flat sRGB swatch for concept art reference.
- **Shoulder insert:** a blunt chevron/ram-horn wedge shape -- reads as
  "impact," not decorative. Slightly proud of the pauldron surface, like a
  battering-ram plate bolted on.
- **Back/hip prop:** a compact hydraulic ram frame or reinforced knuckle
  cowling riding the forearm/back -- ties directly to RAM CHARGE (kit) and
  BULWARK DASH (the 0.35x damage-taken dash). Should look like *the thing
  that lets them tank a hit and keep moving forward*, not a weapon.
- **Wear bias:** this is the class that should look the most battle-worn --
  scuffed edges, a scorch mark or two, visibly reinforced (thicker) front
  plating relative to the other two.

## Picket -- "SEE IT FIRST" · RECON

> Forward sentry of the exclusion zones. Intel, precision damage, and the
> class that finds what's hidden.

- **Trade color:** uplink cyan -- engine value `(0.25, 0.75, 0.85)` linear,
  ~`#89E0EB` sRGB reference. (Convenient: this is close to the cyan already
  glowing in the concept art's visors -- if the multi-lens helmet image is
  kept as Picket's base, its visor may need little to no recolor.)
- **Shoulder insert:** a small radiating ring/aperture icon -- literally an
  eye/scope motif, echoing the multi-lens helmet.
- **Back/hip prop:** a slim grapple-line spool on one hip (LINE BOLT) and a
  flare canister rack on the other (LAMPLIGHT FLARE) -- both small, low-
  profile, nothing that reads as bulky since Picket should silhouette as
  the leanest of the three.
- **Wear bias:** cleanest, least battle-scarred plating of the three --
  this is the class that avoids taking hits, not the one that's been hit.

## Bellringer -- "SHAPE THE FIELD" · CONTROL

> Sonic-warfare corps. Shapes the battlefield -- denies ground, redirects
> kaiju, owns dungeon utility.

- **Trade color:** harmonic violet -- engine value `(0.58, 0.38, 0.88)`
  linear, ~`#C8A3EF` sRGB reference.
- **Shoulder insert:** a concentric ripple/radial-pulse disc -- a sound-wave
  motif (matches the existing `SM_DeterrentEmplacement` prop's "tripod
  acoustic horn array" language from the district Tripo3D prompts -- keep
  the sonic-warfare visual language consistent between operative and prop).
- **Back/hip prop:** a small backpack-mounted resonator module with 2-3
  short antenna/tuning-fork prongs -- ties to DETERRENT PYLON (the slow
  zone) and NULL STEP (glide). The glowing chest/knee lights already in the
  concept art are a strong head start here -- lean into them as "the suit
  itself hums."
- **Wear bias:** the most high-tech-looking of the three, precise machined
  edges rather than battle wear -- this is a specialist kit, not a front-
  line grunt's.

## Corpsman -- "BRING THEM HOME" · SUSTAIN *(locked, `ClassAvailable()` returns false -- not released yet)*

> The extraction specialist. Sustain, revive economy, and the rescue scoring
> the Breakwater decorates.

Not blocking anything today since there's no 4th base image and the class
isn't playable yet, but logging the identity now so it's consistent whenever
it ships:

- **Trade color:** medic green -- engine value `(0.30, 0.72, 0.42)` linear,
  ~`#95DDAB` sRGB reference.
- **Shoulder insert:** a simple cross/plus badge (clearest possible read at
  a glance -- "this person heals you").
- **Back/hip prop:** a stim-canister bandolier across the chest/hip and a
  stretcher-strap loop on the back (STIM LINE, SURGE CARRY).

---

## Tripo3D prompts (add-on props only -- not new suits)

Follows this project's established Subject + Detail + Style format
(`Docs/M1_DISTRICT_TRIPO3D_PROMPTS.md`). Generate these as small standalone
props sized to clip onto the existing armor at the shoulder/back socket,
same workflow as the district props: Text to 3D -> generate -> Refine (for
real PBR textures) -> Export FBX.

**Breaker shoulder ram insert** (target height ~15cm)
> A blunt angular ram-horn shoulder plate insert, breach red-orange power
> cell strip along one edge, thick beveled metal wedge shape, scuffed and
> scorched military hardware finish, small modular armor attachment,
> low-poly game asset style, mid-detail hero prop.

**Breaker back-mounted ram frame** (target height ~40cm)
> A compact hydraulic ram frame and reinforced knuckle cowling, exposed
> pistons and thick cabling, breach red-orange indicator light, worn dark
> steel, military exosuit attachment, low-poly game asset style, mid-detail
> hero prop.

**Picket shoulder scope insert** (target height ~12cm)
> A small radiating aperture/scope-ring shoulder plate insert, uplink cyan
> glowing rim, precise machined metal, minimal and low-profile military
> hardware, small modular armor attachment, low-poly game asset style,
> mid-detail hero prop.

**Picket hip grapple spool + flare rack** (target height ~20cm)
> A slim grapple-line spool and a small flare-canister rack mounted on a hip
> plate, uplink cyan status light, compact tactical hardware, low-profile
> military attachment, low-poly game asset style, mid-detail hero prop.

**Bellringer shoulder resonance disc** (target height ~14cm)
> A concentric ripple/radial-pulse disc shoulder plate insert, harmonic
> violet glow between the rings, precise machined sonic-emitter styling,
> small modular armor attachment, low-poly game asset style, mid-detail
> hero prop.

**Bellringer backpack resonator module** (target height ~35cm)
> A compact backpack-mounted resonator module with 2-3 short tuning-fork
> antenna prongs, harmonic violet glow at the base, precise machined
> sonic-warfare hardware, military exosuit attachment, low-poly game asset
> style, mid-detail hero prop.

*(Corpsman prompts intentionally omitted until the class actually ships --
easy to add from the identity spec above when it does.)*

## After generating

Same pipeline this project already uses for district props: Refine ->
Export FBX -> rename to match (`SM_ClassKit_Breaker_Shoulder.fbx`, etc.) ->
drop into a new `Content/IronBreach/Classes/Kits/` folder -> import and
socket-attach in the character Blueprint/C++ (`ApplyOperativeBody` already
swaps meshes on class change in `AIBCharacter_Infantry` -- the natural place
to also attach/detach these kit props per class). Happy to write the
Python/C++ wiring for the socket attachment once the meshes exist -- no
point guessing socket names before there's something to attach.

---

## v2 -- Destiny-style class garments (2026-09-12)

Follow-up after Shane clarified: not small attachment badges -- something
closer to how Destiny reads Titan/Hunter/Warlock at a glance. Worth naming
what Destiny is actually doing, since it's three specific, copyable design
moves, not just "give them different colors":

1. **A dedicated garment slot that never changes shape.** Titan Mark (hip
   cloth), Hunter Cloak (back cape), Warlock Bond (forearm wrap) are a
   separate equipment slot from the rest of the armor. Whatever else you
   unlock or re-skin, that one piece is always the class's shape -- so the
   class read survives every cosmetic system built on top of it later. This
   is worth being a real inventory/itemization concept here, not just a
   modeling choice -- see "Class Sigil slot" below.
2. **Cloth, not just plate.** The class item and a few other pieces are
   soft-body/cloth-simmed, so they move independently of the rigid armor --
   a cape drifting, a sash swaying, tassels bouncing on a run. That
   motion is a huge part of why a Hunter reads as a Hunter from 30m even
   before you can see color -- silhouette-in-motion, not just silhouette.
3. **Distinct proportions and material language per class**, independent of
   the garment: Titans are visually wider/squarer, mostly hard plate;
   Hunters are leaner with more exposed cloth/leather layered under lighter
   plate; Warlocks are asymmetric and robed, hard surface kept to
   shoulders/chest with the rest flowing fabric.

### Iron Breach equivalent -- a "Class Sigil" garment per operative

Same idea, translated to a breach/kaiju-hunter military setting instead of
Destiny's mystic-soldier one. Proposing one signature cloth/soft-body
element per class -- always that shape, colorable/patternable later the way
shaders reskin Destiny's class items without changing their silhouette.

**Breaker -- the Breach Sash.** A heavy diagonal bandolier of blast-panel
plates and chain, slung shoulder-to-hip like a demolitionist's charge belt.
Reads as "about to go through a door," which is exactly the class fantasy.
Stiffer cloth-sim than the others -- it should swing like something with
real weight, not flutter.

**Picket -- the Picket Cloak.** A low hood + short weather cape, the kind a
sentry standing watch for six hours actually wears -- muted, matte,
non-reflective, faint sensor mesh woven into the hood's edge (small
aperture glints, not obvious tech). This is the one that should look
almost mundane/functional next to the other three's more overt sci-fi
flourishes -- Picket's whole identity is "doesn't want to be seen."

**Bellringer -- the Cantor Stole.** A hanging bandolier of small tuned
resonator tubes across the chest, worn like a priest's stole/vestment --
literal bells for a class named Bellringer. These should be the one
genuinely unique animation hook of the four: the tubes physically swing and
audibly/visually pulse in sync with kit activations (DETERRENT PYLON /
NULL STEP), so teammates learn to recognize a Bellringer popping their kit
by sound and silhouette before they see the ability's VFX land.

**Corpsman -- the Field Smock.** *(locked class, same caveat as before)* A
half-apron of canvas and pouches over the chest/hip, tourniquets clipped
within reach, a faded cross marking -- the one class that should look
visibly less armored than the other three (bare forearms, lighter
plating), because "doesn't look like a combatant" is itself the read for
"this is who patches you up."

### Silhouette/material language per class (independent of the garment)

| Class | Proportions | Material bias |
|---|---|---|
| Breaker | Widest/squarest, thickest limbs | Heavy plate, chain, scorched dark metal |
| Picket | Leanest, lowest profile | Matte treated fabric over light plate, no reflective surfaces |
| Bellringer | Tallest/most asymmetric, antenna silhouette | Machined metal + glass/resonant crystal elements that glow |
| Corpsman | Bulkier at hip/chest (pouches), bare forearms | Canvas, strapping, brightest/cleanest of the four |

### Suggested itemization hook: a real "Class Sigil" slot

Since `UIBVaultSubsystem` / the per-operative vault already exists
(`Docs/OPERATIVE_SELECT_WIRING.md`), the garment above is a natural fit as
its own equipment slot -- always locked to the operative's class (can't
equip a Breach Sash on a Picket), re-skinned/re-colored by whatever
cosmetic unlock system comes later, but never reshaped. That's what makes
the class read survive the game's entire cosmetic lifetime instead of only
the launch armor set.

### Note for Connor: cloth sim

The "swings/sways independent of the rigid armor" effect is a real engine
ask, not just modeling -- these garment pieces want cloth simulation (UE's
Chaos Cloth on a cloth-painted skeletal mesh section, or a simpler
physics-asset-driven bone chain for something like the Bellringer's hanging
tubes if full cloth sim is more than this needs right now). Worth a short
conversation with Connor about which approach fits the existing
`ABP_Infantry` pipeline before committing art time to geometry that assumes
one or the other.

### Tripo3D note

Tripo3D generates rigid meshes, not simulation-ready cloth -- fine for the
Breaker's stiff plated sash or Bellringer's resonator tubes (those can be
close to rigid anyway), but the Picket cloak and Corpsman apron want actual
cloth topology, which means either a real cloth asset built by hand (or in
Marvelous Designer/Blender cloth sim and retopo'd) rather than an AI mesh
gen pass, or accepting a stiffer/lower-fidelity Tripo3D result for those two
specifically. Worth deciding per-garment rather than assuming one pipeline
covers all four.
