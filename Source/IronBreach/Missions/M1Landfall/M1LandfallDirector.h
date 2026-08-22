#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "M1LandfallDirector.generated.h"

class AIBCharacter_Infantry;
class AIBPalawanActor;

/**
 * The four-beat wave from Docs/M1_LANDFALL_Mission_Design.md §4 (L35). Unlike
 * AIBMissionDirector (the demo's Standby/Patrol/Emergence/Engaged/Secured
 * spine, which watches kill-a-kaiju state automatically), M1's beats are
 * scripted and spatial -- "the road lifts," "last bus clears the chokepoint" --
 * not derivable from any system state. So this director doesn't infer beats,
 * it's TOLD: level-placed trigger volumes and Level Sequencer "Call Function"
 * event tracks call the NotifyX functions below, one per §4's LOCKED exit
 * condition, in order. This keeps beat pacing entirely in the level/sequence
 * author's hands -- no timing logic to fight with here.
 */
UENUM(BlueprintType)
enum class EIBLandfallBeat : uint8
{
	Quiet      UMETA(DisplayName = "4.1 Quiet -- Stand the Watch"),
	Dread      UMETA(DisplayName = "4.2 Dread -- The Birds Are Gone"),
	Burst      UMETA(DisplayName = "4.3 Burst -- Run Toward the Sirens"),
	Aftermath  UMETA(DisplayName = "4.4 Aftermath -- Four Hundred Meters"),
	Complete   UMETA(DisplayName = "Mission Complete")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLandfallBeatChangedSignature, EIBLandfallBeat, NewBeat);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnExtractionCountChangedSignature, int32, NewCount);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnNamingBeatSignature, AIBCharacter_Infantry*, Carrier);

UCLASS()
class IRONBREACH_API AM1LandfallDirector : public AActor
{
	GENERATED_BODY()

public:
	AM1LandfallDirector();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION(BlueprintPure, Category = "Mission|Landfall")
	EIBLandfallBeat GetBeat() const { return CurrentBeat; }

	/** Radio-procedural per §7 ("orders, not quest-speak") -- final copy is
	 *  [PROPOSAL] pending sign-off per doc §13; treat these as placeholder text. */
	UFUNCTION(BlueprintPure, Category = "Mission|Landfall")
	FText GetObjectiveText() const;

	/** The burst's only number (LOCKED §7): counts up, never down, never shown
	 *  alongside a kill count because there isn't one. */
	UFUNCTION(BlueprintPure, Category = "Mission|Landfall")
	int32 GetExtractionCount() const { return ExtractionCount; }

	UPROPERTY(BlueprintAssignable, Category = "Mission|Landfall|Events")
	FOnLandfallBeatChangedSignature OnBeatChanged;

	UPROPERTY(BlueprintAssignable, Category = "Mission|Landfall|Events")
	FOnExtractionCountChangedSignature OnExtractionCountChanged;

	/** Fires once, when the carry ends at the hospital muster -- Bricks' "Ferryman"
	 *  line (LOCKED §4.4) hangs off this. */
	UPROPERTY(BlueprintAssignable, Category = "Mission|Landfall|Events")
	FOnNamingBeatSignature OnNamingBeat;

	// --- Beat-exit notifies -- called by level triggers / Sequencer event tracks ---

	/** §4.1 exit: Rhodes stands the platoon to. Quiet -> Dread. */
	UFUNCTION(BlueprintCallable, Category = "Mission|Landfall")
	void NotifyStandToCalled();

	/** §4.2 exit: the road lifts, "Contact is under us." Dread -> Burst. Also
	 *  starts PALAWAN's locomotion if PalawanActor is assigned. */
	UFUNCTION(BlueprintCallable, Category = "Mission|Landfall")
	void NotifyEruptionTriggered();

	/** §4.3 exit: last bus clears the chokepoint, squad sweeps and finds Ms.
	 *  Idris. Burst -> Aftermath (the carry beat). */
	UFUNCTION(BlueprintCallable, Category = "Mission|Landfall")
	void NotifyLastBusCleared();

	/** PALAWAN calcifies, uncommented, per §4.4's "first quiet wrongness." Stays
	 *  within Aftermath -- doesn't advance the beat. Prefer routing this through
	 *  PalawanActor->BeginCalcify() (which this also calls) rather than calling
	 *  BeginCalcify directly, so the director's BP hook (for Rhodes' "contact is
	 *  static, say again, static" line) fires alongside it. */
	UFUNCTION(BlueprintCallable, Category = "Mission|Landfall")
	void NotifyPalawanCalcify();

	/** Sea-wall glimpse held, title card shown. Aftermath -> Complete. */
	UFUNCTION(BlueprintCallable, Category = "Mission|Landfall")
	void NotifyMissionComplete();

	/** Optional: wire PALAWAN once it's placed, so NotifyEruptionTriggered/
	 *  NotifyPalawanCalcify can drive it without a second call from the level. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Mission|Landfall")
	TObjectPtr<AIBPalawanActor> PalawanActor;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(ReplicatedUsing = OnRep_CurrentBeat, VisibleAnywhere, BlueprintReadOnly, Category = "Mission|Landfall")
	EIBLandfallBeat CurrentBeat = EIBLandfallBeat::Quiet;

	UPROPERTY(ReplicatedUsing = OnRep_ExtractionCount, VisibleAnywhere, BlueprintReadOnly, Category = "Mission|Landfall")
	int32 ExtractionCount = 0;

	UFUNCTION()
	void OnRep_CurrentBeat();

	UFUNCTION()
	void OnRep_ExtractionCount();

	/** BP hook for stings/banners, mirrors AIBMissionDirector's pattern -- fires
	 *  on every machine alongside the delegate. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Mission|Landfall", meta = (DisplayName = "On Beat Changed"))
	void BP_OnBeatChanged(EIBLandfallBeat NewBeat);

	UFUNCTION(BlueprintImplementableEvent, Category = "Mission|Landfall", meta = (DisplayName = "On Naming Beat"))
	void BP_OnNamingBeat(AIBCharacter_Infantry* Carrier);

	UFUNCTION()
	void HandleCivilianMustered(AActor* Civilian);

	UFUNCTION()
	void HandleCarryEnded(AActor* CarriedActor, AIBCharacter_Infantry* Carrier);

private:
	void SetBeat(EIBLandfallBeat NewBeat); // server only
};
