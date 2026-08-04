#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Items/IBItemTypes.h"
#include "IBItemTileWidget.generated.h"

class UImage;
class UTextBlock;
class UBorder;
class UIBItemDefinition;
class UIBItemTileWidget;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnItemTileClicked, UIBItemTileWidget*, Tile);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnItemTileHoverChanged, UIBItemTileWidget*, Tile, bool, bHovered);

/**
 * The one item square, everywhere: backpack grid cells, equipped-slot wells,
 * ledger entries. Three display modes:
 *   SetItem       — owned instance (icon, rarity frame, stack count)
 *   SetLocked     — ledger silhouette for undiscovered entries
 *   SetEmptySlot  — vacant equipment well
 *
 * Optional-bind visuals: build WBP_ItemTile with any/all of IconImage,
 * StackText, RarityBorder and the C++ drives them; BP_OnTileUpdated fires
 * after every state change for extra polish (masterwork glints, wear, etc.).
 */
UCLASS()
class IRONBREACH_API UIBItemTileWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Tile")
	FOnItemTileClicked OnTileClicked;

	UPROPERTY(BlueprintAssignable, Category = "Tile")
	FOnItemTileHoverChanged OnTileHoverChanged;

	UFUNCTION(BlueprintCallable, Category = "Tile")
	void SetItem(const FIBItemInstance& InItem);

	UFUNCTION(BlueprintCallable, Category = "Tile")
	void SetLocked(const UIBItemDefinition* InDefinition);

	UFUNCTION(BlueprintCallable, Category = "Tile")
	void SetEmptySlot(EIBEquipSlot InSlot);

	UFUNCTION(BlueprintPure, Category = "Tile")
	const FIBItemInstance& GetItem() const { return Item; }

	UFUNCTION(BlueprintPure, Category = "Tile")
	const UIBItemDefinition* GetDefinition() const { return Definition; }

	UFUNCTION(BlueprintPure, Category = "Tile")
	bool IsLockedEntry() const { return bLocked; }

	UFUNCTION(BlueprintPure, Category = "Tile")
	EIBEquipSlot GetRepresentedSlot() const { return RepresentedSlot; }

protected:
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseLeave(const FPointerEvent& InMouseEvent) override;

	UFUNCTION(BlueprintImplementableEvent, Category = "Tile", meta = (DisplayName = "On Tile Updated"))
	void BP_OnTileUpdated();

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Tile")
	TObjectPtr<UImage> IconImage;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Tile")
	TObjectPtr<UTextBlock> StackText;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Tile")
	TObjectPtr<UBorder> RarityBorder;

	/** Undiscovered-entry tint (ledger silhouettes). */
	UPROPERTY(EditDefaultsOnly, Category = "Tile")
	FLinearColor LockedTint = FLinearColor(0.02f, 0.02f, 0.03f, 1.0f);

private:
	void RefreshVisuals();

	FIBItemInstance Item;

	UPROPERTY()
	TObjectPtr<const UIBItemDefinition> Definition;

	EIBEquipSlot RepresentedSlot = EIBEquipSlot::None;
	bool bLocked = false;
};
