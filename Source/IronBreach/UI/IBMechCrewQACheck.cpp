// Opt-in, development-only two-process verification of the MECH menu's crew readout on a
// REMOTE CLIENT. Two console commands, one per process:
//
//   IB.CrewQAHost              on the listen host, after IB.DeploymentCheck has settled it
//   IB.CrewQAClient <address>  on the second process; it connects, then observes
//
// The host drives the real boarding / crew-swap / disembark APIs. The client opens the real
// Mech menu and reads the text the widgets actually render. Neither writes progression: the
// host only calls existing crew entry points, and the client is NM_Client, where the vault
// and XP saves are authority-gated and never run.
#include "CoreMinimal.h"
#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
#include "IronBreach.h"
#include "Infantry/IBCharacter_Infantry.h"
#include "Items/IBPlayerState.h"
#include "Mech/IBGunnerSeat.h"
#include "Mech/IBMech_Base.h"
#include "UI/IBMenuScreen.h"
#include "UI/IBMenuSubsystem.h"
#include "Blueprint/WidgetTree.h"
#include "Components/HorizontalBox.h"
#include "Components/PanelWidget.h"
#include "Components/TextBlock.h"
#include "Containers/Ticker.h"
#include "Engine/LocalPlayer.h"
#include "Engine/NetDriver.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

namespace IBMechCrewQA
{
// ---------------------------------------------------------------- reporting

static void Say(const TCHAR* Tag, const TCHAR* Verdict, const FString& What)
{
	UE_LOG(LogIronBreach, Display, TEXT("[%s] %s %s"), Tag, Verdict, *What);
}

/** Every run's own scoreboard. A run is only a pass when every expected assertion actually
 *  ran: 'nothing failed' is not the same thing, because a TIMEOUT or a SKIP ends the sequence
 *  early and leaves the remaining assertions unmade. */
struct FTally
{
	int32 Passed = 0;
	int32 Failed = 0;
	int32 Skipped = 0;
	int32 TimedOut = 0;
};

static const int32 HostExpected = 6;
static const int32 ClientExpected = 13;

static bool Complete(const TCHAR* Tag, const FTally& Tally, int32 Expected)
{
	const bool bFull = Tally.Failed == 0 && Tally.Skipped == 0 && Tally.TimedOut == 0 && Tally.Passed == Expected;
	UE_LOG(LogIronBreach, Display, TEXT("[%s] COMPLETE: %s %d/%d (%d failed, %d skipped, %d timed out)"),
		Tag, bFull ? TEXT("PASS") : TEXT("INCOMPLETE"), Tally.Passed, Expected, Tally.Failed, Tally.Skipped, Tally.TimedOut);
	return false; // the ticker stops by returning false — never by clearing itself
}

/** The mech Blueprint the project's placed actors are instances of, used only to tell a missing
 *  asset apart from an unplaced one when a run finds no frame. Nothing spawns from this. */
static const TCHAR* ConfiguredMechClassPath() { return TEXT("/Game/Characters/Mech/Blueprints/Class/BP_Mech.BP_Mech_C"); }

static FString Shot(const TCHAR* Name)
{
	// ProjectDir, not ProjectSavedDir: both processes run under their own -UserDir sandbox, so
	// ProjectSavedDir would scatter these into two sandboxes. Absolute, in the real project
	// tree, so both processes deposit their images in one predictable place.
	const FString File = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir() / TEXT("Saved/MechCrewQA/shots") / Name);
	FScreenshotRequest::RequestScreenshot(File, true, false);
	return File;
}

// ---------------------------------------------------------------- shared reads

/** The two humans in the session, if there are exactly two. AI controllers never create a
 *  PlayerState, so PlayerArray is already human-only; this also rejects bots explicitly. */
static bool TwoHumans(const UWorld* World, const APlayerState*& OutA, const APlayerState*& OutB)
{
	OutA = OutB = nullptr;
	const AGameStateBase* GS = World ? World->GetGameState() : nullptr;
	if (!GS) { return false; }
	TArray<const APlayerState*> Humans;
	for (const APlayerState* PS : GS->PlayerArray)
	{
		if (PS && !PS->IsABot()) { Humans.Add(PS); }
	}
	if (Humans.Num() != 2 || Humans[0] == Humans[1]) { return false; }
	OutA = Humans[0];
	OutB = Humans[1];
	return true;
}

