#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Interfaces/OnlineSessionInterface.h" // IOnlineSessionPtr + completion delegate types
#include "IBSessionSubsystem.generated.h"

class FOnlineSessionSearch;

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
	/** Create a listen session and travel to the gameplay map. */
	UFUNCTION(BlueprintCallable, Exec, Category = "IronBreach|Online")
	void IBHost();

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

	/** Map travelled to on successful host. Exposed so a future front-end can pick zones. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	FString HostTravelURL = TEXT("/Game/Lvl_Plains?listen");

	/** Where IBLeave lands. Matches DefaultEngine.ini's GameDefaultMap. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	FString LeaveTravelURL = TEXT("/Game/FirstPerson/Lvl_MainMenu");

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	int32 MaxPlayers = 4;

private:
	void OnCreateSessionComplete(FName SessionName, bool bWasSuccessful);
	void OnFindSessionsComplete(bool bWasSuccessful);
	void OnJoinSessionComplete(FName SessionName, EOnJoinSessionCompleteResult::Type Result);
	void OnLeaveDestroyComplete(FName SessionName, bool bWasSuccessful);

	/** The IBLeave landing: travel the first local player to LeaveTravelURL. */
	void TravelToMainMenu();

	IOnlineSessionPtr GetSessionInterface() const;
	bool IsLANFallback() const;

	TSharedPtr<FOnlineSessionSearch> SessionSearch;

	FDelegateHandle CreateCompleteHandle;
	FDelegateHandle FindCompleteHandle;
	FDelegateHandle JoinCompleteHandle;
	FDelegateHandle LeaveDestroyHandle;
};
