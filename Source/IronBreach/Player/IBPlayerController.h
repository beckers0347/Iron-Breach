#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "Player/IBCharacterTypes.h"
#include "IBPlayerController.generated.h"

class UInputMappingContext;
class UInputAction;

/**
 * Project player controller. Its first job: menu input.
 *
 * Menu keys live HERE, not on any pawn, because the controller is the one
 * player-side object that never churns — it survives death (menus must open
 * while you wait out the respawn timer), and it survives the infantry<->mech
 * possession swap (a Caryatid gunner still needs the map). A pawn-bound
 * binding dies with the pawn; this one doesn't.
 *
 * MenuMappingContext is added at priority 1 — above the pawn contexts at 0 —
 * so menu keys win regardless of which pawn's IMC is active. The actions only
 * OPEN screens; once a menu is up the game runs UI-only input (controller
 * input goes quiet) and closing/cycling belongs to the screen widgets.
 *
 * Shane: reparent a BP to this, assign the IMC + four actions, set it as the
 * GameMode's Player Controller Class (MENUS_UI_WIRING.md §3). Front-end/HUD
 * logic you'd normally put on a controller BP goes in the child as usual.
 */
UCLASS()
class IRONBREACH_API AIBPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	/**
	 * Send the local operative (UIBCharacterSubsystem's active character) to
	 * the server so this player's PlayerState carries callsign/class/gender for
	 * everyone. Runs on BeginPlay for every level; the main menu calls it again
	 * the moment an operative is chosen or switched. Safe with no character.
	 */
	UFUNCTION(BlueprintCallable, Category = "Operative")
	void PushOperativeIdentity();

protected:
	virtual void BeginPlay() override;
	virtual void SetupInputComponent() override;

	/** Clients receive their PlayerState after BeginPlay — push again when it lands. */
	virtual void OnRep_PlayerState() override;

	/** Added at priority 1 (pawn contexts sit at 0) for every local player. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Menus")
	TObjectPtr<UInputMappingContext> MenuMappingContext;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Menus")
	TObjectPtr<UInputAction> OpenInventoryAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Menus")
	TObjectPtr<UInputAction> OpenMapAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Menus")
	TObjectPtr<UInputAction> OpenLedgerAction;

	/** Escape / Start: the pause-menu-that-isn't (co-op never pauses). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input|Menus")
	TObjectPtr<UInputAction> OpenSystemAction;

	// --- HUD layer (objective banner + loot toasts) ---
	// Spawned here because the controller survives death and the mech swap;
	// the C++ widget classes self-build, so these work with zero content.
	// Point them at WBP children later to reskin.

	UPROPERTY(EditDefaultsOnly, Category = "HUD")
	TSubclassOf<class UIBObjectiveWidget> ObjectiveWidgetClass;

	UPROPERTY(EditDefaultsOnly, Category = "HUD")
	TSubclassOf<class UIBLootToastWidget> LootToastWidgetClass;

	UPROPERTY(Transient)
	TObjectPtr<class UIBObjectiveWidget> ObjectiveWidget;

	UPROPERTY(Transient)
	TObjectPtr<class UIBLootToastWidget> LootToastWidget;

	void OpenInventoryMenu();
	void OpenMapMenu();
	void OpenLedgerMenu();
	void OpenSystemMenu();

private:
	void ToggleMenuScreen(FName ScreenId) const;
};
