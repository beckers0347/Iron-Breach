#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Missions/IBMissionDirector.h" // EIBMissionPhase in a UFUNCTION signature
#include "IBObjectiveWidget.generated.h"

class UTextBlock;

/**
 * The objective banner: one line, top-center, driven by the mission director.
 * Optional bind `Txt_Objective`; with a bare WBP (or no WBP at all — the
 * controller can spawn this C++ class directly) it constructs its own text
 * block. Finds the director lazily because on clients the replicated actor
 * can arrive after widget construction.
 */
UCLASS()
class IRONBREACH_API UIBObjectiveWidget : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional), Category = "Objective")
	TObjectPtr<UTextBlock> Txt_Objective;

	UFUNCTION()
	void HandleMissionPhase(EIBMissionPhase NewPhase);

	/** BP hook for pulses/animations on phase flips. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Objective", meta = (DisplayName = "On Objective Changed"))
	void BP_OnObjectiveChanged(EIBMissionPhase NewPhase);

private:
	void TryBindDirector();
	void RefreshText();

	TWeakObjectPtr<AIBMissionDirector> Director;
	FTimerHandle FindDirectorTimer;
};
