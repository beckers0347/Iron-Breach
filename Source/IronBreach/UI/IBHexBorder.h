#pragma once

#include "CoreMinimal.h"
#include "Components/ContentWidget.h"
#include "IBHexBorder.generated.h"

class SIBHexBorder;

/**
 * The banner silhouette: an elongated hexagon (pointed top and bottom, long
 * straight sides) painted with Slate custom verts — the concept sheet's card
 * shape, which rounded-box brushes can't do. Fill + glowing outline, content
 * slotted inside with padding that clears the points.
 *
 * Generic on purpose: the fireteam cards use it today; anything else that
 * wants the angular Iron Breach frame can slot into one.
 */
UCLASS()
class IRONBREACH_API UIBHexBorder : public UContentWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Hex")
	void SetFillColor(FLinearColor InColor);

	UFUNCTION(BlueprintCallable, Category = "Hex")
	void SetOutlineColor(FLinearColor InColor);

	UFUNCTION(BlueprintCallable, Category = "Hex")
	void SetOutlineThickness(float InThickness);

	/** Height of each point as a fraction of total height (0..0.4). */
	UFUNCTION(BlueprintCallable, Category = "Hex")
	void SetPointFraction(float InFraction);

	UFUNCTION(BlueprintCallable, Category = "Hex")
	void SetContentPadding(FMargin InPadding);

	UPROPERTY(EditAnywhere, Category = "Hex")
	FLinearColor FillColor = FLinearColor(0.03f, 0.04f, 0.065f, 1.0f);

	UPROPERTY(EditAnywhere, Category = "Hex")
	FLinearColor OutlineColor = FLinearColor(0.12f, 0.16f, 0.24f, 1.0f);

	UPROPERTY(EditAnywhere, Category = "Hex", meta = (ClampMin = "0.0"))
	float OutlineThickness = 1.5f;

	UPROPERTY(EditAnywhere, Category = "Hex", meta = (ClampMin = "0.0", ClampMax = "0.4"))
	float PointFraction = 0.10f;

	UPROPERTY(EditAnywhere, Category = "Hex")
	FMargin ContentPadding = FMargin(12.f, 40.f, 12.f, 40.f);

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void SynchronizeProperties() override;
	virtual void ReleaseSlateResources(bool bReleaseChildren) override;
	virtual void OnSlotAdded(UPanelSlot* InSlot) override;
	virtual void OnSlotRemoved(UPanelSlot* InSlot) override;

private:
	void PushToSlate();

	TSharedPtr<SIBHexBorder> MyHex;
};
