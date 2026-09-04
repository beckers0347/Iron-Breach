#include "Online/IBSessionSubsystem.h"
#include "IronBreach.h"
#include "OnlineSubsystem.h"
#include "OnlineSubsystemUtils.h"   // Online::GetSubsystem / session helpers
#include "OnlineSessionSettings.h"  // FOnlineSessionSettings, FOnlineSessionSearch
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

namespace
{
	// One project-wide session name; we only ever run one session at a time.
	const FName IBSessionName(NAME_GameSession);
}

void UIBSessionSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Steam overlay invites: accepting one lands here — join the sender.
	if (IOnlineSessionPtr Sessions = GetSessionInterface())
	{
		InviteAcceptedHandle = Sessions->AddOnSessionUserInviteAcceptedDelegate_Handle(
			FOnSessionUserInviteAcceptedDelegate::CreateUObject(this, &UIBSessionSubsystem::OnInviteAccepted));
	}
}

void UIBSessionSubsystem::Deinitialize()
{
	if (IOnlineSessionPtr Sessions = GetSessionInterface())
	{
		Sessions->ClearOnSessionUserInviteAcceptedDelegate_Handle(InviteAcceptedHandle);
	}
	Super::Deinitialize();
}

void UIBSessionSubsystem::OnInviteAccepted(const bool bWasSuccessful, const int32 /*ControllerId*/,
	FUniqueNetIdPtr /*UserId*/, const FOnlineSessionSearchResult& InviteResult)
{
	if (!bWasSuccessful || !InviteResult.IsValid())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("Invite accepted but the session result was invalid"));
		ReportStatus(EIBSessionStatus::JoinFailed, TEXT("INVITE EXPIRED"));
		return;
	}
	UE_LOG(LogIronBreach, Log, TEXT("Invite accepted — joining the sender's squad"));
	ReportStatus(EIBSessionStatus::Joining, TEXT("INVITE ACCEPTED - LINKING..."));
	JoinSearchResult(InviteResult);
}

bool UIBSessionSubsystem::IsInSession() const
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	return Sessions.IsValid() && Sessions->GetNamedSession(IBSessionName) != nullptr;
}

void UIBSessionSubsystem::ReportStatus(EIBSessionStatus Status, const FString& Message)
{
	UE_LOG(LogIronBreach, Log, TEXT("Session status: %s"), *Message);
	OnSessionStatusChanged.Broadcast(Status, FText::FromString(Message));
}

IOnlineSessionPtr UIBSessionSubsystem::GetSessionInterface() const
{
	if (IOnlineSubsystem* OSS = Online::GetSubsystem(GetWorld()))
	{
		return OSS->GetSessionInterface();
	}
	return nullptr;
}

bool UIBSessionSubsystem::IsLANFallback() const
{
	// PIE and machines without Steam running fall back to the NULL subsystem -> treat as LAN.
	const IOnlineSubsystem* OSS = Online::GetSubsystem(GetWorld());
	return !OSS || OSS->GetSubsystemName() == TEXT("NULL");
}

void UIBSessionSubsystem::DestroyThen(TFunction<void()> Continuation)
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid() || !Sessions->GetNamedSession(IBSessionName))
	{
		Continuation();
		return;
	}

	PostDestroyContinuation = MoveTemp(Continuation);
	PreDestroyHandle = Sessions->AddOnDestroySessionCompleteDelegate_Handle(
		FOnDestroySessionCompleteDelegate::CreateUObject(this, &UIBSessionSubsystem::OnPreDestroyComplete));

	UE_LOG(LogIronBreach, Log, TEXT("Session: tearing down the stale local session before the next step"));
	if (!Sessions->DestroySession(IBSessionName))
	{
		// Refused outright: proceed anyway rather than strand the player.
		Sessions->ClearOnDestroySessionCompleteDelegate_Handle(PreDestroyHandle);
		TFunction<void()> Next = MoveTemp(PostDestroyContinuation);
		PostDestroyContinuation = nullptr;
		if (Next) { Next(); }
	}
}