/** The frame the Mech sheet will pick, decided the same way but INDEPENDENTLY of
 *  UIBMechScreen::FindFrame: a frame with the local player aboard wins, else the first. */
static AIBMech_Base* Frame(UWorld* World, const APlayerState* Mine, int32& OutCount)
{
	OutCount = 0;
	AIBMech_Base* Crewed = nullptr;
	AIBMech_Base* First = nullptr;
	for (TActorIterator<AIBMech_Base> It(World); It; ++It)
	{
		AIBMech_Base* M = *It;
		++OutCount;
		if (!First) { First = M; }
		if (Mine && !Crewed)
		{
			const bool bAboard = M->GetPlayerState() == Mine ||
				(M->GunnerSeat && M->GunnerSeat->GetPlayerState() == Mine);
			if (bAboard) { Crewed = M; }
		}
	}
	return Crewed ? Crewed : First;
}

/**
 * What the sheet OUGHT to print for a station, derived without touching the code under test.
 *
 * Deliberately not UIBMechScreen::StationOccupant: that helper is the thing being verified,
 * and an expectation computed from it would agree with any bug it contains. This reads the
 * station pawn's own replicated PlayerState — which reaches every machine — and formats the
 * name the way a person reading the sheet would. An empty string means "no human here", which
 * the sheet may legitimately render as EMPTY or AI CO-PILOT.
 */
static FString ExpectedOccupant(const APawn* StationPawn)
{
	const APlayerState* PS = StationPawn ? StationPawn->GetPlayerState() : nullptr;
	if (const AIBPlayerState* Operative = Cast<AIBPlayerState>(PS)) { return Operative->GetDisplayCallsign().ToUpper(); }
	if (PS) { return PS->GetPlayerName().ToUpper(); }
	return FString();
}

/** One CREW row of the open Mech sheet, read as rendered. The row is found by its caption and
 *  its cells are taken in slot order — [caption, occupant, role] — so nothing here depends on
 *  the screen's private members or on the helper that filled them. */
static bool ReadCrewRow(UUserWidget* Screen, const TCHAR* Caption, FString& OutOccupant, FString& OutRole)
{
	if (!Screen || !Screen->WidgetTree) { return false; }
	UTextBlock* CaptionCell = nullptr;
	Screen->WidgetTree->ForEachWidget([&CaptionCell, Caption](UWidget* Widget)
	{
		if (UTextBlock* Text = Cast<UTextBlock>(Widget))
		{
			if (!CaptionCell && Text->GetText().ToString().Equals(Caption, ESearchCase::IgnoreCase)) { CaptionCell = Text; }
		}
	});
	if (!CaptionCell) { return false; }

	UHorizontalBox* Row = nullptr;
	for (UPanelWidget* Parent = CaptionCell->GetParent(); Parent; Parent = Parent->GetParent())
	{
		if (UHorizontalBox* Box = Cast<UHorizontalBox>(Parent)) { Row = Box; break; }
	}
	if (!Row) { return false; }

	TArray<UTextBlock*> Cells;
	UWidgetTree::ForWidgetAndChildren(Row, [&Cells](UWidget* Widget)
	{
		if (UTextBlock* Text = Cast<UTextBlock>(Widget)) { Cells.Add(Text); }
	});
	if (Cells.Num() < 3) { return false; }
	OutOccupant = Cells[1]->GetText().ToString();
	OutRole = Cells[2]->GetText().ToString();
	return true;
}

// ================================================================ HOST

/**
 * Drives the real crew lifecycle so the client has something true to observe. Every step is
 * an existing entry point: AIBCharacter_Infantry::Server_RequestBoard (which re-validates
 * range on the server and calls AIBMech_Base::ServerBoard), ServerRequestCrewSwap twice
 * inside its confirm window (-> PerformPossessionSwap), then ServerDisembark.
 *
 * The one harness liberty is positioning: both test pawns are moved next to the hull first.
 * That is not a boarding bypass — Server_RequestBoard's BoardMaxDistance check still runs and
 * must pass, and its passing is part of the evidence. Nothing sets HullOccupancy or
 * SeatOccupancy directly; those are only ever written by the mech's own RefreshCrewView.
 */
