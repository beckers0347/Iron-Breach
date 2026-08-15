#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kaiju/IBCharacter_Kaiju.h" // EKaijuFightPhase in a UFUNCTION signature
#include "IBMissionDirector.generated.h"

class AIBCharacter_Kaiju;

/** The demo mission's spine, in order. Server-authoritative, replicated. */
UENUM(BlueprintType)
enum class EIBMissionPhase : uint8
{
	Standby    UMETA(DisplayName = "Standby"),
	Patrol     UMETA(DisplayName = "Patrol (sweep the zone)"),
	Emergence  UMETA(DisplayName = "Kaiju Emergence"),
	Engaged    UMETA(DisplayName = "Engaged (kill it)"),
	Secured    UMETA(DisplayName = "Zone Secured")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMissionPhaseChangedSignature, EIBMissionPhase, NewPhase);

/**
 * Turns the systems into a MISSION: deploy → a kaiju emerges → kill it →
 * ZONE SECURED. One replicated actor, spawned automatically by
 * UIBMissionSubsystem in any world that contains kaiju (or a spawner), or
 * hand-placed for authored levels.
 *
 * Server logic only watches two things: kaiju entering the world (spawner or
 * placed) and kaiju hitting their terminal fight phase. Everything cosmetic —
 * banners, roars, music stings — hangs off OnPhaseChanged / the BP hooks on
 * every machine. The objective TEXT ships in code (GetObjectiveText) so the
 * demo reads as a mission with zero content wiring; restyle freely in the
 * objective widget later.
 */
UCLASS()
class IRONBREACH_API AIBMissionDirector : public AActor
{
	GENERATED_BODY()

public:
	AIBMissionDirector();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	UFUNCTION(BlueprintPure, Category = "Mission")
	EIBMissionPhase GetMissionPhase() const { return MissionPhase; }

	/** The banner line for the current phase. */
	UFUNCTION(BlueprintPure, Category = "Mission")
	FText GetObjectiveText() const;

	UPROPERTY(BlueprintAssignable, Category = "Mission|Events")
	FOnMissionPhaseChangedSignature OnMissionPhaseChanged;

	/** Seconds the EMERGENCE warning holds before the objective flips to kill orders. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Mission", meta = (ClampMin = "0.0"))
	float EmergenceDuration = 4.0f;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UPROPERTY(ReplicatedUsing = OnRep_MissionPhase, VisibleAnywhere, BlueprintReadOnly, Category = "Mission")
	EIBMissionPhase MissionPhase = EIBMissionPhase::Standby;

	UFUNCTION()
	void OnRep_MissionPhase();

	/** BP hook for stings/FX; fires on every machine alongside the delegate. */
	UFUNCTION(BlueprintImplementableEvent, Category = "Mission", meta = (DisplayName = "On Mission Phase Changed"))
	void BP_OnMissionPhaseChanged(EIBMissionPhase NewPhase);

	UFUNCTION()
	void HandleKaijuFightPhase(EKaijuFightPhase NewPhase);

private:
	void SetMissionPhase(EIBMissionPhase NewPhase); // server only
	void TrackKaiju(AIBCharacter_Kaiju* Kaiju);     // server only
	void OnWorldActorSpawned(AActor* Actor);        // server only

	FDelegateHandle ActorSpawnedHandle;
	FTimerHandle EmergenceTimer;

	/** Live tracked kaiju count; Secured when it returns to zero. */
	int32 LiveKaiju = 0;
};
