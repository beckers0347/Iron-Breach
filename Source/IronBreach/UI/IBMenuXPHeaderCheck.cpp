// Opt-in regression check for the live menu header (IB.MenuXPHeaderCheck).
//
// Reads and redraws only. It never awards XP, never calls UIBXPSubsystem, and never writes
// the XP ledger, the operative roster, a vault, an inventory or any save game. See the
// isolation note below for exactly what it does touch and what it therefore cannot cover.
#include "CoreMinimal.h"
#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "UI/IBMenuSubsystem.h"
#include "UI/IBMenuScreen.h"
#include "Items/IBPlayerState.h"
#include "Blueprint/WidgetTree.h"
#include "Components/TextBlock.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Containers/Ticker.h"
#include "HAL/IConsoleManager.h"
#include "TimerManager.h"

namespace IBMenuXPHeaderCheck
{
/**
 * Does the menu header redraw when the player state's XP and level events arrive — in either
 * order — and again after the screen has been closed and reopened?
 *
 * WHY. UIBXPSubsystem::GrantXP broadcasts OnXPAwarded BEFORE OnXPLevelUp. The first reaches
 * the header through AIBPlayerState::HandleXPAwarded -> SetOperativeXP -> OnOperativeXPChanged
 * while OperativeLevel still holds the OLD value; the new level follows afterwards on
 * OnOperativeIdentityChanged. A header subscribed to XP alone redraws early and then shows a
 * stale LV until the next award or a reopen. On a client the two are separate RepNotifies and
 * their arrival order is not ours to assume, so both orders are checked here.
 *
 * ISOLATION. The check broadcasts the player state's own public change events — the same ones
 * replication and the award path raise — and watches the real UTextBlock in the open header.
 * No progression value is set: not XP, not level, not the roster, not the vault. The only
 * mutation is one text block's text, overwritten with a sentinel and restored whenever the
 * redraw under test did not already replace it.
 *
 * NOT COVERED, deliberately: the award -> delegate leg (GrantXP -> HandleXPAwarded ->
 * SetOperativeXP). Driving that writes the real XP save, and SetOperativeLevel would reach
 * SyncLevelToRoster -> SetCharacterLevel -> SaveRoster, so it is left to the runtime pass.
 *
 * PAGE CHOICE. Inventory (the Character page). UIBWatchScreen calls RefreshTabBanner() from
 * its own tick once a second, which would redraw the header whether or not the binding exists
 * and turn every assertion below into a false PASS. The control step guards against exactly
 * that: it plants the sentinel, raises nothing, and requires the sentinel to survive before
 * any real assertion is trusted.
 */
struct FRun
{
	int32 Passed = 0;
	int32 Failed = 0;
	float Waited = 0.f;
	bool bObservable = true;
	uint64 Id = 0;
	double StartedAt = 0.0;
	FTimerHandle Wait;
	FTSTicker::FDelegateHandle Watchdog;
	TWeakObjectPtr<UTextBlock> Probe;
	TWeakObjectPtr<AIBPlayerState> State;
	TWeakObjectPtr<UIBMenuSubsystem> Menu;
	FText Original;
};

/**
 * OWNERSHIP. ActiveRun is the one strong owner of the run state that is NOT a delegate
 * capture. Every callback below also holds a shared reference, but a delegate can be
 * destroyed in the middle of its own callback — clearing a repeating timer from inside it
 * does exactly that — so the state must never be left owned by delegates alone.
 *
 * IDENTITY. Callbacks can outlive their run: the watchdog is scheduled 20 s out and world
 * timers fire whenever they fire. A stale callback compares its run's Id against the live
 * one and touches nothing if they differ, so an old run can neither restore a newer run's
 * probe with its own remembered text nor release the newer run's guard.
 */
static TSharedPtr<FRun> ActiveRun;
static uint64 NextRunId = 1;

static bool IsCurrentRun(const TSharedRef<FRun>& Run)
{
	return ActiveRun.IsValid() && ActiveRun->Id == Run->Id;
}

/** Self-expiring, so a run stranded by a world teardown cannot lock the command out for the
 *  rest of the session. Identity above is what keeps the stranded run's late callbacks from
 *  touching whatever replaces it. */
static bool IsRunActive()
{
	return ActiveRun.IsValid() && FPlatformTime::Seconds() - ActiveRun->StartedAt < 120.0;
}

static const TCHAR* SentinelText() { return TEXT("IB XPHEADER PROBE"); }
static bool ShowsSentinel(const UTextBlock* Line) { return Line && Line->GetText().ToString() == SentinelText(); }

static void Check(const TSharedRef<FRun>& Run, bool bOK, const FString& What)
{
	if (!IsCurrentRun(Run)) { return; } // a superseded run does not report into a later one's log
	if (bOK) { ++Run->Passed; } else { ++Run->Failed; }
	UE_LOG(LogIronBreach, Display, TEXT("[XPHeader] %s %s"), bOK ? TEXT("PASS") : TEXT("FAIL"), *What);
}

static void Note(const FString& What)
{
	UE_LOG(LogIronBreach, Display, TEXT("[XPHeader] SKIP %s"), *What);
}

static void Complete(const TSharedRef<FRun>& Run)
{
	// A callback that outlived its run reports nothing and cleans up nothing: the run it is
	// holding is not the one that owns the probe or the guard any more.
	if (!IsCurrentRun(Run)) { return; }
	// Never leave the probe on screen, whatever happened above.
	if (UTextBlock* Line = Run->Probe.Get())
	{
		if (ShowsSentinel(Line)) { Line->SetText(Run->Original); }
	}
	// Hand the world back as it was found: this runs in a live gameplay map, where an open
	// menu would leave the player in UI-only input. CloseMenu() no-ops when nothing is open.
	if (UIBMenuSubsystem* Menu = Run->Menu.Get()) { Menu->CloseMenu(); }
	// Cancel this run's watchdog rather than leaving it to fire into a later run's session.
	if (Run->Watchdog.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(Run->Watchdog);
		Run->Watchdog.Reset();
	}
	ActiveRun.Reset();
	UE_LOG(LogIronBreach, Display, TEXT("[XPHeader] COMPLETE: %d passed, %d failed"), Run->Passed, Run->Failed);
}

/** Last-resort probe cleanup.
 *
 *  The control step plants the sentinel and verifies it 0.6 s later, and the whole sequence
 *  runs on WORLD timers. A travel, a teardown or an early return between those two points
 *  would leave the probe text sitting on the menu screen — and menu screens are cached by
 *  UIBMenuSubsystem, a LOCAL PLAYER subsystem, so one can outlive the world its timers died
 *  with. This rides the CORE ticker, which outlives both, and fires once regardless. */
static void ArmSentinelWatchdog(const TSharedRef<FRun>& Run)
{
	Run->Watchdog = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([Run](float) -> bool
	{
		Run->Watchdog.Reset(); // it is firing; there is nothing left for Complete() to cancel
		// Stale: a later run owns the probe and the guard now, and restoring THIS run's
		// remembered text over it would corrupt the newer run's control step.
		if (!IsCurrentRun(Run)) { return false; }
		if (UTextBlock* Line = Run->Probe.Get())
		{
			if (ShowsSentinel(Line))
			{
				Line->SetText(Run->Original);
				UE_LOG(LogIronBreach, Warning, TEXT("[XPHeader] probe text outlived the run; restored by the watchdog."));
			}
		}
		ActiveRun.Reset(); // this run was stranded — let a later invocation start
		return false; // one shot
	}), 20.0f);
}

