#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBPlayerBannerWidget.generated.h"

class APlayerState;
class UTextBlock;
class UBorder;
class USizeBox;
class UIBHexBorder;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnIBBannerInviteClicked, UIBPlayerBannerWidget*, Banner);

/**
 * One fireteam banner — the tall angular card from the concept sheet. Three
 * states:
 *   featured ... the local player, center, larger (the hero card)
 *   filled ..... a squadmate: monogram, callsign, clearance, HOST/LINKED
 *   empty ...... an INVITE PLAYER slot: big cyan +, clickable, fires
 *                OnInviteClicked so the screen can raise the social flyout
 *
 * On top of those three, three interaction reads that layer over whichever
 * state the seat is in:
 *   hovered .... the card edge lifts toward the menu's interaction white
 *   focused .... corner brackets, the same mark the backpack tiles use
 *   selected ... the lit notch on the top edge, set while a social flyout is
 *                open on this seat
 *
 * Entirely code-drawn: accent edge bars, ink portrait block, tracked-out
 * type. Shane reskins by childing this in a WBP later.
 */
UCLASS()
class IRONBREACH_API UIBPlayerBannerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Featured = the local player's hero card (bigger). Call before Set*. */
	void SetFeatured(bool bInFeatured);

	/** Fill the banner from a live player. bIsHost drives the HOST chip. */
	void SetFromPlayerState(const APlayerState* PS, bool bIsHost);

	/** Empty seat: INVITE PLAYER (clickable when bInvitable). */
	void SetEmptySlot(int32 SlotIndex, bool bInvitable = true);

	/** Marks the seat an open social flyout was raised from. Purely a visual
	 *  origin mark — nothing in the invite path reads it, and invites are not
	 *  targeted at a seat. */
	void SetSeatSelected(bool bInSelected);

	UPROPERTY(BlueprintAssignable, Category = "Banner")
	FOnIBBannerInviteClicked OnInviteClicked;

protected:
	virtual void NativeOnInitialized() override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseEnter(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseLeave(const FPointerEvent& InMouseEvent) override;
	/** Focus-PATH, not focus: the pair fires for this widget or any child of it,
	 *  and both return void, so there is no FReply contract to get wrong on a
	 *  card that is only ever a focus target, never a focus consumer. */
	virtual void NativeOnAddedToFocusPath(const FFocusEvent& InFocusEvent) override;
	virtual void NativeOnRemovedFromFocusPath(const FFocusEvent& InFocusEvent) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Cull,
		FSlateWindowElementList& Out, int32 Layer, const FWidgetStyle& Style, bool bEnabled) const override;

private:
	void BuildLayout();
	void ApplySize();
	/** Re-derives the card edge from the recorded rest paint plus whichever
	 *  interaction states are live. The single place any of them is applied. */
	void ApplyStateVisuals();

	bool bFeatured = false;
	bool bEmptyInvitable = false;
	bool bHovered = false;
	bool bFocused = false;
	bool bSeatSelected = false;

	/** The card's paint with every interaction state off. SetFromPlayerState and
	 *  SetEmptySlot record it here instead of writing the card directly, so a
	 *  hover that ends restores exactly the look the seat's own state asked for
	 *  — including a trade color the interaction states know nothing about. */
	FLinearColor RestOutline = FLinearColor(0.12f, 0.29f, 0.35f, 0.65f);
	FLinearColor RestAccent = FLinearColor(0.12f, 0.29f, 0.35f, 0.65f);
	float RestOutlineThickness = 1.0f;

	UPROPERTY(Transient) TObjectPtr<USizeBox> Frame;
	UPROPERTY(Transient) TObjectPtr<UIBHexBorder> Card;
	UPROPERTY(Transient) TObjectPtr<UBorder> AccentBar;
	UPROPERTY(Transient) TObjectPtr<UBorder> PortraitBlock;
	UPROPERTY(Transient) TObjectPtr<UBorder> UnderBar;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> MonogramText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ClearanceValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ClearanceLabel;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusChip;
};