static FAutoConsoleCommandWithWorld HostCommand(TEXT("IB.CrewQAHost"),
	TEXT("Listen host: board two humans into the mech, swap them, then disembark. Pairs with IB.CrewQAClient."),
FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* StartWorld)
{
	if (!StartWorld || !StartWorld->IsGameWorld()) { return; }
	TWeakObjectPtr<UGameInstance> WeakGI(StartWorld->GetGameInstance());

	// Core ticker, not a world timer: it survives world replacement, and — the lesson from the
	// XP check's crash — it is stopped by RETURNING FALSE, never by clearing itself from
	// inside its own callback, so no delegate ever destroys the state it is still running on.
	FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(
		[WeakGI, Phase = 0, Started = FPlatformTime::Seconds(), StepAt = 0.0,
		 bNetLogged = false, Tally = FTally()](float) mutable -> bool
	{
		UGameInstance* GI = WeakGI.Get();
		UWorld* World = GI ? GI->GetWorld() : nullptr;
		if (!World) { return false; }
		const double Now = FPlatformTime::Seconds();
		auto Verdict = [&Tally](bool bOK, const FString& What)
		{
			if (bOK) { ++Tally.Passed; } else { ++Tally.Failed; }
			Say(TEXT("CrewQAHost"), bOK ? TEXT("PASS") : TEXT("FAIL"), What);
		};
		auto Expire = [&Tally](const FString& What) { ++Tally.TimedOut; Say(TEXT("CrewQAHost"), TEXT("TIMEOUT"), What); };
		auto Finish = [&Tally]() -> bool { return Complete(TEXT("CrewQAHost"), Tally, HostExpected); };

		// The connect evidence, emitted ONCE as soon as this host is listening and before the
		// wait for a second player. It has to come first: the launch procedure reads the port
		// from this line to start the client, so gating it behind the client's own arrival
		// would be circular. Non-const driver pointer — LowLevelGetNetworkNumber() is not a
		// const member — and every FString bound to a named local before it is formatted.
		if (!bNetLogged)
		{
			if (UNetDriver* Driver = World->GetNetDriver())
			{
				bNetLogged = true;
				const FString DriverName = Driver->GetClass()->GetName();
				const FString Listen = Driver->LowLevelGetNetworkNumber();
				const FString Url = World->URL.ToString();
				Say(TEXT("CrewQAHost"), TEXT("NET"), FString::Printf(
					TEXT("driver=%s listen=%s url=%s netmode=%d — connect the client to 127.0.0.1:<port from listen/url>"),
					*DriverName, *Listen, *Url, int32(World->GetNetMode())));
			}
		}

		// Generous, because phase 0 also covers however long it takes Codex to launch the client.
		if (Now - Started > 480.0)
		{
			Expire(FString::Printf(TEXT("gave up in phase %d"), Phase));
			return Finish();
		}

		AIBMech_Base* Mech = nullptr;
		{
			int32 Count = 0;
			Mech = Frame(World, nullptr, Count);
			if (Phase == 0 && Count == 0 && Now - Started > 20.0)
			{
				Verdict(false, FString::Printf(
					TEXT("no AIBMech_Base in %s — this map cannot exercise the crew sheet"), *World->GetMapName()));
				// Diagnostic only; nothing is spawned. "No frame here" has two very different
				// causes and the log should say which: the configured mech Blueprint class
				// resolves but is not placed in this map, or the class does not resolve at all.
				// A failed load is reported as exactly that and nothing more — it does not by
				// itself establish that the package is gone, since a cook, path or dependency
				// fault fails the same way. Whether the package exists is a question for the
				// project on disk, confirmed separately.
				const UClass* Configured = LoadClass<AIBMech_Base>(nullptr, ConfiguredMechClassPath());
				Say(TEXT("CrewQAHost"), TEXT("NOTE"), FString::Printf(TEXT("configured mech Blueprint '%s' %s"),
					ConfiguredMechClassPath(),
					Configured
						? TEXT("resolves — it is simply not placed in this map")
						: TEXT("FAILED TO LOAD: the class did not resolve in this run. Confirm on disk whether the package exists before concluding the asset is missing")));
				return Finish();
			}
		}

		// ---- 0: two humans, both settled in the world, on a listen server, with a frame ----
		if (Phase == 0)
		{
			const APlayerState* A = nullptr;
			const APlayerState* B = nullptr;
			if (!Mech || !TwoHumans(World, A, B)) { return true; }
			// Readiness gate. There is no acknowledgement channel from the client — see the
			// note above ClientCommand — so the host waits for the strongest signal it CAN
			// see: both humans have finished travelling and possess a pawn. That removes the
			// long, variable part of client start-up from the timing below.
			int32 WithPawn = 0;
			for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
			{
				const APlayerController* PC = It->Get();
				if (PC && PC->GetPawn()) { ++WithPawn; }
			}
			if (WithPawn < 2) { return true; }

			Verdict(World->GetNetMode() == NM_ListenServer, FString::Printf(
				TEXT("host is a listen server (net mode %d) with two distinct human player states, both possessing a pawn: '%s' / '%s'"),
				int32(World->GetNetMode()), *A->GetPlayerName(), *B->GetPlayerName()));
			StepAt = Now;
			Phase = 1;
			return true;
		}

		// Everything below needs the frame.
		if (!Mech) { return true; }

		// ---- 1: put both pawns in range, then board through the real relay ----
		if (Phase == 1)
		{
			if (Now - StepAt < 2.0) { return true; }
			int32 Boarded = 0;
			int32 Index = 0;
			for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
			{
				APlayerController* PC = It->Get();
				AIBCharacter_Infantry* Body = PC ? Cast<AIBCharacter_Infantry>(PC->GetPawn()) : nullptr;
				if (!Body) { continue; }
				// Harness positioning only; the range check in Server_RequestBoard still decides.
				const FVector Side = Mech->GetActorRightVector() * (Index == 0 ? 300.f : -300.f);
				Body->SetActorLocation(Mech->GetActorLocation() + Side + FVector(0, 0, 120.f),
					false, nullptr, ETeleportType::TeleportPhysics);
				// Both ask for the hull; ServerBoard's own correction gives boarder 2 the seat.
				Body->Server_RequestBoard(Mech, /*bWantLeftSeat=*/true);
				++Boarded;
				++Index;
			}
			Verdict(Boarded == 2, FString::Printf(TEXT("boarding requested for %d pawns through Server_RequestBoard"), Boarded));
			StepAt = Now;
			Phase = 2;
			return true;
		}

		// ---- 2: confirm both stations took a human, then hold for the client to look ----
		if (Phase == 2)
		{
			if (Now - StepAt < 3.0) { return true; }
			APlayerController* HullPC = Cast<APlayerController>(Mech->GetController());
			APlayerController* SeatPC = Mech->GunnerSeat ? Cast<APlayerController>(Mech->GunnerSeat->GetController()) : nullptr;
			Verdict(HullPC && SeatPC && HullPC != SeatPC, FString::Printf(
				TEXT("two humans aboard — hull '%s', gunner seat '%s'"),
				HullPC && HullPC->PlayerState ? *HullPC->PlayerState->GetPlayerName() : TEXT("none"),
				SeatPC && SeatPC->PlayerState ? *SeatPC->PlayerState->GetPlayerName() : TEXT("none")));
			if (!HullPC || !SeatPC) { return Finish(); }
			StepAt = Now;
			Phase = 3;
			return true;
		}

		// ---- 3: the two-human swap: arm, then confirm inside SwapConfirmWindow ----
		if (Phase == 3)
		{
			if (Now - StepAt < 20.0) { return true; } // open-loop hold: the client's first screenshot lands here
			APlayerController* HullPC = Cast<APlayerController>(Mech->GetController());
			APlayerController* SeatPC = Mech->GunnerSeat ? Cast<APlayerController>(Mech->GunnerSeat->GetController()) : nullptr;
			if (!HullPC || !SeatPC) { Verdict(false, TEXT("crew left the frame before the swap")); return Finish(); }
			Say(TEXT("CrewQAHost"), TEXT("STEP"), FString::Printf(TEXT("swap armed by '%s', confirmed by '%s'"),
				*HullPC->PlayerState->GetPlayerName(), *SeatPC->PlayerState->GetPlayerName()));
			Mech->ServerRequestCrewSwap(HullPC);
			Mech->ServerRequestCrewSwap(SeatPC); // inside the 5 s confirm window by construction
			StepAt = Now;
			Phase = 4;
			return true;
		}

		// ---- 4: the stations must now hold the OTHER human ----
		if (Phase == 4)
		{
			if (Now - StepAt < 3.0) { return true; }
			APlayerController* HullPC = Cast<APlayerController>(Mech->GetController());
			APlayerController* SeatPC = Mech->GunnerSeat ? Cast<APlayerController>(Mech->GunnerSeat->GetController()) : nullptr;
			Verdict(HullPC && SeatPC && HullPC != SeatPC, FString::Printf(
				TEXT("after PerformPossessionSwap — hull '%s', gunner seat '%s'"),
				HullPC && HullPC->PlayerState ? *HullPC->PlayerState->GetPlayerName() : TEXT("none"),
				SeatPC && SeatPC->PlayerState ? *SeatPC->PlayerState->GetPlayerName() : TEXT("none")));
			StepAt = Now;
			Phase = 5;
			return true;
		}

		// ---- 5: the gunner leaves; BackfillSeatWithAI should fill the seat ----
		if (Phase == 5)
		{
			if (Now - StepAt < 15.0) { return true; } // open-loop hold: the client's swap screenshot lands here
			APlayerController* SeatPC = Mech->GunnerSeat ? Cast<APlayerController>(Mech->GunnerSeat->GetController()) : nullptr;
			if (!SeatPC) { Verdict(false, TEXT("no human in the gunner seat to dismount")); return Finish(); }
			Say(TEXT("CrewQAHost"), TEXT("STEP"), FString::Printf(TEXT("gunner '%s' dismounting"), *SeatPC->PlayerState->GetPlayerName()));
			Mech->ServerDisembark(SeatPC);
			StepAt = Now;
			Phase = 6;
			return true;
		}

		if (Phase == 6)
		{
			if (Now - StepAt < 3.0) { return true; }
			AController* SeatNow = Mech->GunnerSeat ? Mech->GunnerSeat->GetController() : nullptr;
			const bool bAI = SeatNow && !SeatNow->IsA<APlayerController>();
			Verdict(bAI, FString::Printf(TEXT("gunner seat backfilled by a non-player controller: %s"),
				SeatNow ? *SeatNow->GetClass()->GetName() : TEXT("none")));
			StepAt = Now;
			Phase = 7;
			return true;
		}

		// ---- 7: the last human leaves the hull ----
		if (Phase == 7)
		{
			if (Now - StepAt < 15.0) { return true; } // open-loop hold: the client's backfill screenshot lands here
			APlayerController* HullPC = Cast<APlayerController>(Mech->GetController());
			if (!HullPC) { Verdict(false, TEXT("no human in the hull to dismount")); return Finish(); }
			Say(TEXT("CrewQAHost"), TEXT("STEP"), FString::Printf(TEXT("hull pilot '%s' dismounting"), *HullPC->PlayerState->GetPlayerName()));
			Mech->ServerDisembark(HullPC);
			StepAt = Now;
			Phase = 8;
			return true;
		}

		if (Phase == 8)
		{
			if (Now - StepAt < 3.0) { return true; }
			// Derived from the code, not from a wish: ServerDisembark vacates the hull and calls
			// BackfillSeatWithAI, whose bHullHasPlayer test now fails — so it neither fills the
			// hull nor evicts the AI already in the seat.
			AController* HullNow = Mech->GetController();
			AController* SeatNow = Mech->GunnerSeat ? Mech->GunnerSeat->GetController() : nullptr;
			Verdict(Cast<APlayerController>(HullNow) == nullptr, FString::Printf(
				TEXT("hull holds no human after the last departure (controller: %s)"),
				HullNow ? *HullNow->GetClass()->GetName() : TEXT("none")));
			Say(TEXT("CrewQAHost"), TEXT("OBSERVED"), FString::Printf(TEXT("gunner seat controller after the last departure: %s"),
				SeatNow ? *SeatNow->GetClass()->GetName() : TEXT("none")));
			StepAt = Now;
			Phase = 9;
			return true;
		}

		if (Phase == 9 && Now - StepAt > 15.0) { return Finish(); } // let the client finish looking
		return true;
	}), 1.0f);
}));

