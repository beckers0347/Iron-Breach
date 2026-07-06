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

void UIBSessionSubsystem::IBHost()
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid())
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBHost: no session interface (Online Subsystem missing?)"));
		return;
	}

	// Tear down any stale session first (e.g. re-hosting after returning to menu).
	if (Sessions->GetNamedSession(IBSessionName))
	{
		Sessions->DestroySession(IBSessionName);
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
		return;
	}

	UE_LOG(LogIronBreach, Log, TEXT("IBHost: session live - listen-hosting %s"), *HostTravelURL);

	if (UWorld* World = GetWorld())
	{
		World->ServerTravel(HostTravelURL);
	}
}

void UIBSessionSubsystem::IBJoin()
{
	IOnlineSessionPtr Sessions = GetSessionInterface();
	if (!Sessions.IsValid())
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: no session interface (Online Subsystem missing?)"));
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

	if (!Sessions->FindSessions(0, SessionSearch.ToSharedRef()))
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: FindSessions call failed immediately"));
		Sessions->ClearOnFindSessionsCompleteDelegate_Handle(FindCompleteHandle);
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
		return;
	}

	UE_LOG(LogIronBreach, Log, TEXT("IBJoin: %d session(s) found - joining the first"), SessionSearch->SearchResults.Num());

	JoinCompleteHandle = Sessions->AddOnJoinSessionCompleteDelegate_Handle(
		FOnJoinSessionCompleteDelegate::CreateUObject(this, &UIBSessionSubsystem::OnJoinSessionComplete));

	if (!Sessions->JoinSession(0, IBSessionName, SessionSearch->SearchResults[0]))
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: JoinSession call failed immediately"));
		Sessions->ClearOnJoinSessionCompleteDelegate_Handle(JoinCompleteHandle);
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
		return;
	}

	FString ConnectString;
	if (!Sessions->GetResolvedConnectString(SessionName, ConnectString))
	{
		UE_LOG(LogIronBreach, Error, TEXT("IBJoin: could not resolve connect string"));
		return;
	}

	UE_LOG(LogIronBreach, Log, TEXT("IBJoin: travelling to host at %s"), *ConnectString);

	if (APlayerController* PC = GetGameInstance()->GetFirstLocalPlayerController())
	{
		PC->ClientTravel(ConnectString, ETravelType::TRAVEL_Absolute);
	}
}
