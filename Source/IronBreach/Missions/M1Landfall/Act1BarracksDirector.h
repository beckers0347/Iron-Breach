// Act1BarracksDirector.h
//
// Drives the M1 "Landfall" Act I beat: the pre-dawn watch room at Carrowgate garrison.
// Static's "Green Tomb hum" theory -> Rhodes enters -> seismic contact -> stand-to order
// -> hand-off to Act II (evacuation).
//
// Design intent: this is a pure logic/timeline actor. It does NOT spawn meshes, does NOT
// require any Blueprint graph work, and does NOT depend on any new level geometry -- drop
// ONE instance of this actor anywhere in the existing CarrowGateGarrison level (or spawn
// it from GameMode::BeginPlay) and it will run the whole beat using only:
//   - on-screen subtitles (native Canvas HUD, see MissionSubtitleHUD)
//   - existing actors you optionally wire up via the exposed UPROPERTY references
//     (SquadNPCs) -- optional/nullable.
//
// Nothing here requires touching the Unreal Editor to compile; wiring the optional actor
// references and dropping the instance in the level is the only editor step, whenever
// you're ready for it.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "DialogueTypes.h"
#include "ActBeatProviderInterface.h"
#include "Act1BarracksDirector.generated.h"

// Broadcast once Act I's stand-to order fires and the beat is considered complete.
// Bind Act II's setup to this from a subclass, a GameMode, or a Blueprint child.
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAct1Complete);

// Broadcast for each scripted, non-dialogue gameplay beat tagged on a line
// (see FDialogueLine::ScriptedEventTag). Lets you hook lighting/audio/animation cues
// to specific moments in the scene without hardcoding them into this class.
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAct1ScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AAct1BarracksDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AAct1BarracksDirector();

protected:
	virtual void BeginPlay() override;

public:
	// -------------------------------------------------------------------------
	// Scripted content. Defaults are populated in the constructor to match the
	// mission doc, but every line is editable per-instance in the Details panel
	// with zero code changes.
	// -------------------------------------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act I|Dialogue")
	TArray<FDialogueLine> Beats;

	// Seconds after BeginPlay before the very first line fires. Lets you delay the
	// scene start (e.g. until a loading fade finishes).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act I|Timing")
	float InitialDelay = 1.0f;

	// If true, the sequence starts automatically on BeginPlay. If false, call
	// StartAct1() manually (e.g. from a trigger volume or cutscene start event).
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act I|Timing")
	bool bAutoStart = true;

	// Optional: existing squad NPC actors already placed in the garrison level that
	// you want this beat to be aware of (e.g. to play idle/alert animations on cue).
	// Left empty by default -- the dialogue timeline runs fine without them.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act I|Optional Refs")
	TArray<TSoftObjectPtr<AActor>> SquadNPCs;

	// -------------------------------------------------------------------------
	// Delegates
	// -------------------------------------------------------------------------

	UPROPERTY(BlueprintAssignable, Category = "Act I|Events")
	FOnAct1Complete OnAct1Complete;

	UPROPERTY(BlueprintAssignable, Category = "Act I|Events")
	FOnAct1ScriptedEvent OnScriptedEvent;

	// -------------------------------------------------------------------------
	// API
	// -------------------------------------------------------------------------

	// Kicks off the Act I beat from the top. Safe to call multiple times (restarts).
	UFUNCTION(BlueprintCallable, Category = "Act I")
	void StartAct1();

	// Skips straight to the stand-to order and fires completion -- useful for testing
	// Act II without sitting through the full barracks scene every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Act I|Debug")
	void SkipToStandTo();

	// Returns the currently displayed line, for the HUD to render.
	// Also serves as the IActBeatProviderInterface override -- the signature matches,
	// so this one function satisfies both the Blueprint-exposed API and the interface.
	UFUNCTION(BlueprintPure, Category = "Act I")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	// -------------------------------------------------------------------------
	// IActBeatProviderInterface
	// -------------------------------------------------------------------------
	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	// Populates Beats with the Act I script. Called from the constructor so the
	// content ships with the class but remains fully editable per-instance.
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishAct1();

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	// True once OnAct1Complete has fired, to guard against double-firing.
	bool bHasCompleted = false;
};
