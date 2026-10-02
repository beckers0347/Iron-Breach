# MP Test Day — the two-machine session with Shane

*2026-09-15 · by Claude (Fable 5) · board: un-01 / un-03 / uv-05 · gate: DEMO d5 ("2 players over Steam, host + join, 10 min with no hard crash")*

A second human has never joined an Iron Breach session. Everything below is built and
verified solo (PIE, `-game` instances, Steam listen-host with the deployment check), so the
point of this day is not to find out *whether* it works — it is to find out **what breaks with a
real second person on a real second machine**, write it down, and leave with d5 either checked
or with a short, specific bug list.

Read `Docs/MP_HARDENING_2026-09-15.md` first for what changed in the code this week (link-failure
messages, board cleanup, director hardening) so you recognise the new log lines.

---

## 0. Pass criteria (what "d5 checked" means)

| # | Must be true | Proof |
|---|---|---|
| 1 | Shane joins Connor's session over Steam (not LAN, not the same machine) | Shane's screen shows Connor's world; both logs show the join |
| 2 | Host log shows the **Steam** net driver, not the IP fallback | `SteamNetDriver_0 bound to port 7777` in Connor's log |
| 3 | 10 minutes of play with no hard crash on either machine | both games still running at T+10; no `Fatal`/`Assertion` in either log |
| 4 | Both players fight the same kaiju and both see ZONE SECURED | banner flips on both screens; `[Mission] Phase -> Secured` in the host log |
| 5 | Shane can leave and rejoin without Connor restarting | second join succeeds in-progress |

Anything else that breaks is a bug to file, not a reason to fail the gate.

---

## 1. Before the day (both machines)

1. **Same build on both machines.** The client/server handshake rejects a mismatch, and the
   game now says so (`BUILD MISMATCH - RUN UPDATE_IronBreach.bat AND RETRY`). Decide first:
   test the **committed** build or the working tree? Recommendation: commit + push the current
   working tree first (ux-06), build, cut a fresh sync pack (`README_FIRST.txt` — the one on
   disk is from 57324df, Sep 6, and predates the Watch v2 / net driver work), send it to Shane,
   and have him run `UPDATE_IronBreach.bat` **with Unreal closed**. Confirm with the visual
   check in README_FIRST: SELECT OPERATIVE sheet with the 3D preview after "Press Any Button".
2. **Steam running on both machines, two DIFFERENT accounts, friends with each other.**
   AppID 480 (SpaceWar) is shared by every UE developer on Earth — do not use console `IBJoin`
   (it grabs the first session it finds, which may not be yours). Use the friend / invite path.
3. **Launch with the log visible**: run `PLAY_IronBreach.bat` or add `-log` to the shortcut so
   a log window opens beside the game. Both machines. The file copy lands in
   `Saved/Logs/IronBreach.log` regardless.
4. Windows Firewall: first launch will prompt — allow on Private networks. Steam P2P relay
   handles NAT; no port forwarding is needed.
5. Have Discord/voice open on phones or a second device. You will want to say "now" a lot.
6. Print §5 (the triage sheet) or keep it open on a second screen.

**Do not** start a Multi-User Editing session on either machine that day. This is runtime
netcode, not the editor (collab conventions §2).

---

## 2. Rung 1 — PIE, Connor alone (15 min, the morning of)

Play dropdown → **Net Mode: Play As Listen Server**, **Number of Players: 2**, new editor windows.

- [ ] Both windows land in the world with a body each.
- [ ] Place / let the spawner bring `BP_Kaiju_Palawan`: the **client window sees 60 m**, not 1.8 m.
- [ ] Objective banner shows the same phase in both windows; kill the kaiju from the client window
      → **ZONE SECURED** on both.
- [ ] Loot: client picks up a drop → it appears in the client's inventory (I), toast plays.
- [ ] Log (editor Output Log, filter `[Mission]`): `Tracking kaiju`, `Kaiju ... down (0 remain)`,
      `Phase -> Secured`. One `down` line per kaiju, never two.

PIE uses the NULL online subsystem (LAN). It proves replication, not Steam. If anything fails
here it will fail worse over the internet — fix it before rung 2.

---

## 3. Rung 2 — two `-game` instances on Connor's machine (30 min)

Both instances **must** run with `-nosteam` (with Steam live the host listens on a Steam P2P
socket, not UDP 7777, and `open 127.0.0.1` can't reach it — see `NETCODE_RETROFIT_NOTES.md`).

```text
UnrealEditor.exe "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1280 -ResY=720 -nosteam -log
```
(or the packaged exe with the same flags; run the line twice for instances A and B.)

**A (host):** Press Any Button → SELECT OPERATIVE → DEPLOY. Wait for the world. Log must show
`Session: input mode reset...`, `IBHost: session live` and `LogNet: ... listening`.

**B (client):** `~` → `open 127.0.0.1`. B travels straight into A's world (no session object on
B's side — that is expected for this rung).

Checks, in order:

- [ ] B has a body, sees A's body moving, A sees B.
- [ ] B's operative identity lands (A sees B's callsign in the Squad tab, not "Player 2"): log on A
      `operative on station -> <callsign>`.