// ================================================================ CLIENT

/**
 * Connects, then WATCHES. It never drives crew state — it waits for each condition to appear
 * and asserts what the real widgets render when it does, so the two processes need no clock
 * agreement, only the host actually doing the work.
 */
static FAutoConsoleCommandWithWorldAndArgs ClientCommand(TEXT("IB.CrewQAClient"),
	TEXT("Second process: connect to <address>, open the Mech menu and verify the crew readout. Pairs with IB.CrewQAHost."),
FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* StartWorld)
{
	if (!StartWorld || !StartWorld->IsGameWorld()) { return; }
	const FString Address = Args.Num() > 0 ? Args[0] : TEXT("127.0.0.1:7777");
	TWeakObjectPtr<UGameInstance> WeakGI(StartWorld->GetGameInstance());

	FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(
		[WeakGI, Address, Phase = 0, Started = FPlatformTime::Seconds(), StepAt = 0.0,
		 bAsked = false, Tally = FTally(), HullWas = FString(), SeatWas = FString(), SettleAt = 0.0](float) mutable -> bool
	{
		UGameInstance* GI = WeakGI.Get();
		UWorld* World = GI ? GI->GetWorld() : nullptr;
		if (!World) { return false; }
		const double Now = FPlatformTime::Seconds();
		auto Verdict = [&Tally](bool bOK, const FString& What)
		{
			if (bOK) { ++Tally.Passed; } else { ++Tally.Failed; }
			Say(TEXT("CrewQAClient"), bOK ? TEXT("PASS") : TEXT("FAIL"), What);
		};
		auto Skip = [&Tally](const FString& What) { ++Tally.Skipped; Say(TEXT("CrewQAClient"), TEXT("SKIP"), What); };
		auto Expire = [&Tally](const FString& What) { ++Tally.TimedOut; Say(TEXT("CrewQAClient"), TEXT("TIMEOUT"), What); };
		auto Finish = [&Tally]() -> bool { return Complete(TEXT("CrewQAClient"), Tally, ClientExpected); };
		if (Now - Started > 420.0)
		{
			Expire(FString::Printf(TEXT("gave up in phase %d"), Phase));
			return Finish();
		}

		APlayerController* PC = World->GetFirstPlayerController();

		// ---- 0: connect, and prove this really is a remote client ----
		if (Phase == 0)
		{
			if (World->GetNetMode() != NM_Client)
			{
				if (!bAsked && PC)
				{
					bAsked = true;
					Say(TEXT("CrewQAClient"), TEXT("STEP"), FString::Printf(TEXT("connecting to %s"), *Address));
					PC->ClientTravel(Address, ETravelType::TRAVEL_Absolute);
				}
				return true;
			}
			const APlayerState* A = nullptr;
			const APlayerState* B = nullptr;
			if (!PC || !PC->PlayerState || !TwoHumans(World, A, B)) { return true; }
			const bool bMineIsOne = (PC->PlayerState == A || PC->PlayerState == B);
			Verdict(true, FString::Printf(TEXT("joined as a remote client (net mode %d) of %s"),
				int32(World->GetNetMode()), *World->GetMapName()));
			Verdict(bMineIsOne, FString::Printf(
				TEXT("two distinct human player states present, one of them local: '%s' / '%s' (local '%s')"),
				*A->GetPlayerName(), *B->GetPlayerName(), *PC->PlayerState->GetPlayerName()));
			if (A->GetPlayerName() == B->GetPlayerName())
			{
				// Two identical names can never evidence an exchange, and carrying on would
				// only produce a timeout that looks like a product fault. Stop here instead.
				Skip(FString::Printf(TEXT("both humans render the same name ('%s'), so no swap could ever be distinguished — relaunch the client with ?Name= on the connect address"),
					*A->GetPlayerName()));
				return Finish();
			}
			StepAt = Now;
			Phase = 1;
			return true;
		}

		// ---- 1: open the real Mech page ----
		if (Phase == 1)
		{
			const ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
			UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
			if (!Menu) { return true; }
			Menu->OpenScreen(TEXT("Mech"));
			Verdict(Menu->GetActiveScreenId() == TEXT("Mech"), TEXT("Mech page opened on the client"));
			StepAt = Now;
			Phase = 2;
			return true;
		}

		const ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
		UIBMenuSubsystem* Menu = LP ? LP->GetSubsystem<UIBMenuSubsystem>() : nullptr;
		UUserWidget* Sheet = Menu ? Cast<UUserWidget>(Menu->GetActiveScreen()) : nullptr;
		FString HullName, HullRole, SeatName, SeatRole;
		const bool bRead = ReadCrewRow(Sheet, TEXT("HULL"), HullName, HullRole)
			&& ReadCrewRow(Sheet, TEXT("GUNNER SEAT"), SeatName, SeatRole);

		int32 FrameCount = 0;
		AIBMech_Base* Mech = Frame(World, PC ? PC->PlayerState : nullptr, FrameCount);
		const FString HullExpected = ExpectedOccupant(Mech);
		const FString SeatExpected = Mech ? ExpectedOccupant(Mech->GunnerSeat) : FString();

		// ---- 2: both stations crewed by distinct humans ----
		if (Phase == 2)
		{
			if (!bRead || HullExpected.IsEmpty() || SeatExpected.IsEmpty() || HullExpected == SeatExpected)
			{
				SettleAt = 0.0;
				if (Now - StepAt > 90.0)
				{
					Expire(TEXT("two distinct humans never appeared at the two stations — the host may not have boarded, or this client opened the sheet before they did"));
					return Finish();
				}
				return true;
			}
			// The expectation is read from the station pawns' PlayerStates, which can land a beat
			// before the frame's replicated HullOccupancy/SeatOccupancy and before the sheet's own
			// 0.5 s refresh. The 09-30 run asserted 0.23 s after boarding and read EMPTY/EMPTY while
			// the same sheet later showed the correct AI CO-PILOT. Give the sheet a short settle
			// window to catch up, so the verdict measures the sheet rather than that race.
			if (HullName != HullExpected || SeatName != SeatExpected)
			{
				if (SettleAt == 0.0) { SettleAt = Now; }
				if (Now - SettleAt < 5.0) { return true; }
			}
			Verdict(HullName == HullExpected && SeatName == SeatExpected, FString::Printf(
				TEXT("stations name their own occupants — HULL '%s' (expected '%s'), GUNNER SEAT '%s' (expected '%s')"),
				*HullName, *HullExpected, *SeatName, *SeatExpected));
			Verdict(HullName != SeatName, TEXT("the two stations name different operatives"));
			Verdict(HullRole.IsEmpty() && SeatRole.IsEmpty(), FString::Printf(
				TEXT("roles stay blank on a remote client — hull role '%s', seat role '%s'"), *HullRole, *SeatRole));
			Say(TEXT("CrewQAClient"), TEXT("SHOT"), Shot(TEXT("client-crewed.png")));
			HullWas = HullName;
			SeatWas = SeatName;
			StepAt = Now;
			Phase = 3;
			return true;
		}

		// ---- 3: the names exchange across the possession swap; captions do not ----
		if (Phase == 3)
		{
			if (!bRead || HullName != SeatWas || SeatName != HullWas)
			{
				if (Now - StepAt > 90.0)
				{
					// The likeliest cause is arrival order, not a broken swap: if this client
					// only reached phase 2 after the host had already swapped, the names it
					// latched were the post-swap pair and no further exchange is coming.
					Expire(FString::Printf(
						TEXT("the station names never exchanged — HULL '%s', GUNNER SEAT '%s' (latched '%s' / '%s'). If this client joined late it may have latched the POST-swap pair; re-run before treating it as a sheet fault"),
						*HullName, *SeatName, *HullWas, *SeatWas));
					return Finish();
				}
				return true;
			}
			Verdict(true, FString::Printf(TEXT("names exchanged across the possession swap — HULL '%s' -> '%s', GUNNER SEAT '%s' -> '%s'"),
				*HullWas, *HullName, *SeatWas, *SeatName));
			Verdict(HullName == HullExpected && SeatName == SeatExpected,
				TEXT("each station still names the operative actually possessing its pawn"));
			Verdict(HullRole.IsEmpty() && SeatRole.IsEmpty(), TEXT("roles still blank after the swap"));
			Say(TEXT("CrewQAClient"), TEXT("SHOT"), Shot(TEXT("client-swapped.png")));
			StepAt = Now;
			Phase = 4;
			return true;
		}

		// ---- 4: gunner departs, AI backfills ----
		if (Phase == 4)
		{
			const bool bSeatIsAI = SeatName.Equals(TEXT("AI CO-PILOT"), ESearchCase::IgnoreCase);
			if (!bRead || !bSeatIsAI)
			{
				if (Now - StepAt > 90.0)
				{
					Expire(FString::Printf(TEXT("the gunner seat never read AI CO-PILOT — it reads '%s'"), *SeatName));
					return Finish();
				}
				return true;
			}
			// Corroborated, not taken on the sheet's word: the seat pawn carries no PlayerState,
			// so whoever is in it is genuinely not a human.
			Verdict(SeatExpected.IsEmpty(), TEXT("the gunner seat pawn carries no human player state while the sheet reads AI CO-PILOT"));
			Verdict(!HullName.IsEmpty() && HullName == HullExpected, FString::Printf(
				TEXT("the hull still names its human — '%s'"), *HullName));
			Say(TEXT("CrewQAClient"), TEXT("SHOT"), Shot(TEXT("client-backfill.png")));
			StepAt = Now;
			Phase = 5;
			return true;
		}

		// ---- 5: the last human leaves ----
		if (Phase == 5)
		{
			const bool bHullEmpty = HullName.Equals(TEXT("EMPTY"), ESearchCase::IgnoreCase);
			if (!bRead || !bHullEmpty)
			{
				if (Now - StepAt > 90.0)
				{
					Expire(FString::Printf(TEXT("the hull never emptied — it reads '%s'"), *HullName));
					return Finish();
				}
				return true;
			}
			// Expected from AIBMech_Base::ServerDisembark + BackfillSeatWithAI, read beforehand:
			// the hull empties, and the AI already in the seat is not evicted.
			Verdict(HullExpected.IsEmpty(), TEXT("hull reads EMPTY and carries no human player state"));
			Say(TEXT("CrewQAClient"), TEXT("OBSERVED"), FString::Printf(
				TEXT("gunner seat after the last departure: '%s' (code predicts AI CO-PILOT — the backfill does not evict)"), *SeatName));
			Verdict(HullRole.IsEmpty() && SeatRole.IsEmpty(), TEXT("roles blank on an uncrewed-by-humans frame"));
			Say(TEXT("CrewQAClient"), TEXT("SHOT"), Shot(TEXT("client-departed.png")));
			if (FrameCount < 2)
			{
				// A known limitation of the map, not a case this run covered. It is logged as a
				// NOTE rather than a SKIP so it does not pretend to be an assertion that was
				// almost made — but §5 of the result document names it as uncovered.
				Say(TEXT("CrewQAClient"), TEXT("NOTE"), FString::Printf(
					TEXT("a wholly empty frame is NOT covered by this run: the map holds %d AIBMech_Base actor(s) and the AI keeps the seat after the last human leaves"), FrameCount));
			}
			return Finish();
		}
		return true;
	}), 1.0f);
}));
}
#endif
