#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "IBPlayerState.generated.h"

class UIBInventoryComponent;
class UIBItemDefinition;

/**
 * Project player state: the durable per-player home. Inventory lives here so
 * loadout survives respawns and the infantry↔Caryatid pawn swap.
 *
 * Wiring (Shane, per §3 ownership — GameMode content is yours): set
 * BP_IronBreachGameMode's Player State Class to a BP child of this, and fill
 * StarterLoadout there so first-run players have something on the grid.
 * MENUS_UI_WIRING.md §3 has the exact clicks.
 */
UCLASS()
class IRONBREACH_API AIBPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	AIBPlayerState();

	UFUNCTION(BlueprintPure, Category = "Inventory")
	UIBInventoryComponent* GetInventory() const { return InventoryComponent; }

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UIBInventoryComponent> InventoryComponent;

	/** Granted once, server-side, on first BeginPlay. Placeholder for the real
	 *  loot/persistence spine (M2 §3.3) — replace with profile load when saves land. */
	UPROPERTY(EditDefaultsOnly, Category = "Inventory")
	TArray<TObjectPtr<UIBItemDefinition>> StarterLoadout;

	/** Auto-equip each starter item whose definition has an equip slot. */
	UPROPERTY(EditDefaultsOnly, Category = "Inventory")
	bool bAutoEquipStarters = true;

private:
	bool bStartersGranted = false;
};
