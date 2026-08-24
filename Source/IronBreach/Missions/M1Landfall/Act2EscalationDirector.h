// Act2EscalationDirector.h
//
// Drives M1 "Landfall" Act II: "An Eerie Escalation." The squad moves into the
// civilian evac district. Escalation here is environmental/psychological, not
// combat -- gulls vanish, the K9 balks, glow-veins surface through the asphalt, a
// child reaches for one, the street swells like the earth inhaling, and Rhodes
// confirms the contact is directly beneath them. Ends on that line, handing off
// to Act III (the eruption).
//
// Same design intent as Act I: pure logic/timeline actor, no new level geometry,
// no Blueprint graph work required to compile or run. Existing evac-district
// actors (civilians, buses, the K9 unit) are optional references you can wire
// up later purely to trigger reactions on cue -- the dialogue/subtitle timeline
// runs fine without them.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "DialogueTypes.h"
#include "ActBeatProviderInterface.h"
#include "Act2EscalationDirector.generated.h"

class AAct1BarracksDirector;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAct2Complete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAct2ScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AAct2EscalationDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AAct2EscalationDirector();

protected:
	virtual void BeginPlay() override;

public:
	// -------------------------------------------------------------------------
	// Scripted content -- see BuildDefaultBeats() for the Act II script. Editable
	// per-instance in the Details panel, no code changes needed to tweak timing
	// or wording.
	// -------------------------------------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act II|Dialogue")
	TArray<FDialogueLine> Beats;

	// Seconds after starting before the first line fires (only used when this act
	// starts on its own timer rather than chaining off Act I -- see below).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act II|Timing")
	float InitialDelay = 1.0f;

	// If PreviousActDirector is set, this act auto-starts the moment Act I's
	// OnAct1Complete fires, and bAutoStart/InitialDelay below are ignored.
	// If PreviousActDirector is left null, bAutoStart controls whether this act
	// starts itself on its own BeginPlay timer instead -- handy for testing Act II
	// in isolation without replaying Act I first.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act II|Chaining")
	TSoftObjectPtr<AAct1BarracksDirector> PreviousActDirector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act II|Timing")
	bool bAutoStart = true;

	// Optional existing actors already placed in the evac district you want this
	// beat to be aware of, purely for triggering reactions on scripted-event cues
	// (e.g. the K9 unit balking on "K9Refusal", a bus door closing on "BusesClear").
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act II|Optional Refs")
	TArray<TSoftObjectPtr<AActor>> DistrictNPCs;

	// -------------------------------------------------------------------------
	// Delegates
	// -------------------------------------------------------------------------

	// Fires once, the moment Rhodes' "contact is directly beneath them" line lands --
	// that's the hard cut into Act III's eruption, so bind Act III's setup here.
	UPROPERTY(BlueprintAssignable, Category = "Act II|Events")
	FOnAct2Complete OnAct2Complete;

	UPROPERTY(BlueprintAssignable, Category = "Act II|Events")
	FOnAct2ScriptedEvent OnScriptedEvent;

	// -------------------------------------------------------------------------
	// API
	// -------------------------------------------------------------------------

	UFUNCTION(BlueprintCallable, Category = "Act II")
	void StartAct2();

	// Jumps straight to the final "contact beneath them" beat and fires completion --
	// for testing Act III without replaying the whole escalation every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Act II|Debug")
	void SkipToEruption();

	UFUNCTION(BlueprintPure, Category = "Act II")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishAct2();

	UFUNCTION()
	void OnPreviousActComplete();

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
