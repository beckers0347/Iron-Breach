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

	/** Host-only: ServerTravel the whole squad to a specific map — the Watch's
	 *  breach board calls this with the armed destination. The session survives
	 *  the map change (?listen is appended while one is live); standalone just
	 *  travels. */
	UFUNCTION(BlueprintCallable, Exec, Category = "IronBreach|Online")
	void IBDeployTo(const FString& MapPath);

	/** Host-only: bring the squad back to the Watch (the lobby map) without
	 *  tearing the session down — the mid-mission "return to orbit". */
	UFUNCTION(BlueprintCallable, Exec, Category = "IronBreach|Online")
	void IBReturnToWatch();

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

	/** Pre-deploy lobby — THE WATCH. ON: deploying from the operative sheet
	 *  stands up the session and lands the host in the menu map as a live
	 *  lobby where the breach board (UIBWatchScreen) opens; friends join
	 *  there, anyone proposes a destination, the host confirms, the board
	 *  counts down and IBDeployTo takes the whole squad. OFF = legacy: straight
	 *  into HostTravelURL, squad forms from the in-game Squad tab. */
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
	/** Input-mode law, enforced globally: UIOnly survives map travel and
	 *  bricks the next level, so every travel (host ServerTravel, client
	 *  follow, solo OpenLevel) resets the local player to GameOnly first.
	 *  Front-end widgets re-take UIOnly when they spawn. */
	void HandlePreLoadMap(const FString& MapName);
	FDelegateHandle PreLoadMapHandle;

	/** Log + broadcast in one move so the two can never drift apart. */
	void ReportStatus(EIBSessionStatus Status, const FString& Message);
	void OnCreateSessionComplete(FName SessionName, bool bWasSuccessful);
	void OnFindSessionsComplete(bool bWasSuccessful);
	void OnJoinSessionComplete(FName SessionName, EOnJoinSessionCompleteResult::Type Result);
	void OnLeaveDestroyComplete(FName SessionName, bool bWasSuccessful);

	/** The IBLeave landing: travel the first local player to LeaveTravelURL. */
	void TravelToMainMenu();

	/** Tear down the local named session if one exists, THEN run Continuation.
	 *  Steam destroys asynchronously — a create/join fired on the same frame
	 *  fails with "session already exists". Every player now hosts their own
	 *  world, so joining a friend always starts from "in a session". */
	void DestroyThen(TFunction<void()> Continuation);
	void OnPreDestroyComplete(FName SessionName, bool bWasSuccessful);
	void CreateSessionNow();
	void JoinPendingNow();

	TFunction<void()> PostDestroyContinuation;
	FDelegateHandle PreDestroyHandle;
	TSharedPtr<FOnlineSessionSearchResult> PendingJoinResult;

	IOnlineSessionPtr GetSessionInterface() const;
	bool IsLANFallback() const;
	/** Match every listen URL to the active session transport, including when
	 *  Steam loaded its socket plugin but failed to initialize its online service. */
	FString BuildListenTravelURL(const FString& MapURL) const;

	TSharedPtr<FOnlineSessionSearch> SessionSearch;

	void OnInviteAccepted(const bool bWasSuccessful, const int32 ControllerId,
		FUniqueNetIdPtr UserId, const FOnlineSessionSearchResult& InviteResult);

	FDelegateHandle CreateCompleteHandle;
	FDelegateHandle FindCompleteHandle;
	FDelegateHandle JoinCompleteHandle;
	FDelegateHandle LeaveDestroyHandle;
	FDelegateHandle InviteAcceptedHandle;
};
