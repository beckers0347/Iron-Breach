#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBKitHudWidget.generated.h"

class UIBOperativeKitComponent;
class UTextBlock;
class UProgressBar;
class UBorder;

/**
 * Two chips bottom-right: [Q] KIT ABILITY and [V] MOVEMENT TOOL, each with a
 * cooldown bar in the trade's color. Pure C++ floor (zero content); reskin by
 * parenting a WBP later.
 */
UCLASS()
class IRONBREACH_API UIBKitHudWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void InitFor(UIBOperativeKitComponent* InKit);
	void RefreshLabels();

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	struct FChip
	{
		UTextBlock* Key = nullptr;
		UTextBlock* Name = nullptr;
		UTextBlock* State = nullptr;
		UProgressBar* Bar = nullptr;
		UBorder* Frame = nullptr;
	};

	void BuildLayout();
	FChip BuildChip(class UVerticalBox* Column);
	void UpdateChip(const FChip& Chip, bool bMovementTool);

	TWeakObjectPtr<UIBOperativeKitComponent> Kit;
	FChip KitChip;
	FChip MoveChip;

	UPROPERTY(Transient) TObjectPtr<UVerticalBox> Column;
};
