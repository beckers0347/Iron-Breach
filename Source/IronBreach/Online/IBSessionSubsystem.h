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

	/** Map travelled to on successful host. Exposed so a future front-end can pick zones. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	FString HostTravelURL = TEXT("/Game/Lvl_Plains?listen");

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "IronBreach|Online")
	int32 MaxPlayers = 4;

private:
	void OnCreateSessionComplete(FName SessionName, bool bWasSuccessful);
	void OnFindSessionsComplete(bool bWasSuccessful);
	void OnJoinSessionComplete(FName SessionName, EOnJoinSessionCompleteResult::Type Result);

	IOnlineSessionPtr GetSessionInterface() const;
	bool IsLANFallback() const;

	TSharedPtr<FOnlineSessionSearch> SessionSearch;

	FDelegateHandle CreateCompleteHandle;
	FDelegateHandle FindCompleteHandle;
	FDelegateHandle JoinCompleteHandle;
};
