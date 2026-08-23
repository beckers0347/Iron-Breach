#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBPlayerBannerWidget.generated.h"

class APlayerState;
class UTextBlock;
class UBorder;

/**
 * One squad banner — the Apex-style card the lobby strip deals out. Entirely
 * code-drawn: accent bar (amber host / cyan ally / steel empty), monogram
 * portrait block, callsign, clearance, status chip. Shane reskins by
 * childing this in a WBP later; the strip only talks to the two setters.
 */
UCLASS()
class IRONBREACH_API UIBPlayerBannerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Fill the banner from a live player. bIsHost drives the amber treatment. */
	void SetFromPlayerState(const APlayerState* PS, bool bIsHost);

	/** Empty seat: dashed identity, "AWAITING OPERATIVE". */
	void SetEmptySlot(int32 SlotIndex);

protected:
	virtual void NativeOnInitialized() override;

private:
	void BuildLayout();
	void ApplyEmptyVisuals();

	UPROPERTY(Transient) TObjectPtr<UBorder> AccentBar;
	UPROPERTY(Transient) TObjectPtr<UBorder> PortraitBlock;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> MonogramText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ClearanceLabel;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ClearanceValue;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusChip;
};
