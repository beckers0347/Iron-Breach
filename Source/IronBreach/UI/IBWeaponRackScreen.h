// IBWeaponRackScreen.h
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBWeaponRackScreen.generated.h"

class UUniformGridPanel;
class UTextBlock;
class UButton;
class UIBItemTileWidget;
class AIBWeaponRack;

/**
 * Contextual weapon-picker popup for AIBWeaponRack — NOT part of the tab-cycle
 * menu ring (UIBMenuScreen/UIBMenuSubsystem); this is a standalone widget shown
 * on interact and dismissed on close, the same shape as the mech's seat-select
 * popup (Create Widget -> Add to Viewport -> Input Mode UI Only), just for
 * weapons instead of seats.
 *
 * Same optional-bind philosophy as the other screens: build WBP_WeaponRack for
 * Shane's layout (ItemGrid + TitleText + CloseButton, GridTileClass =
 * WBP_ItemTile), or leave it bare and the C++ fallback below is fully functional.
 */
UCLASS()
class IRONBREACH_API UIBWeaponRackScreen : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Call right after CreateWidget, before AddToViewport. */
	void InitForRack(AIBWeaponRack* InRack);

	UFUNCTION(BlueprintPure, Category = "Weapon Rack")
	AIBWeaponRack* GetRack() const { return Rack; }

	/** Closes the popup and tells the rack to restore game input. Bind CloseButton
	 *  to this in the WBP if you replace the fallback layout's own button. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Rack")
	void RequestClose();

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UFUNCTION(BlueprintImplementableEvent, Category = "Weapon Rack", meta = (DisplayName = "On Opened"))
	void BP_OnOpened();

	UFUNCTION(BlueprintImplementableEvent, Category = "Weapon Rack", meta = (DisplayName = "On Closed"))
	void BP_OnClosed();

	UFUNCTION()
	void HandleTileClicked(UIBItemTileWidget* Tile);

	UFUNCTION()
	void HandleCloseClicked();

	UFUNCTION()
	void HandleStockChanged();

	// ---- Optional-bind layout hooks (names matter) ----

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Weapon Rack")
	TObjectPtr<UUniformGridPanel> ItemGrid;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Weapon Rack")
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Weapon Rack")
	TObjectPtr<UButton> CloseButton;

	UPROPERTY(EditDefaultsOnly, Category = "Weapon Rack")
	TSubclassOf<UIBItemTileWidget> GridTileClass;

	UPROPERTY(EditDefaultsOnly, Category = "Weapon Rack", meta = (ClampMin = "1"))
	int32 GridColumns = 6;

private:
	void BuildFallbackLayout();
	void RebuildGrid();

	UPROPERTY(Transient)
	TObjectPtr<AIBWeaponRack> Rack;

	bool bStockBound = false;
};
