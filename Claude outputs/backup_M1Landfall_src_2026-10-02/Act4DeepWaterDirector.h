// Act4DeepWaterDirector.h
//
// Drives M1 "Landfall" Act IV: "Deep Water." PALAWAN surfaces -- reclassified Class B per
// KAIJU-CODEX.md (was Class C in the original draft). Infantry crews the sea-wall
// deterrent battery (flinch only, never damage -- unchanged from the original design).
// The garrison's one mech (Vance/Achterberg, introduced in Act III) commits against it
// anyway, because doctrine says it takes multiple mechs and there's exactly one. Gets real
// hits in, doesn't come close to winning. Ends on Rhodes ordering a full garrison
// fall-back -- not a squad retreat, everyone pulls out.
//
// Same pattern as Acts I-III. Optional refs let a level BP hang real combat/VFX logic off
// this Director's scripted events without the Director owning any of it -- see
// Docs/M1_DISTRICT_BP_WIRING.md and the §5 flag in the v2 mission doc about whether
// PALAWAN's side of the mech fight needs even a token IDamageableInterface hookup.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBLandfallDialogueTypes.h"
#include "ActBeatProviderInterface.h"
#include "Act4DeepWaterDirector.generated.h"

class AAct3ContactDirector;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAct4Complete);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAct4ScriptedEvent, FName, EventTag);

UCLASS(Blueprintable, BlueprintType)
class IRONBREACH_API AAct4DeepWaterDirector : public AActor, public IActBeatProviderInterface
{
	GENERATED_BODY()

public:
	AAct4DeepWaterDirector();

protected:
	virtual void BeginPlay() override;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act IV|Dialogue")
	TArray<FDialogueLine> Beats;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act IV|Timing")
	float InitialDelay = 1.0f;

	// If PreviousActDirector is set, this act auto-starts the moment Act III's
	// OnAct3Complete fires. If unset, bAutoStart controls a standalone timer instead --
	// handy for testing Act IV in isolation.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act IV|Chaining")
	TSoftObjectPtr<AAct3ContactDirector> PreviousActDirector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act IV|Timing")
	bool bAutoStart = true;

	// Optional: PALAWAN's level actor (BP_Palawan_Scripted per the wiring doc -- NOT
	// BP_Kaiju_Palawan/AIBCharacter_Kaiju, which is the fightable-boss framework and is
	// wrong for this mission). Left null, this Director still runs its timeline.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act IV|Optional Refs")
	TSoftObjectPtr<AActor> PalawanActor;

	// Optional: the garrison's mech actor, so scripted events (engagement start, mech
	// losing, fall-back) can drive its cosmetic state without this Director owning it.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Act IV|Optional Refs")
	TSoftObjectPtr<AActor> GarrisonMech;

	UPROPERTY(BlueprintAssignable, Category = "Act IV|Events")
	FOnAct4Complete OnAct4Complete;

	UPROPERTY(BlueprintAssignable, Category = "Act IV|Events")
	FOnAct4ScriptedEvent OnScriptedEvent;

	UFUNCTION(BlueprintCallable, Category = "Act IV")
	void StartAct4();

	// Skips straight to the fall-back order and fires completion -- for testing Act V
	// without replaying the whole PALAWAN engagement every PIE run.
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Act IV|Debug")
	void SkipToFallBack();

	UFUNCTION(BlueprintPure, Category = "Act IV")
	virtual bool GetCurrentLine(FDialogueLine& OutLine) const override;

	virtual bool IsActRunning() const override { return CurrentLineIndex >= 0 && !bHasCompleted; }

protected:
	void BuildDefaultBeats();

	void PlayLineAtIndex(int32 Index);
	void AdvanceToNextLine();
	void HandleScriptedEvent(FName EventTag);
	void FinishAct4();

	UFUNCTION()
	void OnPreviousActComplete();

	UPROPERTY(Transient)
	int32 CurrentLineIndex = -1;

	FTimerHandle LineTimerHandle;
	FTimerHandle StartTimerHandle;

	bool bHasCompleted = false;
};
