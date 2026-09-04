// M2FirstSeatDirector.h
//
// Drives M2 "Dead Reckoning" Beat 4: "First Seat." The mech has to walk out under its own
// power, and Achterberg can't fly and run recovery diagnostics alone -- she needs someone
// in the second seat: Vance's old gunnery/systems position. The game does not comment on
// this out loud (same discipline M1 uses for its own quiet wrongness).
//
// Per the mission doc's scope note (see M2_MISSION_DESIGN_v2.md §5), THIS BEAT TEACHES
// MOVEMENT/CAMERA/DIAGNOSTICS ONLY. No weapons, no targeting, no sync/clasp UI -- that
// content is scoped to M6 "Two Hearts" per the existing roadmap, pending Connor/Shane
// sign-off on the split. Nothing in this Director assumes or requires that combat-tutorial
// content to exist.
//
// Same pause/resume pattern as M2ContactDirector and M1's Act5RetreatDirector: plays the
// intro beats (getting in the seat, Achterberg's first instructions) up to a reserved
// "WalkoutBegins" event, then PAUSES for the actual interactive mech walk-out tutorial
// (real player-controlled movement, owned by a separate gameplay system, not a dialogue
// timeline). Call ResumeAfterWalkout() once the mech reaches the extraction clearing.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "../M1Landfall/IBLandfallDialogueTypes.h"
#include "../M1Landfall/ActBeatProviderInterface.h"
#include "M2FirstSeatDirector.generated.h"

class AM2ContactDirector;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnM2Complete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnM2FirstSeatScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AM2FirstSeatDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AM2FirstSeatDirector();

protected:
	virtual void BeginPlay() override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 First Seat|Dialogue")
	TArray<FDialogueLine> Beats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 First Seat|Timing")
	float InitialDelay = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 First Seat|Chaining")
	TSoftObjectPtr<AM2ContactDirector> PreviousBeatDirector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 First Seat|Timing")
	bool bAutoStart = true;

	// This is M2's OWN "OnM2Complete" -- named without a per-beat number since it's the
	// mission's actual finish line, fired once, when the walk-out reaches the clearing.
	UPROPERTY(BlueprintAssignable, Category = "M2 First Seat|Events")
	FOnM2Complete OnM2Complete;

	UPROPERTY(BlueprintAssignable, Category = "M2 First Seat|Events")
	FOnM2FirstSeatScriptedEvent OnScriptedEvent;

	UFUNCTION(BlueprintCallable, Category = "M2 First Seat")
	void StartFirstSeat();

	// Called by whatever owns the interactive walk-out tutorial once the mech reaches the
	// extraction clearing. Resumes the timeline past the "WalkoutBegins" pause into the
	// mission's closing beat. Safe to call only while actually paused there.
	UFUNCTION(BlueprintCallable, Category = "M2 First Seat")
	void ResumeAfterWalkout();

	// Skips straight to the pause point -- for testing the walk-out tutorial hookup
	// directly without replaying the cockpit intro every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "M2 First Seat|Debug")
	void SkipToWalkout();

	// Skips straight to mission end and fires completion.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "M2 First Seat|Debug")
	void SkipToEnding();

	UFUNCTION(BlueprintPure, Category = "M2 First Seat")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishM2();

	UFUNCTION()
	void OnPreviousBeatComplete();

	// Reserved tag: the line carrying this tag pauses the timeline instead of
	// auto-advancing. See class comment.
	static const FName WalkoutBeginsTag;

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	UPROPERTY(Transient)
	bool bWaitingForWalkout = false;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
