#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBPalawanActor.generated.h"

class USplineComponent;
class UStaticMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPalawanFlinchSignature, FName, HitSocket);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnPalawanCalcifyBeginSignature);

/**
 * PALAWAN, M1 LANDFALL's Class C (Docs/M1_LANDFALL_Mission_Design.md §5):
 * "not a boss, not an AI." Deliberately NOT AIBCharacter_Kaiju -- that class
 * carries EKaijuFightPhase/health/targeting for the killable arena-kaiju used
 * elsewhere, and giving PALAWAN any of that would contradict the doc's core
 * mechanical law: "nothing the garrison owns can hurt it, and the game says so
 * with its systems, not a lecture." This class structurally cannot take
 * damage -- it has no health field and doesn't implement IDamageableInterface,
 * so a design/code review can confirm the rule holds by inspection.
 *
 * Locomotion is spline-driven and sequencer-owned (destruction keyed to its
 * timeline as pre-authored Chaos events, per doc §12) -- PlayLocomotion below
 * is a simple constant-speed fallback for blockout/testing; swap SetActorTransform
 * calls here for a Level Sequence driving the same spline if/when the eruption
 * gets its full cinematic treatment.
 */
UCLASS()
class IRONBREACH_API AIBPalawanActor : public AActor
{
	GENERATED_BODY()

public:
	AIBPalawanActor();

	virtual void Tick(float DeltaSeconds) override;

	/** Deterrent-battery hit (AIBDeterrentBattery::FireCharge). Redirect only --
	 *  LOCKED: "the flinch is a redirect, never damage. No health bar exists."
	 *  Broadcasts for the flinch reaction montage/FX; does not alter locomotion
	 *  state beyond whatever BP_OnFlinch chooses to do cosmetically. */
	UFUNCTION(BlueprintCallable, Category = "Landfall|Palawan")
	void ReactToFlinch(FName HitSocket);

	/** Stops locomotion and enters the calcified end state (§4.4: "it just...
	 *  stops. Nobody on comms can explain it and nobody tries"). Called by a
	 *  placed trigger/Sequencer event two blocks short of the hospital, not by
	 *  any combat outcome -- PALAWAN was never fought. */
	UFUNCTION(BlueprintCallable, Category = "Landfall|Palawan")
	void BeginCalcify();

	UFUNCTION(BlueprintPure, Category = "Landfall|Palawan")
	bool IsCalcified() const { return bIsCalcified; }

	UPROPERTY(BlueprintAssignable, Category = "Landfall|Palawan|Events")
	FOnPalawanFlinchSignature OnFlinch;

	UPROPERTY(BlueprintAssignable, Category = "Landfall|Palawan|Events")
	FOnPalawanCalcifyBeginSignature OnCalcifyBegin;

	/** cm/s along LocomotionSpline. Fallback constant-speed mover for blockout --
	 *  see class comment re: Sequencer taking this over later. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Landfall|Palawan", meta = (ClampMin = "0.0"))
	float TraverseSpeed = 300.0f;

	/** Start locomotion along LocomotionSpline. No-op if already moving or calcified. */
	UFUNCTION(BlueprintCallable, Category = "Landfall|Palawan")
	void BeginLocomotion();

protected:
	virtual void BeginPlay() override;

	UFUNCTION(BlueprintImplementableEvent, Category = "Landfall|Palawan", meta = (DisplayName = "On Flinch"))
	void BP_OnFlinch(FName HitSocket);

	UFUNCTION(BlueprintImplementableEvent, Category = "Landfall|Palawan", meta = (DisplayName = "On Calcify Begin"))
	void BP_OnCalcifyBegin();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> BodyMesh; // placeholder collision/visual until the real skeletal asset lands

	/** Authored path through the district. World-space spline placed in the level. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USplineComponent> LocomotionSpline;

private:
	float DistanceAlongSpline = 0.0f;
	bool bIsMoving = false;
	bool bIsCalcified = false;
};