- [ ] **Late join reads the mission**: quit B, have A trigger the kaiju emergence, then `open
      127.0.0.1` again from a fresh B. B's banner must read the *current* phase (ENGAGED or
      SECURED), not SWEEP THE ZONE; the kaiju must be 60 m and its armor bar must match A's.
- [ ] Both shoot the kaiju; armor break FX / roar plays on **both**; organ pops register from B's
      shots (`FindOrganAlongShot` handles capsule hits — aim at the sacs).
- [ ] ZONE SECURED on both screens.
- [ ] B opens every menu (I, K, L, B, M, J, F, Esc) — nothing strands input.
- [ ] Board the mech from B (E near it) — B drives. Press F: **nothing happens on a client alone in
      the hull — known limitation, do not file** (VIRGIL holds the guns; see §6). E exits.
- [ ] A boards and drives, B boards → gunner seat; B fires from the seat (server-authoritative
      path) and hits; both press F within the window → seats swap; E exits each.
- [ ] **Vault**: B picks up an item, equips it, quits (Alt+F4). A's log: `Vault:` save line under
      B's key. Relaunch B, `open 127.0.0.1`: the item is still there.
- [ ] **Client drop while crewed**: B in the gunner seat, Alt+F4. A keeps driving; log on A:
      `disconnected while crewed (gunner)` and VIRGIL takes the seat. Then B in the HULL, Alt+F4:
      A must NOT lose the mech (log: `promoted to NAVIGATOR` if A was in the seat, or the hull
      simply empties and A can board it).
- [ ] **Host drop** (do this last, it ends the run): B in the world, A Alt+F4. B lands back on the
      title map and, about two seconds later, prints **`SQUAD LINK LOST - THE HOST WENT DARK`**
      (red line + status). B's log: `Session: network failure ConnectionLost on the client`.

---

## 4. Rung 3 — two machines over Steam (the real thing, 60–90 min)

### 4.1 Net driver proof (2 minutes, before anything else)

Connor: Press Any Button → SELECT OPERATIVE → DEPLOY. Open the log window and find the listen
line:

- `SteamNetDriver_0 bound to port 7777` → **good, continue.**
- `IpNetDriver_0 listening on port 7777` → **stop.** The Steam driver did not load. Check the
  startup log for `Mounting Engine plugin SocketSubsystemSteamIP` and any `LogSockets` errors;
  confirm `IronBreach.uproject` still lists `SocketSubsystemSteamIP` and that
  `DefaultEngine.ini` still has the `!NetDriverDefinitions=ClearArray` block under
  `[/Script/Engine.Engine]`. Remote joins will die at ClientTravel until this reads right.
- `LISTEN SOCKET FAILED - SQUAD CANNOT JOIN` on screen → new this week: the listen socket itself
  failed to open. Same checks; also make sure nothing else is bound to 7777.

Tick uv-05 on the board when the Steam line shows.

### 4.2 Path A — Connor hosts, Shane joins (the invite path)

1. Connor is in his world (DEPLOY from the sheet — that *is* hosting; there is no separate host button).
2. Shane at the title screen: Press Any Button → SELECT OPERATIVE → **DEPLOY into his own world
   first is fine** (everyone hosts their own world; joining tears it down — that is Path B).
   For Path A, have Shane stay on the sheet and use the **Steam overlay** (Shift+Tab → Friends →
   Connor → **Join Game**) — or Connor sends the invite from the overlay.
3. Shane's status line: `INVITE ACCEPTED - LINKING...` → `LINKED - DEPLOYING...` → world.
   Logs: Shane `IBJoin: travelling to host at steam.<id>...`; Connor `LogNet: Join succeeded: <name>`
   and `operative on station -> <Shane's callsign>`.
4. Both in the world: run the same checks as rung 2 §3 (body, callsign, kaiju scale, banner).

### 4.3 Path B — Shane deploys first, then joins (DestroyThen)

1. Shane: DEPLOY into his own world. Confirm he is hosting (his log shows the listen line).
2. Shane: F → Squad tab → Connor's row (**IN IRON BREACH**) → **JOIN**.
3. Shane's log must show `Session: tearing down the stale local session before the next step`
   *before* `IBJoin: travelling to host`. If the join fails with "session already exists", the
   teardown did not complete — note it and retry once.
4. Shane lands in Connor's world.

### 4.4 The 10-minute soak (start a timer)

- [ ] Patrol together, shoot enemies — enemies split aggro between the two of you.
- [ ] Kaiju emergence → EMERGENCE banner on both → ENGAGED.
- [ ] Both fight it: armor break (roar/FX on both), organ pops from both players' shots, EXPOSED,
      death → **ZONE SECURED on both screens** at the same moment. Host log: `[Mission] Phase -> Secured`.
