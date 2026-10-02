# Utility-menu visual finishing pass — result (September 23, 2026)

Bounded task from `Docs/CLAUDE_MENU_UTILITY_FINISH_2026-09-23.md`. Ten source files, all under
`Source/IronBreach/UI/`. No build, no process launch or control, no save operation, no git or lock
operation, no asset, map, config, gameplay, network, progression or garrison change. No crew-harness
work and nothing that recreates or stands in for `BP_Mech`.

**Nothing here has been built or run. Every visual claim below is a claim about the code, not about
a frame anyone has seen.** §6 has the capture routes; §7 says plainly which states those routes
cannot capture.

---

## 1. Changed files

| File | What changed |
|---|---|
| `UI/IBPlayerBannerWidget.h` / `.cpp` | Hover, keyboard-focus and selected states on the seat card. Rest paint is now recorded and re-applied rather than written straight to the card. Accept key fires the same invite the mouse does. |
| `UI/IBFriendRowWidget.h` / `.cpp` | Row-wide hover and focus surface with a lead edge, so the target is the whole line rather than the chip at the end of it. |
| `UI/IBFriendsScreen.h` / `.cpp` | Marks the seat an open flyout was raised from; moves the seat row clear of the flyout; flyout made near-opaque; bottom bar put on a chip. |
| `UI/IBSettingsScreen.h` / `.cpp` | Category strip, dossier section headings, flat chevron controls, value in service steel, roomier rhythm, footer rule. |
| `UI/IBSystemScreen.cpp` | Two command bands with shared section headings, exit control marked as one, spacing. |
| `UI/IBMechCrewQACheck.cpp` | Housekeeping only — the `NOTE` wording, per your correction. No behaviour change. |

---

## 2. Squad / Friends

### The three states, and what makes them tellable apart

The seat card had no hover, no focus and no selection at all — the September 19 report left exactly
this undone. All three now layer over whichever state the seat is already in (featured / filled /
empty), and none of them replaces it.

The trick is that `SetFromPlayerState` and `SetEmptySlot` no longer write the card's edge directly.
They record it — `RestOutline`, `RestOutlineThickness`, `RestAccent` — and `ApplyStateVisuals()` is
the single place any of it is applied. A hover that ends therefore restores exactly what the seat's
own state asked for, including a combat-trade color the interaction states know nothing about.

- **Hover** lifts the card edge toward the cold interaction white the backpack tiles already use, and
  thickens it. The edge keeps the seat's own hue underneath: a Breaker-red edge lifts to a lit
  Breaker red, not to cyan.
- **Focus** lifts it further *and* paints corner brackets, top-left and bottom-right — the same mark
  `UIBItemTileWidget::NativePaint` draws for the same job. One grammar across every focusable
  surface in the menus.
- **Selected** is the loudest edge plus the lit notch the active navigation tab wears, centred on the
  top edge. Deliberately a different mark from focus, because the focused seat and the selected seat
  are often not the same seat.

Focus is taken through `NativeOnAddedToFocusPath` / `NativeOnRemovedFromFocusPath` rather than
`NativeOnFocusReceived` / `NativeOnFocusLost`: both return `void`, so there is no `FReply` contract to
get wrong on a card that is only ever a focus target, and the pair also fires for a child, which the
friend row needs. All six seats are focusable, occupied ones included — reading the roster by
keyboard is the point, not only reaching the open seats.

`UIBMenuScreen::NativeTick` reasserts focus every frame while a menu is open, which would have made
this flicker. It does not: that reassertion is already guarded by `!HasKeyboardFocus() &&
!HasFocusedDescendants()`, so a focused seat keeps focus. Escape and the Q/E cycle still reach the
screen, because the seat's `NativeOnKeyDown` handles only the accept keys and returns `Super` for
everything else.

### Selection means one specific thing

`HandleInviteSlotClicked` already received the banner that raised the flyout and threw it away. It
now marks it. **This is a visual origin mark and nothing else.** Invites go to the session, not to a
seat; no code below that line reads the mark; and it is cleared when the flyout closes, when the
flyout is raised from the SOCIAL chip instead of a seat, and when somebody takes the seat.

