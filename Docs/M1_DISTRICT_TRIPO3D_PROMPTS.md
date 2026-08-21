# M1 District — Tripo3D Generation Prompts

Ready-to-paste prompts for the 6 props `import_m1_district_ai_models.py` is
waiting on. I can't drive Tripo3D from this session myself right now — the
Claude in Chrome browser extension isn't connected, and even connected it
only automates Chrome (needs its own extension there), not Edge — so this is
written for you to run by hand in Edge. If you'd rather I drive it directly,
install the extension from claude.ai/chrome in Chrome, log into Tripo3D
there, and say the word next session; everything below still applies, it'd
just be me clicking instead of you.

Each prompt follows Tripo3D's own recommended structure — **Subject + Detail
Description + Style Definition** — since that's what their prompting guide
says the model responds to best.

**Every item: Text to 3D tab → paste prompt → generate → click Refine (this
is what gets you real PBR textures instead of an untextured clay mesh) →
Export → format FBX.** Tripo3D doesn't have a documented resize-to-real-
world-height or origin-at-base toggle the way Meshy does — don't worry about
matching an exact height at generation time, `import_m1_district_ai_models.py`
now checks the imported mesh's actual height against the target and tells
you the scale factor to plug in if it's off, and pivot/floating issues get
fixed by eye once the mesh is placed (same "verify once visible" approach
this project already uses everywhere else).

---

## 1. SM_EvacBus — target height 280cm

> A boxy civilian evacuation bus, worn olive-drab paint with a faded route
> number on the side, roof-mounted emergency light bar, mud-splashed lower
> panels, headlights on, doors open on one side, military-adjacent civil
> defense vehicle, low-poly game asset style, background prop detail level.

3 placed along the Dread street.

## 2. SM_DeterrentEmplacement — target height 450cm

> A squat military sonic deterrent emplacement, tripod-mounted acoustic horn
> array angled skyward, exposed thick cabling and a small generator housing
> at the base, weathered dark steel with warning stencils, industrial
> hardware silhouette, no organic parts, low-poly game asset style,
> mid-detail hero prop.

2 placed at the sea-wall gun line ("Bellringer" emplacements).

## 3. SM_SiegeGun — target height 350cm

> A fixed-mount garrison siege gun on a reinforced concrete pedestal, long
> barrel with a muzzle brake, riveted steel shield plate, ammunition crate
> stack beside the base, coastal defense artillery, weathered gunmetal
> finish, low-poly game asset style, mid-detail hero prop.

1 placed beside the deterrent emplacements at the gun line.

## 4. SM_BakerySign — target height 250cm

> A small weathered hanging shop sign on a wrought-iron bracket, painted
> wooden board reading a simple bakery motif (a loaf/pretzel icon, no
> legible text needed), chipped paint, rust streaks on the bracket, the
> awning it once matched now rolled down and dark, European high-street
> storefront detail, low-poly game asset style, background prop detail
> level.

1 placed at the carry route's first turn ("Left at the bakery, love").

## 5. SM_Stretcher — target height 50cm

> A military field stretcher, canvas fabric stretched between two wooden
> poles with folding aluminum legs, olive-drab canvas, worn leather carry
> straps, simple and functional field medical equipment, low-poly game asset
> style, background prop detail level.

1 placed at the hospital muster plaza.

## 6. SM_TideMarkRing — target height 80cm

> A curved fragment of painted armor plate, thick riveted metal with a
> single hand-painted ring motif in white paint slightly uneven from a brush
> not a stencil, weathered gunmetal base material, mech-scale armor plating
> detail, low-poly game asset style, background prop detail level.

1 placed at the sea-wall glimpse, near the kneeling frame silhouette. If this
one doesn't generate as a clean, recognizable "ring painted on plate" shape
after a couple of tries, don't burn more credits on it — it's genuinely
better as a decal or a simple painted texture applied in-editor to the
existing kneeling-frame placeholder than as its own AI mesh.

---

## After downloading each one

1. Rename to match the filename in the list below (Tripo's default download
   name won't match).
2. Move into `X:\IronBreach\Content\LevelPrototyping\AIModels_District\`
   (create the folder if it isn't there yet).
3. Filenames expected: `SM_EvacBus.fbx`, `SM_DeterrentEmplacement.fbx`,
   `SM_SiegeGun.fbx`, `SM_BakerySign.fbx`, `SM_Stretcher.fbx`,
   `SM_TideMarkRing.fbx`.
4. Run `import_m1_district_ai_models.py` in the editor, read the Output Log
   for any height-mismatch warnings, then re-run `build_m1_district.py` to
   swap the real meshes into the placeholder boxes.

## What's deliberately not on this list

PALAWAN and the Caryatid/Longstone frame. Both recur as named, specific
individuals across the whole campaign (KAIJU-CODEX.md, CARYATID-
architecture.md) — a single Tripo3D pass on either is very likely to produce
something the game is stuck looking at for its first act. Worth a real sculpt
or a dedicated, heavily-iterated art pass, not folded into this prop list.

Sources: [Tripo AI Export Formats](https://www.tripo3d.ai/tutorials/tripo-ai-export-formats) · [Tripo3D Prompting Tips](https://www.tripo3d.ai/blog/tripo-user-guide-i-tips-and-tricks-for-effective-prompting)