- [ ] Loot: each of you picks up a drop; each sees their own toast and inventory update.
- [ ] Menus on Shane's machine: I, K, L, B, M, J, F, Esc. Shane equips something, opens Skills, spends
      a point if he has one (host validates: `UIBSkillComponent` log lines on Connor's machine).
- [ ] **The Watch**: Shane presses B → proposes a destination. Connor's card shows it as PROPOSED by
      Shane's callsign → Connor **CONFIRM & DEPLOY** → both screens play the 2.4 s drop together →
      both arrive → Connor B → CARROW-1 pin → return to the Watch → both arrive back.
- [ ] Mech: Connor boards (drives), Shane boards → gunner seat, fires, hits the kaiju/enemies; swap
      handshake (both F inside the window); each E out.
- [ ] Rejoin: Shane leaves via Esc → System → LEAVE (clean), then joins again via the Squad tab or
      overlay. Second join in progress succeeds (pass criterion 5).

### 4.5 Failure drills (each ends something — do them in this order, last)

1. **Client drop while crewed**: Shane in the gunner seat → Alt+F4. Connor keeps the mech; his
   log: `disconnected while crewed (gunner)`; VIRGIL backfills. Shane relaunches and rejoins.
2. **Proposer drops**: Shane proposes a destination on the Watch (do NOT confirm) → Alt+F4.
   Connor's card must clear (`[Watch] ... left the net with '...' proposed and unarmed — standing
   the board down` in the host log). New this week.
3. **Host drop**: Shane in the world → Connor Alt+F4. Shane: title map, then
   `SQUAD LINK LOST - THE HOST WENT DARK`. Shane's Steam overlay must no longer show him "in a
   lobby" (the stale entry is destroyed — `dropping the stale local session entry` in his log).
   Shane can then DEPLOY into his own world without a "session already exists" error.

---

## 5. Log capture + triage sheet

**After the session, both of you:** copy `Saved/Logs/IronBreach.log` to a shared folder as
`MPTest_2026-MM-DD_host.log` / `_client.log`. If the game was relaunched during the day, the
previous logs are `IronBreach-backup-<timestamp>.log` in the same folder — grab those too.

Lines worth grepping (host and client):

```text
SteamNetDriver_0 bound | IpNetDriver_0 listening | Mounting Engine plugin SocketSubsystemSteamIP
Session status:            (every front-end beat)
Session: network failure | Session: travel failure | dropping the stale local session entry
LogNet: Join succeeded | UNetConnection::Close | NetworkFailure | ConnectionTimeout
operative on station
[Mission]  [Watch]  [Mech]  Vault:  Kit:
Ensure | Assertion | Fatal | LogOutputDevice: Error
```

Triage sheet — one row per check above; fill it live, not from memory:

| Step | Expected | Host saw | Client saw | Log line (which log) | Verdict |
|---|---|---|---|---|---|
| 4.1 net driver | Steam line | | — | | |
| 4.2 join (Path A) | world, callsign | | | | |
| 4.3 join (Path B) | teardown then join | | | | |
| 4.4 kaiju → SECURED | both screens | | | | |
| 4.4 Watch propose/confirm/drop | both travel | | | | |
| 4.4 mech seat + swap | fires, swaps | | | | |
| 4.4 rejoin | lands | | | | |
| 4.5 drills 1–3 | per text | | | | |
| T+10 no crash | both alive | | | | |

Verdicts: PASS / FAIL / PARTIAL / NOT RUN. A FAIL with a log line is a bug; a FAIL without one
is a repro step for next time.

---

## 6. Known limitations — do not file these as bugs

- **A client alone in the hull cannot take the guns.** Seat/role state lives on the server and
  the legacy F role-swap is server-side; from a client the hull's F is a no-op and VIRGIL shoots.
  Two humans work (hull + seat, swap handshake); host + AI works. Board item to come (Mech/).
- **Progress is keyed to the host's save files.** XP, vault and skills earned in Connor's session
  are stored on Connor's machine under `<SteamId>#<OperativeId>` (vault v2 is the later pass).
  Shane's solo world has its own copies.
- **Late joiners do not see earlier loot toasts / roars** — they get the current state, not the
  history. The banner and the kaiju's armor/phase are correct.
- **Menus and title styling may differ between machines** if the Sep 12–15 menu passes were not
  committed before the sync pack (§1.1).
- **AppID 480** is shared: console `IBJoin` may find a stranger's session. Use invites.
- `-nosteam` instances (rung 2) have no session object on the client — the Squad tab will not show
  the host row; that is expected there and only there.

---

## 7. Afterwards

- Board (Celeste): tick uv-05 when the Steam line showed; un-01 when Shane joined and stayed;
  un-03 when the seat + swap ran with two humans; **d5** on the DEMO gate when §0 is all true.
- File every FAIL as a new mission item with the log line pasted in.
- Post both logs + the triage sheet in `Saved/MPTest/<date>/` (git-ignored) and tell the other
  Claude session the path — it can read the logs from there.
