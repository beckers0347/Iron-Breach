#pragma once

#include "CoreMinimal.h"
#include "UI/IBMenuScreen.h"
#include "Items/IBItemTypes.h"
#include "IBInventoryScreen.generated.h"

class UUniformGridPanel;
class UTextBlock;
class UIBItemTileWidget;
class UIBInventoryComponent;

/**
 * The character/inventory screen — Destiny's layout grammar in Iron Breach
 * skin: equipped wells around the frame (weapons left, armor right in the WBP),
 * Clearance Rating up top, category-filtered backpack grid center/bottom.
 *
 * Interaction model, click-to-equip for pass 1:
 *   grid tile click ..... RequestEquip (server decides; replication redraws)
 *   equipped tile click . RequestUnequip
 *   hover ............... BP_OnItemFocused/Unfocused → Shane's details pane
 *
 * The C++ builds and wires everything; the WBP child is layout only. Name the
 * optional-bind widgets exactly as below and they light up (full table in
 * MENUS_UI_WIRING.md §5). Nothing here touches authority — every mutation goes
 * through the inventory component's request seam.
 */
UCLASS(Abstract)
class IRONBREACH_API UIBInventoryScreen : public UIBMenuScreen
{
	GENERATED_BODY()

public:
	/** Grid filter (wire category tab buttons to this in the WBP). */
	UFUNCTION(BlueprintCallable, Category = "Inventory")
	void SetCategoryFilter(EIBItemCategory Category);

	UFUNCTION(BlueprintPure, Category = "Inventory")
	EIBItemCategory GetCategoryFilter() const { return CategoryFilter; }

	UFUNCTION(BlueprintPure, Category = "Inventory")
	UIBInventoryComponent* GetInventory() const;

protected:
	virtual void NativeScreenOpened() override;
	virtual void NativeScreenClosed() override;

	/** Shane's details-pane feed. bEquipped distinguishes well vs backpack. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Inventory", meta = (DisplayName = "On Item Focused"))
	void BP_OnItemFocused(const FIBItemInstance& Item, bool bEquipped);

	UFUNCTION(BlueprintImplementableEvent, Category = "Inventory", meta = (DisplayName = "On Item Unfocused"))
	void BP_OnItemUnfocused();

	UFUNCTION()
	void HandleInventoryChanged();

	UFUNCTION()
	// NB: parameter cannot be named 'Slot' — UWidget already declares a member of that
	// name and UHT rejects the shadowing on UFUNCTION signatures.
	void HandleEquipmentChanged(EIBEquipSlot ChangedSlot, const FIBItemInstance& ChangedItem);

	UFUNCTION()
	void HandleTileClicked(UIBItemTileWidget* Tile);

	UFUNCTION()
	void HandleTileHoverChanged(UIBItemTileWidget* Tile, bool bHovered);

	// ---- Optional-bind layout hooks (names matter) ----

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UUniformGridPanel> ItemGrid;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UTextBlock> ClearanceText;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_WeaponPrimary;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_WeaponSpecial;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_WeaponHeavy;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_ArmorHead;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_ArmorChest;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_ArmorArms;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_ArmorLegs;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Inventory")
	TObjectPtr<UIBItemTileWidget> Tile_GearAntiKaiju;

	/** WBP_ItemTile — used for every backpack grid cell. */
	UPROPERTY(EditDefaultsOnly, Category = "Inventory")
	TSubclassOf<UIBItemTileWidget> GridTileClass;

	UPROPERTY(EditDefaultsOnly, Category = "Inventory", meta = (ClampMin = "1"))
	int32 GridColumns = 6;

private:
	void RebuildAll();
	void RebuildGrid();
	void RefreshEquipmentWells();
	void BindInventory();
	void UnbindInventory();
	UIBItemTileWidget* GetWellForSlot(EIBEquipSlot InSlot) const;
	void WireTile(UIBItemTileWidget* Tile);

	UPROPERTY()
	TObjectPtr<UIBInventoryComponent> BoundInventory;

	EIBItemCategory CategoryFilter = EIBItemCategory::Weapon;
};
