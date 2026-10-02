# Astra brief — the "why am I back on the title screen" line

*Paste-ready prompt for Astra (ChatGPT), Connor's visuals/UI lane. Written 2026-09-16 by Claude. Send it once the current menu redesign pass has landed — it touches the operative sheet.*

---

You are working in `D:\Unreal Games\IronBreach` (Unreal Engine 5.8, C++ + Blueprints). Read `Docs/MP_HARDENING_2026-09-15.md` §2 first.

**What exists now (do not rewrite it):** `UIBSessionSubsystem` (a GameInstance subsystem, `Source/IronBreach/Online/`) now remembers the last link failure a client suffered — the host went dark, the connection timed out, a build mismatch, a deployment that never landed. The engine already drops the client back onto the title map; the subsystem keeps the reason and exposes it as

```cpp
UFUNCTION(BlueprintCallable, Category = "IronBreach|Online")
bool ConsumeLastLinkFailure(FText& OutMessage);   // one-shot: true + the text the first time it is read after a failure
```

It also broadcasts `OnSessionStatusChanged(EIBSessionStatus::Failed, Message)` ~1.5 s after the title map loads, and in non-shipping builds prints the line with `AddOnScreenDebugMessage` as a floor.

**The task:** when the SELECT OPERATIVE sheet (`UIBCharacterSelectScreen`, `Source/IronBreach/UI/`) constructs, call `ConsumeLastLinkFailure`. If it returns true, show the message as a one-line status band on the sheet, in the sheet's existing typography and the destructive/alert colour the style kit already defines (`IBStyleKit.h` / `IBMenuLayout.h`), for 8–10 seconds or until the player clicks anything — whichever comes first — then fade it out. Examples of the text you will receive: `SQUAD LINK LOST - THE HOST WENT DARK`, `THE HOST CLOSED THE LINK`, `BUILD MISMATCH - RUN UPDATE_IronBreach.bat AND RETRY`, `DEPLOYMENT FAILED (ClientTravelFailure)`.

**Hard constraints:**
- Do not change any existing `UPROPERTY` names or delete widgets — Shane's Blueprint bindings depend on them.
- Do not touch `Source/IronBreach/Online/`, `Missions/`, `Items/`, `Mech/`, `Kaiju/` or `Combat/` — read only. The subsystem API above is final; if you need something else from it, write the request in `Docs/` instead of editing it.
- No new content assets: the sheet already self-builds in C++ with a zero-content floor; keep it that way.
- Do not invent extra failure strings or player data; display exactly the text the subsystem hands you.
- The band must never block input or leave the sheet in a UI-only input mode it did not already use.

**Acceptance checks (run them, paste the evidence):**
1. Two `-game -nosteam` instances on one machine (`MPTEST_HostLocal.bat`, then `MPTEST_JoinLocal.bat`). With the client in the world, Alt+F4 the host. The client lands on the title map and the sheet shows `SQUAD LINK LOST - THE HOST WENT DARK` in the band; the log contains `Session: network failure ConnectionLost on the client`.
2. Relaunch the client normally (no failure): the sheet shows no band (the message is one-shot).
3. `IB.FrontendStyleCheck` and `IB.MenuFlowCheck` still pass; screenshot the sheet with the band at 1280x720 and 1600x900 into `Saved/LinkFailureBand/`.
4. No commit or push; report the files you changed under `Source/IronBreach/UI/` and the log lines above.