/** The header's identity line, "LV {n}   {CLASS}". Found by what it reads, the way the other
 *  menu checks find widgets — no private access — and reported ambiguous rather than guessed. */
static UTextBlock* FindRankLine(UUserWidget* Screen, int32& OutMatches)
{
	OutMatches = 0;
	UTextBlock* Found = nullptr;
	if (Screen && Screen->WidgetTree)
	{
		Screen->WidgetTree->ForEachWidget([&Found, &OutMatches](UWidget* Widget)
		{
			if (UTextBlock* Text = Cast<UTextBlock>(Widget); Text && Text->GetText().ToString().StartsWith(TEXT("LV ")))
			{
				++OutMatches;
				if (!Found) { Found = Text; }
			}
		});
	}
	return Found;
}

/** Plant the sentinel, raise one event, report whether the header redrew, and put the original
 *  text back if it did not — a failing assertion must not leave the probe on screen. */
static void Raise(const TSharedRef<FRun>& Run, bool bIdentityEvent, const FString& What)
{
	if (!IsCurrentRun(Run)) { return; } // a superseded run does not touch the live probe
	if (!Run->bObservable) { Note(What + TEXT(" — no trustworthy probe on this page")); return; }
	UTextBlock* Line = Run->Probe.Get();
	AIBPlayerState* PS = Run->State.Get();
	if (!Line || !PS) { Check(Run, false, What + TEXT(" — header or player state went away")); return; }

	Line->SetText(FText::FromString(SentinelText()));
	if (bIdentityEvent) { PS->OnOperativeIdentityChanged.Broadcast(); }
	else { PS->OnOperativeXPChanged.Broadcast(); }

	const bool bRedrew = !ShowsSentinel(Line);
	Check(Run, bRedrew, What);
	if (!bRedrew) { Line->SetText(Run->Original); }
}

