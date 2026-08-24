#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBPlayerBannerWidget.generated.h"

class APlayerState;
class UTextBlock;
class UBorder;
class USizeBox;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnIBBannerInviteClicked, UIBPlayerBannerWidget*, Banner);

/**
 * One fireteam banner — the tall angular card from the concept sheet. Three
 * states:
 *   featured ... the local player, center, larger (the hero card)
 *   filled ..... a squadmate: monogram, callsign, clearance, HOST/LINKED
 *   empty ...... an INVITE PLAYER slot: big cyan +, clickable, fires
 *                OnInviteClicked so the screen can raise the social flyout
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

	UPROPERTY(BlueprintAssignable, Category = "Banner")
	FOnIBBannerInviteClicked OnInviteClicked;

protected:
	virtual void NativeOnInitialized() override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;

private:
	void BuildLayout();
	void ApplySize();

	bool bFeatured = false;
	bool bEmptyInvitable = false;

	UPROPERTY(Transient) TObjectPtr<USizeBox> Frame;
	UPROPERTY(Transient) TObjectPtr<UBorder> Card;
	UPROPERTY(Transient) TObjectPtr<UBorder> AccentBar;
	UPROPERTY(Transient) TObjectPtr<UBorder> PortraitBlock;
	UPROPERTY(Transient) TObjectPtr<UBorder> UnderBar;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> MonogramText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ClearanceValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ClearanceLabel;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusChip;
};
