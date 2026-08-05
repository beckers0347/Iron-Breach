# SPEC — Animated Title Screen (L_TitleScreen)

*Owner: Connor. Status: gray-box in progress, 2026-07-29.*
*Supersedes the static-art menu (`Lvl_MainMenu`), which stays shipping-ready until this beats it.*

---

## 1. The pitch

The title screen is a real 3D scene, not a video or a static image. That buys us
responsive lighting, ultrawide/any-resolution support, live background events, and —
the important one — **a seamless camera move from the title into character select
without a hard cut.** Title, operative select, personal hangar and eventually the
Bastion should all read as one continuous physical place.

The shot: the Warden being prepared for deployment inside an enormous hangar, seen
low and from behind Defense Force soldiers. Not standing outdoors — a hangar lets
the camera continue naturally into the other menus.

---

## 2. Timing

### Intro — 8 to 12 seconds, plays once

| Time | Beat |
|---|---|
| 0–2s | Black. Deep reactor vibration. A thin cyan line scans across. Logo fades in. |
| 2–5s | Environment fades up. Camera low behind soldiers; the Warden looms above them through rain, steam, smoke. Reactor core powers on. |
| 5–8s | A dropship crosses overhead. Searchlights rake the mech. Camera pushes slowly forward. `PRESS ANY KEY` appears. |
| 8s+ | Hand off to the idle loop. |

### Idle loop — 30 to 60 seconds, repeats forever

The Warden is an enormous machine **at rest**. No large movements. The loop should be
hard to catch repeating, which comes from running effects on **independent cycles** of
different lengths rather than one long baked animation:

- very slow camera drift + slight handheld vibration
- reactor-core pulsing
- small head / shoulder settles, hydraulic pressure releases
- steam vents at irregular intervals
- technicians and soldiers walking below
- distant dropships crossing
- rain sliding past lens, searchlights sweeping fog
- cloth, cables, antennas in the wind
- occasional lightning silhouetting the mech

### Any-key transition — the moment that sells it

Do **not** cut to another screen. In order:

1. `PRESS ANY KEY` disappears
2. Logo shrinks and moves up
3. Camera begins its approach to the Warden
4. Hangar lights come on in sequence
5. Mech visor activates
6. Character-select UI fades in
7. **Background never changes location**

---

## 3. Architecture

```
L_TitleScreen
├── CineCameraActor        (~35–50mm, NOT a wide action lens)
├── Warden (SK_Mech)       hero, framed off-centre
├── Player silhouettes     foreground, low
├── Bastion hangar         only what the camera can see
├── Clouds / smoke / rain / steam
├── Dropships, searchlights
├── Lighting
├── LS_MainMenu            Level Sequence
└── WBP_MainMenu           UMG overlay
```

Three systems, cleanly separated:

- **Sequencer** — camera, mech motion, lighting, ships, environment events, audio
- **UMG** — logo, prompt, menu items, settings (its own animation tracks)
- **Blueprint** — input, transitions, level loading

Sequence is split conceptually so the Blueprint can loop only the back half:

```
Intro:      0–8s     (plays once)
Idle loop:  8–48s    (loops)
```

### Blueprint flow

```
BeginPlay
  -> Set View Target with Blend  (cine camera)   <- REQUIRED, see §5
  -> Create WBP_MainMenu -> Add to Viewport
  -> Play LS_MainMenu intro
  -> Enable input

AnyKey
  -> Lock further input
  -> Stop PromptPulse
  -> Play MenuReveal
  -> Play camera transition
  -> Show menu options

Select Operative
  -> Play TransitionOut
  -> Camera moves toward hangar
  -> Fade
  -> Load character-select level
```

### UMG animations

`LogoFadeIn` · `PromptPulse` · `MenuReveal` · `TransitionOut`

Keep it restrained. Do not slide every element in from a different direction.
First screen shows **only** the logo and `PRESS ANY KEY`; the rest (Continue,
Select Operative, Settings, Credits, Exit) appear after the any-key reveal.

---

## 4. Build order (do not skip ahead)

Prove the framing and the transition feel powerful **before** modelling the Bastion.

1. Gray-box, ~15s: placeholder mech, simple environment, one camera move, logo fade,
   any-key input, transition into character select
2. Then lighting, fog, particles, audio
3. Then the real hangar

A 2.5D layered version of the key art (foreground soldiers / fog / mech / city / sky,
animated for parallax) is a legitimate faster path to prove the mood — but the final
version is rebuilt fully in 3D for resolution independence, graphics settings,
armor/mech customisation, seasonal Bastion changes and live background events.

---

## 5. Gotchas already hit

- **The menu level has no floor.** On Play, the default pawn spawns and falls forever;
  it reads as "the mech is falling" but the mech is fine and the *camera* is dropping.
  Fix: `Set View Target with Blend` to the cine camera on BeginPlay. A menu GameMode
  with `DefaultPawnClass = None` is the cleaner long-term fix.
- **`SK_Idle_Anim` is not compatible with `SK_Mech`'s skeleton** — the Anim to Play
  dropdown offers only `None`. Needs a re-import against `SK_Mech_Skeleton`, or use
  `ABP_Mech`. Ref pose is acceptable for gray-box (machine at rest).
- **The logo is baked into `T_TitleScreen`.** UMG needs a separate transparent
  logo-only asset (~2048px wide) before the fade/shrink beats can work. Text
  placeholder until then.
- **`Set Input Mode UI Only` persists across level loads.** Any button that leaves the
  menu must first restore `Set Input Mode Game Only`, hide the cursor, and
  `Remove from Parent` — otherwise the next level loads but ignores all input, which
  looks exactly like a freeze. (Cost us a debugging session; see commit `637bf19`.)
- **Full-screen invisible buttons eat clicks** for whatever is underneath, including
  after the widget should be gone. Remove the widget, don't just hide it.

---

## 6. Open questions

- Character-select as a separate level, or the same level with a camera move and
  streamed-in geometry? The "one continuous place" goal argues for the latter.
- Does the idle loop keep running behind the character-select UI, or freeze?
- Menu music: single ambient bed, or stems that layer in as you go deeper?
- Do Host/Join live on the title screen, or inside the operative-select flow?
