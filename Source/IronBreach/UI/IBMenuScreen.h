#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "InputCoreTypes.h"
#include "IBMenuScreen.generated.h"

class UIBMenuSubsystem;

/**
 * Base class for every full-screen menu (WBP_InventoryScreen etc. are BP
 * children of the concrete subclasses). Owns the in-menu key grammar:
 *
 *   Escape / gamepad B ......... close
 *   Q / E, LB / RB ............. cycle screens (settings order)
 *   any screen's hotkey ........ jump there (or close, if it's this screen)
 *
 * Keys route through the widget (not the pawn) because the menu runs in
 * UI-only input mode — see UIBMenuSubsystem::ApplyMenuInputMode.
 *
 * Shane: build layout/animation in the WBP child and hook BP_OnScreenOpened /
 * BP_OnScreenClosed for transitions. Don't rebuild the key handling in BP.
 */
UCLASS(Abstract)
class IRONBREACH_API UIBMenuScreen : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Called by the subsystem. Not for manual use. */
	void NotifyScreenOpened(UIBMenuSubsystem* InOwner, FName InScreenId);
	void NotifyScreenClosed();

	UFUNCTION(BlueprintPure, Category = "Menu")
	FName GetScreenId() const { return ScreenId; }

	UFUNCTION(BlueprintPure, Category = "Menu")
	UIBMenuSubsystem* GetMenuSubsystem() const { return OwnerSubsystem; }

protected:
	virtual void NativeOnInitialized() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	/** Subclass refresh hook — rebuild grids/markers here, not in Construct
	 *  (screens are cached and re-opened, never re-created). */
	virtual void NativeScreenOpened() {}
	virtual void NativeScreenClosed() {}

	UFUNCTION(BlueprintImplementableEvent, Category = "Menu", meta = (DisplayName = "On Screen Opened"))
	void BP_OnScreenOpened();

	UFUNCTION(BlueprintImplementableEvent, Category = "Menu", meta = (DisplayName = "On Screen Closed"))
	void BP_OnScreenClosed();

	UPROPERTY(EditDefaultsOnly, Category = "Menu|Keys")
	TArray<FKey> CloseKeys;

	UPROPERTY(EditDefaultsOnly, Category = "Menu|Keys")
	TArray<FKey> NextScreenKeys;

	UPROPERTY(EditDefaultsOnly, Category = "Menu|Keys")
	TArray<FKey> PrevScreenKeys;

private:
	UPROPERTY()
	TObjectPtr<UIBMenuSubsystem> OwnerSubsystem;

	FName ScreenId;
};
