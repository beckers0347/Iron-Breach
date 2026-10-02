// Act3ContactDirector.h
//
// Drives M1 "Landfall" Act III: "Contact." A handful of Class D kaiju surface near the
// garrison perimeter as the district collapse begins. This is the mission's earned win --
// infantry holds the line, the garrison's one mech (Vance/Achterberg) mops up what the
// squad can't, and the fight is basically won by the time it ends. That feeling is the
// setup for Act IV, not padding before it -- PALAWAN erupts right after.
//
// Same pattern as Acts I/II: a pure dialogue/event timeline, chainable off the previous
// act. UNLIKE Acts I/II, this act is not purely cosmetic -- it references an optional
// AIBKaijuSpawner (Class D pool) so the Director can bracket the actual fight with its
// beats without owning the combat logic itself (spawn/kill stays on the spawner, per the
// project's existing signals-only convention). Leave the spawner reference unset and this
// still runs fine as a dialogue-only stand-in for early playtesting.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBLandfallDialogueTypes.h"
#include "ActBeatProviderInterface.h"
#include "Act3ContactDirector.generated.h"

class AAct2EscalationDirector;
class AIBKaijuSpawner;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAct3Complete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAct3ScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AAct3ContactDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AAct3ContactDirector();

protected:
	virtual void BeginPlay() override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act III|Dialogue")
	TArray<FDialogueLine> Beats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act III|Timing")
	float InitialDelay = 1.0f;

	// If PreviousActDirector is set, this act auto-starts the moment Act II's
	// OnAct2Complete fires. If unset, bAutoStart controls a standalone timer instead --
	// handy for testing Act III without replaying Acts I-II every PIE run.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act III|Chaining")
	TSoftObjectPtr<AAct2EscalationDirector> PreviousActDirector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act III|Timing")
	bool bAutoStart = true;

	// Optional: the level's Class D spawner pool for this beat (MinClass = MaxClass =
	// ClassD recommended, 3-4 concurrent). Left null, the Director still plays its
	// dialogue/event timeline -- it just isn't bracketing an actual spawner.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act III|Optional Refs")
	TSoftObjectPtr<AIBKaijuSpawner> ClassDSpawner;

	// Optional: the garrison's mech actor, purely so this Director can raise scripted
	// events at the moment it's meant to enter the fight (e.g. "MechDeploys") without
	// owning any of its logic.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act III|Optional Refs")
	TSoftObjectPtr<AActor> GarrisonMech;

	UPROPERTY(BlueprintAssignable, Category = "Act III|Events")
	FOnAct3Complete OnAct3Complete;

	UPROPERTY(BlueprintAssignable, Category = "Act III|Events")
	FOnAct3ScriptedEvent OnScriptedEvent;

	UFUNCTION(BlueprintCallable, Category = "Act III")
	void StartAct3();

	// Skips straight to the "all clear" beat and fires completion -- for testing Act IV
	// without replaying the Class D fight every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Act III|Debug")
	void SkipToAllClear();

	UFUNCTION(BlueprintPure, Category = "Act III")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishAct3();

	UFUNCTION()
	void OnPreviousActComplete();

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
