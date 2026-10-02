#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IBKitHudWidget.generated.h"

class UIBOperativeKitComponent;
class UTextBlock;
class UProgressBar;
class UBorder;

/** Signature, two tacticals and overdrive with live recovery and class-state feedback. */
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
	void UpdateChip(const FChip& Chip, int32 SkillSlot);

	TWeakObjectPtr<UIBOperativeKitComponent> Kit;
	TArray<FChip> Chips;

	UPROPERTY(Transient) TObjectPtr<UVerticalBox> Column;
};
