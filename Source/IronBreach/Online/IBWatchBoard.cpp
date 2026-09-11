#include "Online/IBWatchBoard.h"
#include "Online/IBWatchTypes.h"
#include "Online/IBSessionSubsystem.h"
#include "Items/IBPlayerState.h"
#include "IronBreach.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Net/UnrealNetwork.h"
#include "UI/IBWatchScreen.h"
#include "UI/IBMainMenuWidget.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "TimerManager.h"
#include "UnrealClient.h"

AIBWatchBoard::AIBWatchBoard()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
	bReplicates = true;
	bAlwaysRelevant = true;
	SetReplicatingMovement(false);
	SetNetUpdateFrequency(10.f);
}

AIBWatchBoard* AIBWatchBoard::Get(const UWorld* World)
{
	if (!World) { return nullptr; }
	if (const UIBWatchSubsystem* Sub = World->GetSubsystem<UIBWatchSubsystem>())
	{
		if (AIBWatchBoard* Board = Sub->GetBoard()) { return Board; }
	}
	// Clients: the replicated actor arrives without going through the subsystem.
	for (TActorIterator<AIBWatchBoard> It(const_cast<UWorld*>(World)); It; ++It)
	{
		return *It;
	}
	return nullptr;
}

void AIBWatchBoard::BeginPlay()
{
	Super::BeginPlay();
	if (HasAuthority())
	{
		CurrentId = IBWatch::DestinationForMap(GetWorld()->GetMapName());
		UE_LOG(LogIronBreach, Log, TEXT("[Watch] board up in %s (destination '%s')"),
			*GetWorld()->GetMapName(), *CurrentId.ToString());
		Notify();
	}
}

void AIBWatchBoard::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AIBWatchBoard, ProposedId);
	DOREPLIFETIME(AIBWatchBoard, ProposedByName);
	DOREPLIFETIME(AIBWatchBoard, ProposedByPlayerId);
	DOREPLIFETIME(AIBWatchBoard, ArmedId);
	DOREPLIFETIME(AIBWatchBoard, DeployAtServerTime);
	DOREPLIFETIME(AIBWatchBoard, CurrentId);
}

void AIBWatchBoard::OnRep_Board()
{
	OnChanged.Broadcast();
}

void AIBWatchBoard::Notify()
{
	OnChanged.Broadcast();
}

float AIBWatchBoard::ServerNow() const
{
	const UWorld* World = GetWorld();
	if (!World) { return 0.f; }
	if (HasAuthority()) { return static_cast<float>(World->GetTimeSeconds()); }
	if (const AGameStateBase* GS = World->GetGameState()) { return static_cast<float>(GS->GetServerWorldTimeSeconds()); }
	return static_cast<float>(World->GetTimeSeconds());
}

float AIBWatchBoard::GetSecondsToDeploy() const
{
	if (ArmedId.IsNone() || DeployAtServerTime < 0.f) { return -1.f; }
	return FMath::Max(0.f, DeployAtServerTime - ServerNow());
}

bool AIBWatchBoard::IsHostPlayer(const APlayerState* PS) const
{
	if (!PS || !HasAuthority()) { return false; }
	const APlayerController* PC = PS->GetPlayerController();
	return PC && PC->IsLocalPlayerController();
}

void AIBWatchBoard::ServerPropose(APlayerState* By, FName DestinationId)
{
	if (!HasAuthority() || !By) { return; }
	const FIBDestination* Dest = IBWatch::Find(DestinationId);
	if (!Dest || !Dest->CanDeploy())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Watch] %s proposed '%s' — not deployable, ignored"),
			*By->GetPlayerName(), *DestinationId.ToString());
		return;
	}
	if (DestinationId == CurrentId)
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Watch] '%s' is where we already are — ignored"), *DestinationId.ToString());
		return;
	}

	const bool bHost = IsHostPlayer(By);
	if (IsArmed() && !bHost)
	{
		// The drop is running: only the host can change it.
		UE_LOG(LogIronBreach, Log, TEXT("[Watch] %s proposed while armed — host has the trigger"), *By->GetPlayerName());
		return;
	}

	const AIBPlayerState* IBPS = Cast<AIBPlayerState>(By);
	ProposedId = DestinationId;
	ProposedByName = IBPS ? IBPS->GetDisplayCallsign() : By->GetPlayerName();
	ProposedByPlayerId = By->GetPlayerId();
	UE_LOG(LogIronBreach, Log, TEXT("[Watch] %s proposes %s"), *ProposedByName, *Dest->Name.ToString());

	if (bHost)
	{
		Arm(DestinationId); // the host picking is the confirmation
	}
	else
	{
		ArmedId = NAME_None;
		DeployAtServerTime = -1.f;
		bDeployFired = false;
		Notify();
	}
}