static void RunSequence(UWorld* World, UIBMenuSubsystem* Menu, const TSharedRef<FRun>& Run)
{
	Run->Menu = Menu;
	ArmSentinelWatchdog(Run);
	TWeakObjectPtr<UIBMenuSubsystem> M(Menu);
	auto At = [World](float Time, TFunction<void()> Fn)
	{
		FTimerHandle T;
		World->GetTimerManager().SetTimer(T, FTimerDelegate::CreateLambda(MoveTemp(Fn)), Time, false);
	};

	// Inventory is the Character page: it builds the shared header and, unlike the Watch, has
	// no tick of its own that would redraw it behind the check's back.
	At(0.1f, [M] { if (M.IsValid()) { M->OpenScreen(TEXT("Inventory")); } });

	At(1.5f, [M, Run]
	{
		UIBMenuScreen* Screen = M.IsValid() ? M->GetActiveScreen() : nullptr;
		int32 Matches = 0;
		UTextBlock* Line = FindRankLine(Screen, Matches);
		if (!Line)
		{
			Run->bObservable = false;
			Note(TEXT("no \"LV n\" line in the open header — nothing to observe"));
			return;
		}
		if (Matches > 1)
		{
			Run->bObservable = false;
			Note(FString::Printf(TEXT("%d widgets read \"LV \" on this page; the probe is ambiguous"), Matches));
			return;
		}
		Run->Probe = Line;
		Run->Original = Line->GetText();
		AIBPlayerState* PS = Run->State.Get();
		// The header is the only listener on OnOperativeXPChanged, so IsBound() reflects it
		// exactly. OnOperativeIdentityChanged is deliberately not asserted this way: the
		// inventory screen is a second, unrelated listener on that one.
		Check(Run, PS && PS->OnOperativeXPChanged.IsBound(), TEXT("header is subscribed while the screen is open"));
	});

	// Control: no event is raised, so the sentinel MUST survive. If it does not, this page
	// redraws its header on its own and every assertion after it would be meaningless.
	At(2.0f, [Run]
	{
		if (!IsCurrentRun(Run) || !Run->bObservable) { return; }
		if (UTextBlock* Line = Run->Probe.Get()) { Line->SetText(FText::FromString(SentinelText())); }
	});
	At(2.6f, [Run]
	{
		if (!IsCurrentRun(Run) || !Run->bObservable) { return; }
		UTextBlock* Line = Run->Probe.Get();
		const bool bHeld = ShowsSentinel(Line);
		Check(Run, bHeld, TEXT("control: the header does not redraw on its own between events"));
		if (!bHeld) { Run->bObservable = false; Note(TEXT("remaining assertions cannot be trusted on this page")); }
		else if (Line) { Line->SetText(Run->Original); }
	});

	// The real award order: XP first, then the level.
	At(3.0f, [Run] { Raise(Run, false, TEXT("award order: XP event redraws the header")); });
	At(3.5f, [Run] { Raise(Run, true, TEXT("award order: level event redraws the header (the stale-LV regression)")); });

	// A client may see the two RepNotifies the other way round.
	At(4.0f, [Run] { Raise(Run, true, TEXT("client order: level event redraws the header")); });
	At(4.5f, [Run] { Raise(Run, false, TEXT("client order: XP event redraws the header")); });

	At(5.0f, [M] { if (M.IsValid()) { M->CloseMenu(); } });
	At(5.6f, [Run]
	{
		AIBPlayerState* PS = Run->State.Get();
		Check(Run, PS && !PS->OnOperativeXPChanged.IsBound(), TEXT("header unsubscribes when the screen closes"));
	});

	// Screens are cached and reused (UIBMenuSubsystem::GetOrCreateScreen), so a reopen has to
	// rebind the same widget object rather than rely on a binding that survived the close.
	At(6.0f, [M] { if (M.IsValid()) { M->OpenScreen(TEXT("Inventory")); } });
	At(7.0f, [M, Run]
	{
		int32 Matches = 0;
		UTextBlock* Line = FindRankLine(M.IsValid() ? M->GetActiveScreen() : nullptr, Matches);
		if (Line && Matches == 1) { Run->Probe = Line; Run->Original = Line->GetText(); }
		Raise(Run, true, TEXT("reopened screen is rebound: level event redraws the header"));
	});
	At(7.5f, [Run] { Raise(Run, false, TEXT("reopened screen is rebound: XP event redraws the header")); });
	At(8.0f, [Run] { Complete(Run); });
}

