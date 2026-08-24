#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Interfaces/OnlineSessionInterface.h" // IOnlineSessionPtr + completion delegate types
#include "IBSessionSubsystem.generated.h"

class FOnlineSessionSearch;

/** Every beat of the host/join flow, for front-end feedback. A silent menu
 *  reads as a broken menu — the demo build cannot afford that. */
UENUM(BlueprintType)
enum class EIBSessionStatus : uint8
{
	Idle,
	Hosting,     // CreateSession in flight
	HostLive,    // Session up, server travel imminent
	Searching,   // FindSessions in flight
	NoneFound,   // Search returned empty — terminal, re-enable the UI
	Joining,     // Result picked, JoinSession/travel in flight
	Joined,      // Connect string resolved, client travel imminent
	JoinFailed,  // Terminal, re-enable the UI
	Leaving,
	Failed,      // Any hard failure (no OSS, immediate call rejection, create failed)
	LobbyLive,   // Hosting a pre-deploy lobby in the menu level — squad can join
	Deploying    // Host pulled the trigger: ServerTravel to the mission map
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnIBSessionStatusChanged, EIBSessionStatus, Status, const FText&, Message);

/**
 * Minimal session layer for the M2 spike (ADR-002: listen server, Steam-first).
 *
 * Console testing (no UI needed):
 *   IBHost   - create a session and listen-host Lvl_Plains
 *   IBJoin   - find the first session and join it
 *
 * Uses whatever Online Subsystem is active: Steam in packaged/dev builds (AppID 480),
 * the NULL subsystem (LAN) in PIE. Shane's front-end can call Host/Join from Blueprints later.
 */
UCLASS()
class IRONBREACH_API UIBSessionSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Create a listen session. With bLobbyBeforeDeploy (default) the host
	 *  stays in the menu level as a live lobby — friends join THERE, banners
	 *  fill in, and IBDeploy launches the squad. Legacy behavior (straight to
	 *  the mission map) with the flag off. */
	UFUNCTION(BlueprintCallable, Exec, Category = "IronBreach|Online")
	void IBHost();

	/** Host-only: ServerTravel the whole lobby to the mission map. */
	UFUNCTION(BlueprintCallable, Exec, Category = "IronBreach|Online")
	void IBDeploy();

	/** Join a specific search result (friend join / accepted invite / picked
	 *  row). Native-only: FOnlineSessionSearchResult isn't a BP type. */
	void JoinSearchResult(const FOnlineSessionSearchResult& Result);

	/** True while a named game session exists on this machine (host or client). */
	UFUNCTION(BlueprintPure, Category = "IronBreach|Online")
	bool IsInSession() const;

	/** Find sessions and join the first result. */
	UFUNCTION(BlueprintCallable, Exec, Category = "IronBreach|Online")
	void IBJoin();

	/** Leave the current session and return to the main menu. Destroys the
	 *  local session entry (host OR client — DestroySession is how a client
	 *  cleanly unregisters too), then client-travels to LeaveTravelURL once
	 *  teardown completes. Safe to call solo: just travels. On a listen
	 *  server the host leaving ends the session for everyone (ADR-002). */
	UFUNCTION(BlueprintCallable, Exec, Category = "IronBreach|Online")
	void IBLeave();

	/** Map travelled to on successful host. Exposed so a future front-end can pick zones.
	 *  Points at the same mission map Solo uses — host and solo must land in the same
	 *  world for the demo (Lvl_Plains was the pre-FirstPerson spike map). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	FString HostTravelURL = TEXT("/Game/FirstPerson/Lvl_FirstPerson?listen");

	/** Pre-deploy lobby: host dwells in the menu level so the squad assembles
	 *  in front of the banners before anyone shoots anything. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	bool bLobbyBeforeDeploy = true;

	/** Where the lobby lives (must be ?listen — clients travel into it). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	FString LobbyTravelURL = TEXT("/Game/FirstPerson/Lvl_MainMenu?listen");

	/** Where IBLeave lands. Matches DefaultEngine.ini's GameDefaultMap. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	FString LeaveTravelURL = TEXT("/Game/FirstPerson/Lvl_MainMenu");

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	int32 MaxPlayers = 4;

	/** Front-end feedback channel (IBMainMenuWidget listens; BPs can too). */
	UPROPERTY(BlueprintAssignable, Category = "IronBreach|Online")
	FOnIBSessionStatusChanged OnSessionStatusChanged;

private:
	/** Log + broadcast in one move so the two can never drift apart. */
	void ReportStatus(EIBSessionStatus Status, const FString& Message);
	void OnCreateSessionComplete(FName SessionName, bool bWasSuccessful);
	void OnFindSessionsComplete(bool bWasSuccessful);
	void OnJoinSessionComplete(FName SessionName, EOnJoinSessionCompleteResult::Type Result);
	void OnLeaveDestroyComplete(FName SessionName, bool bWasSuccessful);

	/** The IBLeave landing: travel the first local player to LeaveTravelURL. */
	void TravelToMainMenu();

	IOnlineSessionPtr GetSessionInterface() const;
	bool IsLANFallback() const;

	TSharedPtr<FOnlineSessionSearch> SessionSearch;

	void OnInviteAccepted(const bool bWasSuccessful, const int32 ControllerId,
		FUniqueNetIdPtr UserId, const FOnlineSessionSearchResult& InviteResult);

	FDelegateHandle CreateCompleteHandle;
	FDelegateHandle FindCompleteHandle;
	FDelegateHandle JoinCompleteHandle;
	FDelegateHandle LeaveDestroyHandle;
	FDelegateHandle InviteAcceptedHandle;
};