void AIBWatchBoard::ServerConfirm(APlayerState* By)
{
	if (!HasAuthority() || !IsHostPlayer(By))
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Watch] confirm refused — only the host arms the board"));
		return;
	}
	const FIBDestination* Dest = IBWatch::Find(ProposedId);
	if (!Dest || !Dest->CanDeploy())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("[Watch] nothing valid proposed to confirm"));
		return;
	}
	Arm(ProposedId);
}

void AIBWatchBoard::ServerCancel(APlayerState* By)
{
	if (!HasAuthority() || !By) { return; }
	const bool bHost = IsHostPlayer(By);
	const bool bProposer = (By->GetPlayerId() == ProposedByPlayerId);
	if (!bHost && !(bProposer && !IsArmed()))
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Watch] cancel by %s refused"), *By->GetPlayerName());
		return;
	}
	UE_LOG(LogIronBreach, Log, TEXT("[Watch] %s stood the board down"), *By->GetPlayerName());
	ClearAll();
}

void AIBWatchBoard::Arm(FName Id)
{
	ArmedId = Id;
	DeployAtServerTime = ServerNow() + IBWatch::DeployDropSeconds;
	bDeployFired = false;
	if (const FIBDestination* Dest = IBWatch::Find(Id))
	{
		UE_LOG(LogIronBreach, Log, TEXT("[Watch] ARMED %s — drop in %.1fs"), *Dest->Name.ToString(), IBWatch::DeployDropSeconds);
	}
	Notify();
}

void AIBWatchBoard::ClearAll()
{
	ProposedId = NAME_None;
	ProposedByName.Reset();
	ProposedByPlayerId = -1;
	ArmedId = NAME_None;
	DeployAtServerTime = -1.f;
	bDeployFired = false;
	Notify();
}

void AIBWatchBoard::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!HasAuthority() || bDeployFired || ArmedId.IsNone() || DeployAtServerTime < 0.f) { return; }
	if (ServerNow() >= DeployAtServerTime)
	{
		FireDeploy();
	}
}

void AIBWatchBoard::FireDeploy()
{
	bDeployFired = true;
	const FIBDestination* Dest = IBWatch::Find(ArmedId);
	if (!Dest || !Dest->CanDeploy())
	{
		UE_LOG(LogIronBreach, Error, TEXT("[Watch] armed destination vanished — standing down"));
		ClearAll();
		return;
	}
	UE_LOG(LogIronBreach, Log, TEXT("[Watch] DEPLOY -> %s (%s)"), *Dest->Name.ToString(), *Dest->MapPath);
	UGameInstance* GI = GetGameInstance();
	if (UIBSessionSubsystem* Sessions = GI ? GI->GetSubsystem<UIBSessionSubsystem>() : nullptr)
	{
		Sessions->IBDeployTo(Dest->MapPath);
	}
	else if (UWorld* World = GetWorld())
	{
		World->ServerTravel(Dest->MapPath);
	}
}

// ---- world subsystem ------------------------------------------------------

void UIBWatchSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	// A session's lobby uses the title map, but must not repeat its boot gate.
	// Wait for the local controller on clients as well as on the listen host.
	if (InWorld.GetNetMode() != NM_Standalone && InWorld.GetNetMode() != NM_DedicatedServer &&
		IBWatch::DestinationForMap(InWorld.GetMapName()) == IBWatch::WatchId())
	{
		InWorld.GetTimerManager().SetTimer(LobbyMenuTimer, this, &UIBWatchSubsystem::OpenLobbyMenu, 0.1f, true);
	}
	if (InWorld.GetNetMode() == NM_Client) { return; } // the board replicates in
	if (Board.IsValid()) { return; }

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	Params.ObjectFlags |= RF_Transient;
	Board = InWorld.SpawnActor<AIBWatchBoard>(AIBWatchBoard::StaticClass(), FTransform::Identity, Params);

	// Dev shortcut: -IBWatch on the command line opens the deck straight away in
	// the standalone menu world (no boot screen, no sheet). -IBWatchShots adds a
	// timed tour with screenshots into Saved/Screenshots/Watch (orbit, board,
	// the drop) so the look can be checked without anyone at the keyboard.
	if (InWorld.GetNetMode() == NM_Standalone && FParse::Param(FCommandLine::Get(), TEXT("IBWatch"))
		&& IBWatch::DestinationForMap(InWorld.GetMapName()) == IBWatch::WatchId())
	{
		const bool bShots = FParse::Param(FCommandLine::Get(), TEXT("IBWatchShots"));
		FTimerHandle OpenHandle;
		InWorld.GetTimerManager().SetTimer(OpenHandle, FTimerDelegate::CreateWeakLambda(this, [this, bShots]()
		{
			UWorld* W = GetWorld();
			APlayerController* PC = W ? W->GetFirstPlayerController() : nullptr;
			if (!PC) { return; }
			UIBWatchScreen* Screen = CreateWidget<UIBWatchScreen>(PC, UIBWatchScreen::StaticClass());
			if (!Screen) { return; }
			Screen->AddToViewport(50);
			FInputModeUIOnly Mode;
			Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
			PC->SetInputMode(Mode);
			PC->SetShowMouseCursor(true);
			DevScreen = Screen;
			UE_LOG(LogIronBreach, Log, TEXT("[Watch] -IBWatch: deck opened directly (dev)"));
			if (!bShots) { return; }
			const FString Dir = FPaths::ProjectSavedDir() / TEXT("Screenshots/Watch");
			auto Shot = [this, Dir](float At, const TCHAR* Name, TFunction<void()> Before)
			{
				FTimerHandle H;
				GetWorld()->GetTimerManager().SetTimer(H, FTimerDelegate::CreateWeakLambda(this, [Dir, Name, Before]()
				{
					if (Before) { Before(); }
					FScreenshotRequest::RequestScreenshot(Dir / Name, true, false);
				}), At, false);
			};
			Shot(6.f,  TEXT("watch_orbit.png"), nullptr);
			Shot(8.f,  TEXT("watch_board.png"), [this]() { if (DevScreen.IsValid()) { DevScreen->DevOpenBoard(); } });
			Shot(10.f, TEXT("watch_board_open.png"), nullptr);
			Shot(11.f, TEXT("watch_orbit_back.png"), [this]() { if (DevScreen.IsValid()) { DevScreen->DevOpenOrbit(); } });
			Shot(13.5f, TEXT("watch_drop_start.png"), [this]() { if (DevScreen.IsValid()) { DevScreen->DevDeploy(); } });
			Shot(14.4f, TEXT("watch_drop_mid.png"), nullptr);
			Shot(15.2f, TEXT("watch_drop_late.png"), nullptr);
		}), 1.5f, false);
	}
}

void UIBWatchSubsystem::OpenLobbyMenu()
{
	UWorld* World = GetWorld();
	APlayerController* PC = World && World->GetGameInstance() ? World->GetGameInstance()->GetFirstLocalPlayerController() : nullptr;
	if (!PC || !PC->IsLocalController()) { return; }

	TArray<UUserWidget*> Menus;
	UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Menus, UIBMainMenuWidget::StaticClass(), true);
	if (Menus.IsEmpty())
	{
		const TSubclassOf<UIBMainMenuWidget> MenuClass = LoadClass<UIBMainMenuWidget>(nullptr, TEXT("/Game/UI/WBP_MainMenu.WBP_MainMenu_C"));
		UIBMainMenuWidget* Menu = MenuClass ? CreateWidget<UIBMainMenuWidget>(PC, MenuClass) : nullptr;
		if (!Menu)
		{
			UE_LOG(LogIronBreach, Error, TEXT("[Watch] Could not open the lobby menu"));
			World->GetTimerManager().ClearTimer(LobbyMenuTimer);
			return;
		}
		Menu->AddToViewport(); // Native initialization enters the appropriate lobby state.
	}

	// Remove only the authored boot gate; preserve the Watch, roster and other UI.
	TArray<UUserWidget*> Widgets;
	UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Widgets, UUserWidget::StaticClass(), true);
	for (UUserWidget* Widget : Widgets)
	{
		if (Widget->GetClass()->GetPathName() == TEXT("/Game/UI/WBP_BootScreen.WBP_BootScreen_C"))
		{
			Widget->RemoveFromParent();
		}
	}
	World->GetTimerManager().ClearTimer(LobbyMenuTimer);
	UE_LOG(LogIronBreach, Log, TEXT("[Watch] Live lobby entered without the title gate"));
}
