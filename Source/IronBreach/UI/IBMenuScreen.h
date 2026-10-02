#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "InputCoreTypes.h"
#include "UI/IBUISettings.h"
#include "IBMenuScreen.generated.h"

class UIBMenuSubsystem;
namespace IBMenuLayout { struct FPage; }

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
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	/** Subclass refresh hook — rebuild grids/markers here, not in Construct
	 *  (screens are cached and re-opened, never re-created). */
	virtual void NativeScreenOpened() {}
	virtual void NativeScreenClosed() {}

	UFUNCTION(BlueprintImplementableEvent, Category = "Menu", meta = (DisplayName = "On Screen Opened"))
	void BP_OnScreenOpened();

	UFUNCTION(BlueprintImplementableEvent, Category = "Menu", meta = (DisplayName = "On Screen Closed"))
	void BP_OnScreenClosed();

	// --- Tab banner (which screen am I on) ---
	// Built from the settings registry in cycle order; the active tab renders
	// amber, the rest service-gray. Optional bind: place a HorizontalBox named
	// TabBannerBox in the WBP to control placement; with a bare widget whose
	// root is an Overlay (all the C++ fallback layouts), one is injected
	// top-center automatically.

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Menu")
	TObjectPtr<class UHorizontalBox> TabBannerBox;

	void EnsureTabBanner();
	void RefreshTabBanner();

	/** Keeps the header subscribed to BOTH of the owning player state's change events, so it
	 *  redraws while the page is open instead of only at open time.
	 *
	 *  Both are needed, and neither is redundant. A level-up awards XP first: UIBXPSubsystem
	 *  broadcasts OnXPAwarded before OnXPLevelUp, so the player state's XP mirror updates (and
	 *  this header redraws) while OperativeLevel is still the OLD value; the new level arrives
	 *  afterwards on OnOperativeIdentityChanged. Subscribing to XP alone therefore leaves a
	 *  stale LV on screen until the next award or reopen. On a client the two properties are
	 *  separate RepNotifies whose arrival order is not ours to assume, so the header refreshes
	 *  on whichever lands and reads both values fresh each time.
	 *
	 *  Rebinds when the player state is replaced (travel, reconnect); returns true when the
	 *  binding moved. */
	bool BindOperativeEvents();
	void UnbindOperativeEvents();

	UFUNCTION()
	void HandleOperativeStateChanged();

	/** 1600 x 900 reference sheet, scaled as a unit; the scene fills any aspect ratio. */
	class UVerticalBox* BuildHangarPage(const FText& Hint);
	/** Edge-to-edge Director scene, under compact navigation and footer hints. */
	class UOverlay* BuildDirectorPage(const FText& Hint);
	IBMenuLayout::FPage BuildHangarSection(const FText& Title, const FText& Subtitle, const FText& Hint);
	bool bHangarLayout = false;
	bool bDirectorLayout = false;
	FName HangarDefaultTab;
	UPROPERTY(Transient) TObjectPtr<class UTextBlock> HangarCallsign;
	UPROPERTY(Transient) TObjectPtr<class UTextBlock> HangarRank;
	UPROPERTY(Transient) TObjectPtr<class UTextBlock> HangarClearance;
	/** Platform account name beside the callsign (hidden when it is the same string). */
	UPROPERTY(Transient) TObjectPtr<class UTextBlock> HangarAccount;
	/** Real pilot XP through the current level, from the replicated PlayerState mirror. */
	UPROPERTY(Transient) TObjectPtr<class UProgressBar> HangarXPBar;
	UPROPERTY(Transient) TObjectPtr<class UTextBlock> HangarXPText;
	UPROPERTY(Transient) TObjectPtr<class UWidget> HangarXPRow;

	UPROPERTY(EditDefaultsOnly, Category = "Menu|Keys")
	TArray<FKey> CloseKeys;

	UPROPERTY(EditDefaultsOnly, Category = "Menu|Keys")
	TArray<FKey> NextScreenKeys;

	UPROPERTY(EditDefaultsOnly, Category = "Menu|Keys")
	TArray<FKey> PrevScreenKeys;

private:
	EIBMenuGroup GetPresentationGroup() const;
	class UWidget* BuildMenuHeader(bool bCompact);
	UPROPERTY(Transient) TObjectPtr<class UIBMenuNavButton> GroupLink;
	UPROPERTY(Transient) TObjectPtr<class UTextBlock> GroupLinkLabel;
	/** Active-tab marks (hairline + lit notch); toggled Hidden / HitTestInvisible, never faded. */
	UPROPERTY(Transient) TArray<TObjectPtr<class UIBMenuGlyph>> TabUnderlines;
	EIBMenuGroup BuiltTabGroup = EIBMenuGroup::Utility;
	UPROPERTY()
	TObjectPtr<UIBMenuSubsystem> OwnerSubsystem;

	/** The player state the header is subscribed to right now (both events, always together).
	 *  Weak on purpose: the state can be destroyed or replaced under an open screen, and the
	 *  unbind must target the object that was actually bound, not whichever one is current at
	 *  the time. */
	TWeakObjectPtr<class AIBPlayerState> BoundOperativeState;

	FName ScreenId;

	/** Open transition: a short settle from 12 px below into place (translation only — RoundedBox
	 *  outlines ignore RenderOpacity, so no fade). 1 = at rest. */
	float OpenSettle = 1.f;

	/** Banner labels in registry order, paired with their screen ids. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<class UTextBlock>> TabLabels;

	TArray<FName> TabIds;
};
