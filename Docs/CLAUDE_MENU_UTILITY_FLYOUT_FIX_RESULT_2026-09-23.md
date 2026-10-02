# Squad flyout layout correction (September 23, 2026)

Narrow fix from `Docs/CLAUDE_UTILITY_REVIEW_AND_GARRISON_NEXT_2026-09-23.md`. Two files, one screen.
No build, no process, no save, no git or lock operation, no asset or map change, no test code.

**Not built, not run, not captured.** Everything below is a claim about geometry in the code and
measurements of your captures, not about a frame anyone has seen since the change.

---

## 1. What your captures actually show

I measured `1280/Saved/MenuConsistency/after/friends.png` and the 1600 equivalent rather than
eyeballing them, converting both back into the 1600 x 900 design space the sheet is authored in.

The two agree to within a pixel — card edges at design x 65, 93, 252, 280, 323, 448, 517, 642, 711,
836, 905, 1030 in both. That is worth stating on its own: **the fault is in the layout, not in the
fit.** The `ScaleBox` that maps 1600 x 900 onto the window is uniform and doing its job; the row is
in the wrong place before scaling, which is why it reproduces identically at both sizes.

| | Seat row, design space |
|---|---|
| `squad.png`, flyout closed | spans x 198 → 1400, width **1202**, centre 799 in a body that runs 44 → 1556, centre 800 — centred to within a pixel |
| `friends.png`, flyout open | spans x **−137** → 1065 |

So the row moved **335 units left**, not the 180 that centring inside a 360-unit right padding would
give. Seat 0 occupies −129 → 49, which leaves **49 of its 178 units on the sheet: 72% of the first
card is gone.** The seat carrying the selected origin mark is seat 0 in the harness run, so the mark
went with it — exactly as you reported.

I did not reverse-engineer why Slate's centre alignment produces 335 rather than 180. That is the
real lesson here: the arrangement depended on an alignment rule I had assumed rather than measured,
and a fix that depends on the same assumption would be a coin toss at the next resolution.

---

## 2. The fix

The row is a fixed 1202 design units of card. It cannot be shoved sideways to make room — so it is
no longer shoved. It is **fitted**.

`BannerRow` now sits inside a `UScaleBox` (`ScaleToFit`, `DownOnly`) whose overlay slot is
`HAlign_Fill`. Filling removes the centring arithmetic entirely: the box is handed exactly what the
padding leaves, and `ScaleToFit` guarantees its content lands inside that. Whatever the available
width turns out to be, all six cards are in it — by construction, not by a number being right.

- **Flyout closed** — reserve 0, available 1512, row 1202. `DownOnly` clamps the scale at 1.0, the
  slot centres it, and the arrangement is byte-for-byte the authored one. That is the "restore the
  ordinary full-size arrangement" requirement satisfied by arithmetic rather than by a second code
  path.
- **Flyout open** — reserve `340 + 8 + 24 = 372` (frame width, its inset from the sheet edge, and a
  gutter), available 1140, scale 1140 / 1202 ≈ **0.948**. The cards lose about five percent and the
  row runs 44 → 1184 against a flyout that starts at 1208.

The three constants now live in one place next to `SeatDrop`, and the flyout's own `SetWidthOverride`
and slot inset read from them, so the reserve and the panel cannot drift apart the way a literal 340
and a literal 360 already did.

Nothing is clipped, no seat is dropped, no seat goes back under the flyout, the order and the V are
untouched, and the origin mark survives: hover, focus and selection are all painted in each card's
own local geometry, so they scale with the card and stay on screen and on the correct seat.

### Why fitting rather than moving the flyout or shrinking the cards directly

Moving the flyout only trades which end overflows. Shrinking the cards by editing `ApplySize` would
change the closed arrangement too, and the closed arrangement is the one you have already approved.
Scaling a container leaves the authored sizes alone and only changes what happens in the one state
that is short of room.

---

## 3. Changed files

| File | Change |
|---|---|
| `Source/IronBreach/UI/IBFriendsScreen.h` | `UScaleBox` forward declaration; `SeatFit` member. |
| `Source/IronBreach/UI/IBFriendsScreen.cpp` | `FlyoutWidth` / `FlyoutInset` / `FlyoutGutter` / `SeatReserve` constants in `IBSquadLayout`; the row wrapped in `SeatFit`; `SetFlyoutOpen` reserves `SeatReserve` instead of a literal 360; the flyout's width and inset read from the same constants; `Components/ScaleBox.h` and `ScaleBoxSlot.h` included explicitly. |

`UScaleBox` with `ScaleToFit` + `DownOnly` + a `UScaleBoxSlot` alignment is the same construct
`IBMenuLayout::Begin` and `UIBMenuScreen::BuildHangarPage` already use to place every menu sheet, so
this is the existing mechanism applied one level down, not a new one.

---

## 4. Preserved

Six seats and `SeatDrop` untouched. Seat order untouched. Every rest, hover, focus and selection
treatment untouched — `IBPlayerBannerWidget` and `IBFriendRowWidget` are not in the changed-file
list. The flyout is still a separate panel, still opened by the SOCIAL chip and by any open seat's
`+`, still near-opaque, still clearing its origin mark on close and when a marked seat fills. The
bottom chip, the location card and every delegate are as they were. Line endings preserved: the
header stays LF, the source stays uniformly CRLF.

---

## 5. Limitations

- Nothing was built or run. The 0.948 figure is arithmetic on the design-space numbers in the file.
- **Hover, keyboard focus and real friends-presence states were not established by the offline
  screenshots, and I am not claiming them.** The harness moves no pointer, navigates no focus, and
  ran with Steam offline, so the flyout in those captures shows the LAN-mode message rather than
  rows. Selection is the one interaction state the automated route does reach, because the harness
  broadcasts `OnInviteClicked`.
- `ScaleToFit` derives its scale from both axes. The seat row's vertical slot is `VAlign_Center`, so
  the height ratio should be 1.0 and the width should drive the scale — but `SScaleBox` has its own
  desired-size handling and I have not run it. If the cards come back smaller than ~0.95, that is
  where to look.
- One stray `__pycache__` folder was created in `Scripts/` by a syntax check and this session cannot
  delete inside the mounted folder. It is parked at `Scripts/_to_delete/pycache_20260923` for you to
  remove; nothing references it.

Stopping here for your rebuild and recheck at both sizes.