### Two defects the current captures show

I read `Saved/MenuConsistency/after/{squad,friends,settings,system}.png` before changing anything.
Two things in them are not style questions.

**The flyout was landing on the sixth seat.** In `friends.png` the right-hand seat sits behind the
FRIENDS panel and its `+` reads straight through the glass. The centred seat row and the right-anchored
flyout share one overlay and simply collide. Two changes: the flyout fill goes to effectively opaque
(at 0.95 a bright cyan `+` on near-black still shows), and while the flyout is open the seat row
reserves the flyout's width on its right, so the row slides clear. Layout only — same six seats, same
order, all still clickable. Dimming the row instead would not have worked: `SIBHexBorder` paints with
custom verts and never multiplies by the widget style's tint, so `RenderOpacity` does not reach it.

**The privacy line was sitting on the brightest part of the screen.** `FIRETEAM PRIVACY · FRIENDS
ONLY` is small low-contrast type laid directly over the hangar floor's reflections. The bottom bar now
sits on the same chip surface the CURRENT LOCATION card uses, which also makes the two bottom corners
answer each other.

### Friend rows

The row carries the hover and focus reads for the whole 46 px line now, instead of only the JOIN /
INVITE chip at the end of it: a fill that deepens from hover to focus, plus a 3 px lead edge that
lights on focus. The row is **not** made focusable — it uses the focus-*path* pair so it lights when
its own action chip takes focus, which keeps one focus stop per row instead of two. Presence
semantics are untouched: dot color, name contrast, and ONLINE / IN IRON BREACH / OFFLINE all read as
before.

### Side effect worth knowing

`UIBLobbyStripWidget` builds the same banner widget, so the lobby strip inherits the same hover and
focus reads. Being focusable does not make a widget take focus on its own — Slate only grants focus
when a reply asks for it, and nothing in the lobby strip does — so this should be additive there. It
has not been run.

---

## 3. Settings

The existing sheet is sound; the problems are hierarchy and noise, both visible in `settings.png`.

**Thirty-two boxes.** Every `<` and `>` was a full outlined button. The chevron is now an
`IBMenuGlyph` mark in a button that is flat at rest and only draws its box under the pointer. The
control stays discoverable because the chevron itself is the affordance, and the sheet goes back to
reading as one surface. The disabled brush deliberately keeps its box: an unavailable control has to
look like a control rather than like empty space.

**Cyan was doing two jobs.** The headings were white display type and the values were cyan — the
inverse of the approved sheets, where cyan carries section titles and controls and values are service
steel. Headings are now the dossier treatment the character and mission pages already wear (lit
diamond, tracked cyan caps, hairline), values are `TextHi` one step larger than their label, and the
chevrons stay cyan. That leaves one honest rule on the page: **cyan is what you can act on.**

This is the one change here most worth a second opinion, and it is two lines if you disagree — the
value color in `MakeRow` and the heading treatment in `AddSection`.

**Category navigation.** Sixteen rows across two scrolling columns had no way to reach a heading
except by dragging. A VIDEO / AUDIO / CONTROLS strip above the columns now scrolls the owning column
to that heading and lights its chip. It **filters nothing**: no row is hidden, no value is touched,
both columns stay fully scrollable by hand. VIDEO owns the left column; AUDIO and CONTROLS share the
right one, which is why the strip maps to two scroll boxes rather than three.

**Rhythm.** 22 px above a heading and 8 below it (space above separates categories; space below only
pushes a heading off its own list), 10 px under the rule, 5 px per row, a roomier gutter inside each
card, a wider trough between them, and a hairline above the footer so RESET reads as acting on
everything rather than as one more row of the right column.

Every setting label, every value binding, both apply-and-save paths, the arrow handlers, the reset
handler and all four button states are unchanged. The sixteen labels are still QUALITY, WINDOW,
RESOLUTION, RENDER SCALE, VSYNC, FRAME RATE CAP, FIELD OF VIEW, BRIGHTNESS, FPS COUNTER, MASTER
VOLUME, MUSIC, EFFECTS, MOUSE SENSITIVITY, ADS SENSITIVITY, INVERT Y and AIM MODE.

