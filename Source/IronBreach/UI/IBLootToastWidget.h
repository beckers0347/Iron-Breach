#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Items/IBItemTypes.h"
#include "IBLootToastWidget.generated.h"

class UTextBlock;
class UVerticalBox;

/**
 * Loot pickup feedback: "+ Kaiju Chitin x3" lines, bottom-right, rarity-tinted,
 * fading out after a few seconds. Listens to the LOCAL player state inventory's
 * OnItemGranted — the collection moment the loot doc promised a hook for.
 * Fully self-building; reskin later with a WBP child if wanted.
 */
UCLASS()
class IRONBREACH_API UIBLootToastWidget : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UFUNCTION()
	void HandleItemGranted(const FIBItemInstance& Item);

private:
	void TryBindInventory();

	UPROPERTY(Transient)
	TObjectPtr<UVerticalBox> ToastBox;

	struct FToastLine { TWeakObjectPtr<UTextBlock> Text; float Age = 0.f; };
	TArray<FToastLine> Lines;

	TWeakObjectPtr<class UIBInventoryComponent> BoundInventory;
	FTimerHandle FindInventoryTimer;

	static constexpr float ToastLifetime = 3.0f;
	static constexpr float ToastFadeTime = 0.75f;
};