static FAutoConsoleCommandWithWorld Start(TEXT("IB.MenuXPHeaderCheck"),
	TEXT("Check that the menu header redraws on XP and level events in both orders and after a reopen. Reads only; writes no save data."),
FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
{
	if (!World || !World->IsGameWorld()) { return; }
	if (IsRunActive())
	{
		Note(TEXT("a run is already in progress; ignoring this invocation"));
		return;
	}
	const TSharedRef<FRun> Run = MakeShared<FRun>();
	Run->Id = NextRunId++;
	Run->StartedAt = FPlatformTime::Seconds();
	ActiveRun = Run; // strong ownership that no delegate destruction can take away
	TWeakObjectPtr<UWorld> W(World);

	// Poll rather than assume a moment: -IBXPHeaderAfterDeploy starts this from
	// IBDeploymentCheck's COMPLETE branch, on the settled Carrow Gate world, and the poll
	// absorbs whatever settling is left.
	World->GetTimerManager().SetTimer(Run->Wait, FTimerDelegate::CreateLambda([W, Run]()
	{
		// OWNERSHIP, and the reason this check crashed once already. Clearing a REPEATING
		// timer from inside its own callback destroys the FTimerData that owns this very
		// lambda, and with it the captured shared reference — which, once the console
		// command returned, was the only strong reference to the run state. Everything after
		// the clear then ran on freed memory. Take a strong copy onto THIS stack frame before
		// anything can clear the timer, and use it for the rest of the callback: the closure
		// and its capture may cease to exist the moment ClearTimer returns.
		const TSharedRef<FRun> Keep = Run;

		UWorld* Live = W.Get();
		if (!Live) { return; }
		Keep->Waited += 0.5f;

		APlayerController* PC = Live->GetFirstPlayerController();
		ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
		UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
		AIBPlayerState* PS = PC ? PC->GetPlayerState<AIBPlayerState>() : nullptr;

		if (!Menu || !PS || !PS->HasOperative())
		{
			if (Keep->Waited >= 45.f)
			{
				Live->GetTimerManager().ClearTimer(Keep->Wait);
				Note(TEXT("no operative on station after 45 s — the header has no live level or XP to redraw. Start this with -IBXPHeaderAfterDeploy so it runs once deployment has put an operative on station."));
				Complete(Keep);
			}
			return;
		}

		Live->GetTimerManager().ClearTimer(Keep->Wait);
		Keep->State = PS;
		RunSequence(Live, Menu, Keep);
	}), 0.5f, true);
}));
}
#endif