void UIBSessionSubsystem::OnPreDestroyComplete(FName /*SessionName*/, bool /*bWasSuccessful*/)
{
	if (IOnlineSessionPtr Sessions = GetSessionInterface())
	{
		Sessions->ClearOnDestroySessionCompleteDelegate_Handle(PreDestroyHandle);
	}
	TFunction<void()> Next = MoveTemp(PostDestroyContinuation);
	PostDestroyContinuation = nullptr;
	if (Next) { Next(); }
}

void UIBSessionSubsystem::IBHost()
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid())
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBHost: no session interface (Online Subsystem missing?)"));
		ReportStatus(EIBSessionStatus::Failed, TEXT("ONLINE SERVICE UNAVAILABLE"));
		return;
	}

	ReportStatus(EIBSessionStatus::Hosting, TEXT("STANDING UP SERVER..."));

	// Tear down any stale session first (re-hosting after a return to the
	// menu, or a client entry left over from a dropped host) — properly, then create.
	DestroyThen([this]() { CreateSessionNow(); });
}

void UIBSessionSubsystem::CreateSessionNow()
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid())
	{
		ReportStatus(EIBSessionStatus::Failed, TEXT("ONLINE SERVICE UNAVAILABLE"));
		return;
	}

	FOnlineSessionSettings Settings;
	Settings.NumPublicConnections = FMath::Max(MaxPlayers, 2);
	Settings.bShouldAdvertise = true;        // Discoverable via FindSessions
	Settings.bAllowJoinInProgress = true;    // Drop-in co-op
	Settings.bIsLANMatch = IsLANFallback();
	Settings.bUsesPresence = true;           // Steam friends / invites path
	Settings.bAllowJoinViaPresence = true;
	Settings.bUseLobbiesIfAvailable = true;  // Steam lobbies back the session

	CreateCompleteHandle = Sessions->AddOnCreateSessionCompleteDelegate_Handle(
		FOnCreateSessionCompleteDelegate::CreateUObject(this, &UIBSessionSubsystem::OnCreateSessionComplete));

	UE_LOG(LogIronBreach, Log, TEXT("IBHost: creating session (%s, %d slots)"),
		Settings.bIsLANMatch ? TEXT("LAN/NULL") : TEXT("online"), Settings.NumPublicConnections);

	if (!Sessions->CreateSession(0 /*hosting local player*/, IBSessionName, Settings))
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBHost: CreateSession call failed immediately"));
		Sessions->ClearOnCreateSessionCompleteDelegate_Handle(CreateCompleteHandle);
		ReportStatus(EIBSessionStatus::Failed, TEXT("COULD NOT CREATE SESSION"));
	}
}

void UIBSessionSubsystem::OnCreateSessionComplete(FName SessionName, bool bWasSuccessful)
{
	if (IOnlineSessionPtr Sessions = GetSessionInterface())
	{
		Sessions->ClearOnCreateSessionCompleteDelegate_Handle(CreateCompleteHandle);
	}

	if (!bWasSuccessful)
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBHost: session creation failed"));
		ReportStatus(EIBSessionStatus::Failed, TEXT("SESSION CREATION FAILED"));
		return;
	}

	if (bLobbyBeforeDeploy)
	{
		// Dwell in the menu as a live lobby: the squad assembles in front of
		// the banners, then the host pulls the trigger (IBDeploy).
		UE_LOG(LogIronBreach, Log, TEXT("IBHost: session live - lobby-hosting %s"), *LobbyTravelURL);
		ReportStatus(EIBSessionStatus::LobbyLive, TEXT("LOBBY LIVE - SQUAD CAN JOIN"));
		if (UWorld* World = GetWorld())
		{
			World->ServerTravel(LobbyTravelURL);
		}
		return;
	}

	UE_LOG(LogIronBreach, Log, TEXT("IBHost: session live - listen-hosting %s"), *HostTravelURL);
	ReportStatus(EIBSessionStatus::HostLive, TEXT("SERVER LIVE - DEPLOYING..."));

	if (UWorld* World = GetWorld())
	{
		World->ServerTravel(HostTravelURL);
	}
}

