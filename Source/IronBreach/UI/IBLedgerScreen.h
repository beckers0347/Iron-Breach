#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "Items/IBItemTypes.h"
#include "IBLedgerScreen.generated.h"

class UUniformGridPanel;
class UTextBlock;
class UIBItemTileWidget;
class UIBItemDefinition;
class UIBLedgerSubsystem;

/**
 * The Ledger — Destiny's Collections wearing Breakwater colors. Every
 * ledger-visible item in the project, category-tabbed; discovered entries
 * render live, undiscovered as silhouettes (rarity frame dimly visible — the
 * hook that makes people chase).
 *
 * Catalog comes from the Asset Manager, discovery from UIBLedgerSubsystem;
 * this screen is a pure view. Same optional-bind pattern as the inventory
 * screen: ItemGrid + ProgressText, GridTileClass = WBP_ItemTile.
 */
UCLASS(Abstract)
class IRONBREACH_API UIBLedgerScreen : public UIBMenuScreen
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Ledger")
	void SetCategoryFilter(EIBItemCategory Category);

	UFUNCTION(BlueprintPure, Category = "Ledger")
	EIBItemCategory GetCategoryFilter() const { return CategoryFilter; }

protected:
	virtual void NativeScreenOpened() override;

	/** Shane's detail pane. Undiscovered entries pass bDiscovered=false — show
	 *  "DATA SEALED" styling, hide flavor, keep the chase honest. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Ledger", meta = (DisplayName = "On Entry Focused"))
	void BP_OnEntryFocused(const UIBItemDefinition* Definition, bool bDiscovered);

	UFUNCTION(BlueprintImplementableEvent, Category = "Ledger", meta = (DisplayName = "On Entry Unfocused"))
	void BP_OnEntryUnfocused();

	UFUNCTION()
	void HandleEntryDiscovered(const UIBItemDefinition* Definition);

	UFUNCTION()
	void HandleTileHoverChanged(UIBItemTileWidget* Tile, bool bHovered);

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Ledger")
	TObjectPtr<UUniformGridPanel> ItemGrid;

	/** "12 / 48 CATALOGUED" style counter for the current category. */
	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Ledger")
	TObjectPtr<UTextBlock> ProgressText;

	UPROPERTY(EditDefaultsOnly, Category = "Ledger")
	TSubclassOf<UIBItemTileWidget> GridTileClass;

	UPROPERTY(EditDefaultsOnly, Category = "Ledger", meta = (ClampMin = "1"))
	int32 GridColumns = 8;

private:
	void RebuildGrid();
	UIBLedgerSubsystem* GetLedger() const;

	EIBItemCategory CategoryFilter = EIBItemCategory::Weapon;
	bool bDiscoveryBound = false;
};
