// M2ContactDirector.h
//
// Drives M2 "Dead Reckoning" Beat 3: "Contact" -- the mission's centerpiece, and NOT a
// combat encounter. The squad finds Vance's body (same sensitivity law as Ms. Idris in
// M1: no lingering gore, no slow-motion, no score), then a live, armed, defensive
// Achterberg -- alone at the site for over a week, primed to think the squad might be
// scavengers. The player never fires on her and she never seriously threatens to kill the
// player, but it needs to read as a real possibility for a few tense seconds.
//
// UNLIKE M1/M2's other Directors, this one does not run start to finish unattended. It
// plays its pre-standoff beats (finding Vance, spotting Achterberg) up to a reserved
// "DeescalationBegins" event, then PAUSES -- same pattern as M1's Act5RetreatDirector and
// its carry hand-off. Whatever owns the actual de-escalation gameplay (a prompt asking the
// player to lower their weapon, hold position, let Rhodes talk -- real player input, not a
// cutscene) is expected to call ResumeAfterDeescalation() once Achterberg stands down,
// which resumes the timeline into her agreeing to help.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "../M1Landfall/IBLandfallDialogueTypes.h"
#include "../M1Landfall/ActBeatProviderInterface.h"
#include "M2ContactDirector.generated.h"

class AM2DebrisFieldDirector;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnM2ContactComplete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnM2ContactScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AM2ContactDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AM2ContactDirector();

protected:
	virtual void BeginPlay() override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Contact|Dialogue")
	TArray<FDialogueLine> Beats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Contact|Timing")
	float InitialDelay = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Contact|Chaining")
	TSoftObjectPtr<AM2DebrisFieldDirector> PreviousBeatDirector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "M2 Contact|Timing")
	bool bAutoStart = true;

	UPROPERTY(BlueprintAssignable, Category = "M2 Contact|Events")
	FOnM2ContactComplete OnM2ContactComplete;

	UPROPERTY(BlueprintAssignable, Category = "M2 Contact|Events")
	FOnM2ContactScriptedEvent OnScriptedEvent;

	UFUNCTION(BlueprintCallable, Category = "M2 Contact")
	void StartContact();

	// Called by whatever owns the de-escalation gameplay (a prompt/QTE-style system, a
	// dialogue choice, a "hold to lower weapon" input) once Achterberg has stood down.
	// Resumes the timeline past the "DeescalationBegins" pause. Safe to call only while
	// actually paused there; a stray call otherwise is a no-op.
	UFUNCTION(BlueprintCallable, Category = "M2 Contact")
	void ResumeAfterDeescalation();

	// Skips straight to the pause point without replaying the Vance/Achterberg discovery
	// beats -- for testing the de-escalation hookup directly.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "M2 Contact|Debug")
	void SkipToDeescalation();

	// Skips straight past the pause to Achterberg agreeing to help and fires completion --
	// for testing First Seat without replaying the standoff every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "M2 Contact|Debug")
	void SkipToResolved();

	UFUNCTION(BlueprintPure, Category = "M2 Contact")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishContact();

	UFUNCTION()
	void OnPreviousBeatComplete();

	// Reserved tag: the line carrying this tag pauses the timeline instead of
	// auto-advancing. See class comment.
	static const FName DeescalationBeginsTag;

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	UPROPERTY(Transient)
	bool bWaitingForDeescalation = false;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
