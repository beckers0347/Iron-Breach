// Act5RetreatDirector.h
//
// Drives M1 "Landfall" Act V: "Full Retreat." The garrison falls back; PALAWAN throws the
// mech clear of the battlefield into the mountains covering the withdrawal (current
// assumption: this is where Vance is lost -- flagged as an open question in the v2
// mission doc, §13 Q7, confirm before treating it as locked). Then the Idris carry (the
// game's defining early beat) plays out, ending in the naming scene, PALAWAN calcifying
// having WON and stopped anyway, and the sea-wall glimpse. Mission ends on the title card.
//
// UNLIKE Acts I-IV, this act's dialogue timeline does not run start to finish unattended --
// the Idris carry itself (400m walk, her VO as the nav system, no stamina/timer/fail state)
// is real interactive gameplay owned by a separate system (BP_CarryComponent per
// Docs/M1_DISTRICT_BP_WIRING.md §3), not a timed dialogue line. This Director plays its
// PRE-carry beats (the toss, the fall-out, Rhodes' orders to sweep for stragglers) up to a
// reserved "CarryBegins" scripted event, then PAUSES -- it will not auto-advance past that
// line. Whatever finds Ms. Idris and starts the carry (a trigger volume, the carry
// component itself, a level BP) is expected to call ResumeAfterCarry() once she goes quiet
// and the interactive carry is over, which resumes the timeline into the POST-carry beats
// (naming, calcification, the glimpse, mission end).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBLandfallDialogueTypes.h"
#include "ActBeatProviderInterface.h"
#include "Act5RetreatDirector.generated.h"

class AAct4DeepWaterDirector;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAct5Complete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAct5ScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AAct5RetreatDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AAct5RetreatDirector();

protected:
	virtual void BeginPlay() override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act V|Dialogue")
	TArray<FDialogueLine> Beats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act V|Timing")
	float InitialDelay = 1.0f;

	// If PreviousActDirector is set, this act auto-starts the moment Act IV's
	// OnAct4Complete fires. If unset, bAutoStart controls a standalone timer instead --
	// handy for testing Act V in isolation.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act V|Chaining")
	TSoftObjectPtr<AAct4DeepWaterDirector> PreviousActDirector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act V|Timing")
	bool bAutoStart = true;

	// Optional refs, purely so this Director can raise scripted events at the right
	// moments without owning any of the actual mech-toss VFX/camera work or the carry.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act V|Optional Refs")
	TSoftObjectPtr<AActor> PalawanActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act V|Optional Refs")
	TSoftObjectPtr<AActor> GarrisonMech;

	UPROPERTY(BlueprintAssignable, Category = "Act V|Events")
	FOnAct5Complete OnAct5Complete;

	UPROPERTY(BlueprintAssignable, Category = "Act V|Events")
	FOnAct5ScriptedEvent OnScriptedEvent;

	UFUNCTION(BlueprintCallable, Category = "Act V")
	void StartAct5();

	// Called by whatever owns the interactive Idris carry (BP_CarryComponent, a level BP,
	// a trigger volume) once she's gone quiet and the carry is over. Resumes the timeline
	// past the "CarryBegins" pause point into the naming/calcification/glimpse beats.
	// Safe to call only once the timeline is actually paused there; a stray call before
	// that point or after the act has already completed is a no-op.
	UFUNCTION(BlueprintCallable, Category = "Act V")
	void ResumeAfterCarry();

	// Skips straight past the pre-carry beats to the "CarryBegins" pause point, without
	// waiting for Act IV -- for testing the carry hookup without replaying the toss.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Act V|Debug")
	void SkipToCarry();

	// Skips straight to the naming/calcification/glimpse tail and fires completion --
	// for testing the mission's ending without playing the carry every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Act V|Debug")
	void SkipToEnding();

	UFUNCTION(BlueprintPure, Category = "Act V")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishAct5();

	UFUNCTION()
	void OnPreviousActComplete();

	// Reserved tag: the line carrying this tag pauses the timeline instead of
	// auto-advancing. See class comment.
	static const FName CarryBeginsTag;

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	UPROPERTY(Transient)
	bool bWaitingForCarry = false;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