void UIBSessionSubsystem::IBDeploy()
{
	UWorld* World = GetWorld();
	if (!World || World->GetNetMode() == NM_Client)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("IBDeploy: only the host can deploy the squad"));
		return;
	}
	UE_LOG(LogIronBreach, Log, TEXT("IBDeploy: taking the squad to %s"), *HostTravelURL);
	ReportStatus(EIBSessionStatus::Deploying, TEXT("DEPLOYING SQUAD..."));
	World->ServerTravel(HostTravelURL);
}

void UIBSessionSubsystem::IBJoin()
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid())
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: no session interface (Online Subsystem missing?)"));
		ReportStatus(EIBSessionStatus::Failed, TEXT("ONLINE SERVICE UNAVAILABLE"));
		return;
	}

	SessionSearch = MakeShareable(new FOnlineSessionSearch());
	SessionSearch->MaxSearchResults = 32;
	SessionSearch->bIsLanQuery = IsLANFallback();
	// Literal key instead of the SEARCH_PRESENCE macro — its header kept moving between
	// engine versions (5.8 broke it again); the FName value is stable API surface.
	static const FName SearchPresenceKey(TEXT("PRESENCESEARCH"));
	SessionSearch->QuerySettings.Set(SearchPresenceKey, true, EOnlineComparisonOp::Equals);

	FindCompleteHandle = Sessions->AddOnFindSessionsCompleteDelegate_Handle(
		FOnFindSessionsCompleteDelegate::CreateUObject(this, &UIBSessionSubsystem::OnFindSessionsComplete));

	UE_LOG(LogIronBreach, Log, TEXT("IBJoin: searching (%s)..."), SessionSearch->bIsLanQuery ? TEXT("LAN/NULL") : TEXT("online"));
	ReportStatus(EIBSessionStatus::Searching, TEXT("SCANNING FOR SQUADS..."));

	if (!Sessions->FindSessions(0, SessionSearch.ToSharedRef()))
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: FindSessions call failed immediately"));
		Sessions->ClearOnFindSessionsCompleteDelegate_Handle(FindCompleteHandle);
		ReportStatus(EIBSessionStatus::Failed, TEXT("SEARCH COULD NOT START"));
	}
}

void UIBSessionSubsystem::OnFindSessionsComplete(bool bWasSuccessful)
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (Sessions.IsValid())
	{
		Sessions->ClearOnFindSessionsCompleteDelegate_Handle(FindCompleteHandle);
	}

	if (!bWasSuccessful || !Sessions.IsValid() || !SessionSearch.IsValid() || SessionSearch->SearchResults.Num() == 0)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("IBJoin: no sessions found"));
		ReportStatus(EIBSessionStatus::NoneFound, TEXT("NO SQUADS ON THE NET - HOST ONE?"));
		return;
	}

	UE_LOG(LogIronBreach, Log, TEXT("IBJoin: %d session(s) found - joining the first"), SessionSearch->SearchResults.Num());
	ReportStatus(EIBSessionStatus::Joining, TEXT("SQUAD FOUND - LINKING..."));
	JoinSearchResult(SessionSearch->SearchResults[0]);
}

void UIBSessionSubsystem::JoinSearchResult(const FOnlineSessionSearchResult& Result)
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid()) { return; }

	// Everyone hosts their own world now, so a join almost always starts from
	// inside a session: tear ours down properly, THEN join theirs.
	PendingJoinResult = MakeShared<FOnlineSessionSearchResult>(Result);
	DestroyThen([this]() { JoinPendingNow(); });
}

void UIBSessionSubsystem::JoinPendingNow()
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid() || !PendingJoinResult.IsValid()) { return; }

	const FOnlineSessionSearchResult Result = *PendingJoinResult;
	PendingJoinResult.Reset();

	JoinCompleteHandle = Sessions->AddOnJoinSessionCompleteDelegate_Handle(
		FOnJoinSessionCompleteDelegate::CreateUObject(this, &UIBSessionSubsystem::OnJoinSessionComplete));

	if (!Sessions->JoinSession(0, IBSessionName, Result))
	{
		UE_LOG(LogIronBreach, Error, TEXT("JoinSearchResult: JoinSession call failed immediately"));
		Sessions->ClearOnJoinSessionCompleteDelegate_Handle(JoinCompleteHandle);
		ReportStatus(EIBSessionStatus::JoinFailed, TEXT("LINK REFUSED"));
	}
}

