#pragma once

#include "CoreMinimal.h"
#include "Subsystems/LocalPlayerSubsystem.h"
#include "IBMenuSubsystem.generated.h"

class UIBMenuScreen;
class APlayerController;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnGameMenuOpened, FName, ScreenId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnGameMenuClosed);

/**
 * Owns the full-screen menu layer for one local player (split-screen safe by
 * construction — it's a LocalPlayerSubsystem). One screen active at a time,
 * Destiny-style: open, cycle sideways through the ring, close back to the game.
 *
 * Purely client/UI-side — decides no truth, so it lives outside the authority
 * path entirely (uq7). Screens it opens talk to replicated state (inventory,
 * map subsystem) through their own request seams.
 *
 * Signals, not references (the ZoneConfirmed pattern): HUD dims, weapon lowers,
 * and the menu hum (roadmap's "Long Nine at 1/100×") all attach to
 * OnMenuOpened/OnMenuClosed from BP. Nothing needs to know this class exists.
 *
 * Screens are defined in Project Settings > Iron Breach UI (UIBUISettings);
 * gameplay opens them via ToggleScreen — see the AIBCharacter_Infantry patch.
 */
UCLASS()
class IRONBREACH_API UIBMenuSubsystem : public ULocalPlayerSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnGameMenuOpened OnMenuOpened;

	UPROPERTY(BlueprintAssignable, Category = "Menu")
	FOnGameMenuClosed OnMenuClosed;

	/** Open if closed or on another screen; close if this screen is already up.
	 *  The one call gameplay input needs. */
	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ToggleScreen(FName ScreenId);

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void OpenScreen(FName ScreenId);

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void CloseMenu();

	/** +1 / -1 through the settings' screen order (Q/E, shoulders). Wraps. */
	UFUNCTION(BlueprintCallable, Category = "Menu")
	void CycleScreen(int32 Direction);

	UFUNCTION(BlueprintPure, Category = "Menu")
	bool IsMenuOpen() const { return ActiveScreen != nullptr; }

	UFUNCTION(BlueprintPure, Category = "Menu")
	FName GetActiveScreenId() const { return ActiveScreenId; }

private:
	APlayerController* GetOwningPC() const;
	UIBMenuScreen* GetOrCreateScreen(FName ScreenId);
	void ApplyMenuInputMode(UIBMenuScreen* Screen);
	void RestoreGameInputMode();

	/** This subsystem outlives map travel (LocalPlayer scope) but its cached
	 *  widgets do NOT — they were created against the previous world's
	 *  PlayerController. Called on every entry point to drop corpses before
	 *  they're touched (found chasing the IBLeave flow: leave to menu, host
	 *  again, press Tab → dead-world widget without this). */
	void PurgeStaleScreens(const APlayerController* CurrentPC);

	/** Screens are built once and reused so grid layouts, pan/zoom state, and
	 *  selected tabs survive reopening (Destiny keeps your place; so do we). */
	UPROPERTY()
	TMap<FName, TObjectPtr<UIBMenuScreen>> ScreenCache;

	UPROPERTY()
	TObjectPtr<UIBMenuScreen> ActiveScreen;

	FName ActiveScreenId;

	/** Toggle debounce (raw Escape floor + IA route can fire on one press). */
	FName LastToggleId;
	double LastToggleTime = -1.0;
};