---

## 4. System

Two bands, one heading each, in the same dossier treatment Settings now uses: everything above the
second heading keeps you in the session, everything below it takes you out of one. The destinations,
their order and every click path are unchanged.

QUIT TO DESKTOP gets a danger-tinted edge. In `system.png` it is rendering filled teal, the same
treatment as the accented RESUME, which makes the one irreversible control on the page look like the
primary one. Same geometry, same four states — only the edge changes, so it reads as the end of the
list rather than as a different kind of thing. The two-step arm, its amber `CONFIRM — QUIT?` label and
the disarm on reopen are all untouched, so the existing MenuConsistency assertions on those strings
still hold.

A hairline between the IRON BREACH mark and the live session line makes the brand read as a masthead
and the state below it read as state. The authored title Blueprint is not touched, the Personal /
Director split is not touched, and neither are Character single-click, fullscreen Watch or the XP
bindings — `IBMenuScreen.cpp` and `.h` are not in the changed-file list at all.

The two new section labels go through `NSLOCTEXT(...).ToString()` rather than a raw literal, so they
stay localized source strings on the way into the shared helper.

---

## 5. Housekeeping, per your corrections

**The crew `NOTE` no longer infers a missing asset.** It now reports the load result and only that —
`resolves — it is simply not placed in this map`, or `FAILED TO LOAD: the class did not resolve in
this run. Confirm on disk whether the package exists before concluding the asset is missing` — with a
comment saying why: a cook, path or dependency fault fails the same way. That the package is absent
is established separately, on disk. No other change to that file; still no `SpawnActor`, no occupancy
write, no `ClearTimer`, tallies still 6 and 13.

**`CLAUDE_MENU_CREW_QA_FIXTURE_RESULT_2026-09-22.md` §7 is corrected.** You were right on all three.

- The 20 s single-process preflight was described as a success check. It is not one and never was.
  The `NOTE` fires from exactly one branch — phase 0, *zero* frames, 20 s elapsed — so the preflight
  can only return a negative. A `NOTE` inside ~25 s means the map has no mech. **No** `NOTE` means a
  frame was found and the run then waits for a second human that will never arrive, silently, to its
  480 s hard stop; that is an inference from an absence, not a result, and the section now says so
  and says to kill the process.
- The direct listen URL now carries `?bIsLanMatch`, with a note that it is not decoration: every
  listen URL in the logs that actually carried a client has it, `IBHost` builds them that way, and the
  SteamNetDriver passthrough we have observed under `-NoSteam` was observed with it set. A hand-rolled
  command-line URL without it is unverified, not known-good.
- The "non-saving end to end" claim is gone. Dropping the deployment leg removes the `IBCharacters`
  and `Vault` writes we observed; it does not establish that nothing else writes during start-up, and
  no run has checked. Both absolute `-UserDir` sandboxes stay, and so does the before/after hash
  comparison.

The §1 summary line and the quoted snippet in that document were updated to match the new wording.

---

## 6. Capture routes

All four screens already have an automated route — `IB.MenuConsistencyCheck` shoots `system.png` at
t≈12 s, `settings.png` at t≈19, `squad.png` at t≈23 and `friends.png` at t≈26, into
`Saved/MenuConsistency/after/`. Those are the files I read for §2 and §3, so the new captures drop in
beside the old ones for a direct before/after.

`-IBMenuConsistencyAfterDeploy` starts it after `[DeploymentCheck] COMPLETE`. It is exclusive against
`-IBXPHeaderAfterDeploy` and `-IBCrewQAAfterDeploy`; passing two logs an Error and starts neither.