void UIBSessionSubsystem::OnJoinSessionComplete(FName SessionName, EOnJoinSessionCompleteResult::Type Result)
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (Sessions.IsValid())
	{
		Sessions->ClearOnJoinSessionCompleteDelegate_Handle(JoinCompleteHandle);
	}

	if (Result != EOnJoinSessionCompleteResult::Success || !Sessions.IsValid())
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: join failed (%d)"), static_cast<int32>(Result));
		ReportStatus(EIBSessionStatus::JoinFailed, TEXT("COULD NOT JOIN SQUAD"));
		return;
	}

	FString ConnectString;
	if (!Sessions->GetResolvedConnectString(SessionName, ConnectString))
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: could not resolve connect string"));
		ReportStatus(EIBSessionStatus::JoinFailed, TEXT("HOST UNREACHABLE"));
		return;
	}

	UE_LOG(LogIronBreach, Log, TEXT("IBJoin: travelling to host at %s"), *ConnectString);
	ReportStatus(EIBSessionStatus::Joined, TEXT("LINKED - DEPLOYING..."));

	if (APlayerController* PC = GetGameInstance()->GetFirstLocalPlayerController())
	{
		PC->ClientTravel(ConnectString, ETravelType::TRAVEL_Absolute);
	}
}

void UIBSessionSubsystem::IBLeave()
{
	IOnlineSessionPtr Sessions = GetSessionInterface();

	// No interface or no live session (solo PIE, or already torn down):
	// nothing to unregister — just go home.
	if (!Sessions.IsValid() || !Sessions->GetNamedSession(IBSessionName))
	{
		UE_LOG(LogIronBreach, Log, TEXT("IBLeave: no active session — travelling to menu"));
		TravelToMainMenu();
		return;
	}

	// DestroySession is the correct verb on BOTH ends: the host tears the
	// session down, a client unregisters its local entry so the next IBJoin
	// starts clean. Travel waits for the callback — travelling mid-teardown
	// leaves Steam thinking you're still in a lobby.
	LeaveDestroyHandle = Sessions->AddOnDestroySessionCompleteDelegate_Handle(
		FOnDestroySessionCompleteDelegate::CreateUObject(this, &UIBSessionSubsystem::OnLeaveDestroyComplete));

	UE_LOG(LogIronBreach, Log, TEXT("IBLeave: destroying session..."));
	ReportStatus(EIBSessionStatus::Leaving, TEXT("RETURNING TO BASE..."));

	if (!Sessions->DestroySession(IBSessionName))
	{
		UE_LOG(LogIronBreach, Warning, TEXT("IBLeave: DestroySession call failed immediately — travelling anyway"));
		Sessions->ClearOnDestroySessionCompleteDelegate_Handle(LeaveDestroyHandle);
		TravelToMainMenu();
	}
}

void UIBSessionSubsystem::OnLeaveDestroyComplete(FName /*SessionName*/, bool bWasSuccessful)
{
	if (IOnlineSessionPtr Sessions = GetSessionInterface())
	{
		Sessions->ClearOnDestroySessionCompleteDelegate_Handle(LeaveDestroyHandle);
	}

	// Success or not, the player asked to leave — don't trap them in-world
	// because the online backend hiccuped.
	UE_LOG(LogIronBreach, Log, TEXT("IBLeave: session destroy %s — travelling to menu"),
		bWasSuccessful ? TEXT("succeeded") : TEXT("FAILED (leaving anyway)"));
	TravelToMainMenu();
}

void UIBSessionSubsystem::TravelToMainMenu()
{
	if (APlayerController* PC = GetGameInstance() ? GetGameInstance()->GetFirstLocalPlayerController() : nullptr)
	{
		// Absolute client travel: works identically for host, client, and
		// solo — everyone just loads the menu map locally.
		PC->ClientTravel(LeaveTravelURL, ETravelType::TRAVEL_Absolute);
	}
}
