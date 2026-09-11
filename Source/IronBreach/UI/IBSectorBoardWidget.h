#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Online/IBWatchTypes.h"
#include "IBSectorBoardWidget.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnIBDestinationPicked, FName, DestinationId);

/**
 * The breach board itself: a painted tactical map of the Carrow sector — land
 * west, sea east, the harbor scar with the sea wall across its mouth, range
 * rings out from CARROW-1 — with every destination as a pin. Pure Slate paint
 * (no textures, no WBP): coastline, grid and pins are lines and discs, so it
 * ships with zero content and re-tints with the house palette.
 *
 * Interaction is hit-tested here (nearest pin within 16 px), so the screen
 * that hosts it only listens to OnDestinationPicked and feeds back the marks:
 *   Selected — what this player is looking at
 *   Proposed — what someone put forward (cyan pulse)
 *   Armed    — what the host confirmed (amber double pulse, deploying)
 *   Current  — the destination this world IS ("YOU ARE HERE")
 */
UCLASS()
class IRONBREACH_API UIBSectorBoardWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Watch")
	FOnIBDestinationPicked OnDestinationPicked;

	void SetMarks(FName InSelected, FName InProposed, FName InArmed, FName InCurrent);

	/** Top-right status: "BREAKWATER NET · LIVE" / "OFF THE NET". */
	void SetNetLine(const FText& Line, const FLinearColor& Color);

	FName GetSelectedId() const { return SelectedId; }

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseLeave(const FPointerEvent& InMouseEvent) override;

private:
	/** Pin under a board-local point, or NAME_None. */
	FName PinAt(const FVector2D& Local, const FVector2D& Size) const;

	FName SelectedId;
	FName ProposedId;
	FName ArmedId;
	FName CurrentId;
	FName HoverId;

	FText NetLine;
	FLinearColor NetColor = FLinearColor::White;

	/** Seconds, for the pulses. */
	float Pulse = 0.f;
};