**1280 × 720:**

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1280 -ResY=720 -WinX=100 -WinY=60 -NoSplash -IBMenuConsistencyAfterDeploy -ExecCmds=DisableAllScreenMessages,IB.DeploymentCheck -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceMenus\qa-1280-utility-20260923.log"
```

**1600 × 900:** the same line with `-ResX=1600 -ResY=900` and its own `-abslog`. Both write into the
same `Saved/MenuConsistency/after/` folder, so copy the 1280 set aside before running the 1600 one if
you want to keep both.

Manually, without the harness: System is Escape; SETTINGS is on the System card; Squad is the SQUAD
tab or `F`; the friends flyout opens from the SOCIAL chip or from any open seat's `+`.

---

## 7. What those captures will and will not show

Read this before concluding a state is missing.

- **Selected will appear.** The check reaches the flyout by broadcasting `OnInviteClicked` on the
  first banner it finds, which is the path that now sets the mark. So `friends.png` should show one
  seat carrying the notch, the row slid left, and the panel opaque.
- **Hover will not appear.** The harness never moves a pointer, and it broadcasts `OnClicked`
  directly rather than clicking. No automated shot can contain a hover state.
- **Keyboard focus will not appear.** Nothing in the harness navigates focus.

Capturing hover or focus with `HighResShot` is awkward, because opening the console takes focus and
moves the pointer. I would review those two live rather than by screenshot: open Squad, run the
pointer along the seats and watch the edges lift, then arrow-key across them and watch the brackets
move; open Settings and run the pointer along a column of chevrons. That is a five-second check by
eye and a fight to capture.

---

## 8. Unresolved exact-art gaps

These are content decisions, not code, and none of them is blocking:

- Seat portraits are still a letter monogram on a flat block, and the empty seat is still a typed `+`
  rather than a drawn mark. The approved sheets show real portrait art in that well.
- The combat trade only reaches the seat's top accent bar. There is no trade insignia on the card.
- Settings has no authored control art. Everything is a `< value >` stepper, including the six
  genuinely continuous values (three volumes, two sensitivities, render scale, gamma). A real slider
  would suit those, but it needs a decision first about keeping the stepper alongside it for
  controller parity — a slider alone is worse on a pad.
- The IRON BREACH wordmark on System is engine display type, not the authored logo.
- State changes are instant. No motion, no hover or focus sound.
- Friend rows have no avatars; nothing fetches Steam avatar images today.

---

## 9. Preserved — checked, not assumed

Six seats (`UIBSessionSubsystem::FireteamSize()` untouched) and the intentional V arrangement
(`SeatDrop` untouched). Every existing click path, delegate and binding. All nine
`BindWidgetOptional` property names in `IBSystemScreen.h`, unrenamed — Shane's Blueprint bindings are
name-matched and renaming one breaks them silently. All sixteen Settings labels and their value
bindings, both apply-and-save paths, and every button's disabled brush. The Personal / Director split,
Character single-click, fullscreen Watch and the verified XP bindings — `IBMenuScreen.{h,cpp}` was not
touched. The MenuConsistency assertions that click by label text still resolve: no label text changed,
and the buttons that lost their text labels (the chevrons) were never searched for. Per-file line
endings preserved — `IBFriendRowWidget.*`, `IBPlayerBannerWidget.h`, `IBFriendsScreen.h` and
`IBSettingsScreen.h` are LF; the four changed `.cpp` files that were CRLF are still uniformly CRLF.
No new test code, no new console command, no new suite.

---

## 10. Limitations

- **Not built, not run, not captured.** No claim here is runtime-verified.
- The new focus-path and paint overrides follow patterns already in this module
  (`UIBItemTileWidget` for hover and bracket painting, `UIBMenuScreen` for focusable widgets), but
  `NativeOnAddedToFocusPath` and `NativeOnRemovedFromFocusPath` are used here for the first time in
  this project. The engine source is not on a folder I can read, so I verified those two signatures
  against public UE documentation rather than against `UserWidget.h` on your disk.
- The 360 px the seat row reserves for the flyout is derived from the flyout's own 340 px frame plus a
  gap, in the 1600-wide design space. It should leave the row roughly 40 px of clearance, but that is
  arithmetic on the numbers in the file, not something anyone has looked at.
- Moving Settings values from cyan to service steel is a judgement call that follows the approved
  references. If it reads worse in motion, it is one line.
- `UIBLobbyStripWidget` shares the banner widget and inherits the new states unreviewed.

Stopping here for your build and visual review.
