// M2SearchDirector.h
//
// Drives M2 "Dead Reckoning" Beat 1: "The Search." Nine days after Landfall, the squad
// hikes into the mountains the M1 evac helicopter overflew, looking for the garrison's
// lost mech. Quiet, green, unpopulated -- a deliberate tonal reset after M1's urban
// collapse. No combat, no kaiju content anywhere in this mission.
//
// Same Director pattern as M1's Acts (see Act1BarracksDirector for the fullest comments
// on the pattern itself): a pure dialogue/event timeline, played back on a timer,
// chainable off a previous beat, implementing IActBeatProviderInterface so the existing
// MissionSubtitleHUD picks it up automatically. Reuses M1's shared dialogue types
// (IBLandfallDialogueTypes.h / ActBeatProviderInterface.h) since they're already
// mission-agnostic despite the folder name.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "../M1Landfall/IBLandfallDialogueTypes.h"
#include "../M1Landfall/ActBeatProviderInterface.h"
#include "M2SearchDirector.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnM2SearchComplete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnM2SearchScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AM2SearchDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AM2SearchDirector();

protected:
	virtual void BeginPlay() override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Search|Dialogue")
	TArray<FDialogueLine> Beats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Search|Timing")
	float InitialDelay = 1.0f;

	// M2 opens the mission -- nothing to chain off within this mission's own level, so
	// this always runs on its own timer. Left as a bool (rather than removed) purely for
	// consistency with the other Directors' Details panel layout.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Search|Timing")
	bool bAutoStart = true;

	UPROPERTY(BlueprintAssignable, Category = "M2 Search|Events")
	FOnM2SearchComplete OnM2SearchComplete;

	UPROPERTY(BlueprintAssignable, Category = "M2 Search|Events")
	FOnM2SearchScriptedEvent OnScriptedEvent;

	UFUNCTION(BlueprintCallable, Category = "M2 Search")
	void StartSearch();

	// Skips straight to "trail worsens" and fires completion -- for testing the Debris
	// Field beat without replaying the hike-in every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "M2 Search|Debug")
	void SkipToTrailFound();

	UFUNCTION(BlueprintPure, Category = "M2 Search")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishSearch();

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
