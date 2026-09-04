// M2DebrisFieldDirector.h
//
// Drives M2 "Dead Reckoning" Beat 2: "Debris Field." The ballistic trail itself -- torn
// canopy, a scorched skid furrow, scattered armor plating, then personal effects.
// Deliberate mirror of M1 Act II's "the birds are gone" motif: the forest is quiet here
// not because anything kaiju-adjacent is wrong, but because a several-hundred-ton machine
// came down through it nine days ago. No dialogue needed to sell most of this -- see the
// design note on the environment-only stretch in BuildDefaultBeats().

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "../M1Landfall/IBLandfallDialogueTypes.h"
#include "../M1Landfall/ActBeatProviderInterface.h"
#include "M2DebrisFieldDirector.generated.h"

class AM2SearchDirector;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnM2DebrisFieldComplete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnM2DebrisFieldScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AM2DebrisFieldDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AM2DebrisFieldDirector();

protected:
	virtual void BeginPlay() override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Debris Field|Dialogue")
	TArray<FDialogueLine> Beats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Debris Field|Timing")
	float InitialDelay = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Debris Field|Chaining")
	TSoftObjectPtr<AM2SearchDirector> PreviousBeatDirector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Debris Field|Timing")
	bool bAutoStart = true;

	UPROPERTY(BlueprintAssignable, Category = "M2 Debris Field|Events")
	FOnM2DebrisFieldComplete OnM2DebrisFieldComplete;

	UPROPERTY(BlueprintAssignable, Category = "M2 Debris Field|Events")
	FOnM2DebrisFieldScriptedEvent OnScriptedEvent;

	UFUNCTION(BlueprintCallable, Category = "M2 Debris Field")
	void StartDebrisField();

	// Skips straight to the wreck coming into view -- for testing the Contact beat
	// without replaying the trail every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "M2 Debris Field|Debug")
	void SkipToWreckSighted();

	UFUNCTION(BlueprintPure, Category = "M2 Debris Field")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishDebrisField();

	UFUNCTION()
	void OnPreviousBeatComplete();

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
