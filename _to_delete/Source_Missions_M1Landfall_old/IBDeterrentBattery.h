#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Combat/IBInteractableInterface.h"
#include "IBDeterrentBattery.generated.h"

class AIBPalawanActor;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDeterrentFiredSignature, int32, ChargesRemaining);

/**
 * The sea-wall Bellringer battery, M1 LANDFALL's one invented mechanic (Docs/
 * M1_LANDFALL_Mission_Design.md §5, needs Connor/Shane sign-off per doc §13
 * question 1 -- build it either way, the fallback if cut is just not placing
 * this actor and letting the siege-gun-fires-uselessly beat carry the lesson
 * alone). Grammar, LOCKED: "redirect, never damage." There is deliberately no
 * damage parameter anywhere in this class -- FireCharge only ever calls
 * ReactToFlinch on its target.
 *
 * Scope note: this does NOT implement turret possession (camera swap, locked
 * player control while manned). Interact() fires one charge directly, which is
 * enough to prototype the beat's feel and pacing; a full "man the turret" state
 * is a separate, larger feature to layer on if the deterrent beat survives sign-off.
 */
UCLASS()
class IRONBREACH_API AIBDeterrentBattery : public AActor, public IIBInteractable
{
	GENERATED_BODY()

public:
	AIBDeterrentBattery();

	virtual void Tick(float DeltaSeconds) override;

	// IIBInteractable -- each Interact() is one charge, cooldown-gated.
	virtual void Interact_Implementation(AActor* Interactor) override;
	virtual FText GetInteractPrompt_Implementation() const override;

	/** Fires one sonic charge at Target (redirect only -- calls Target->ReactToFlinch,
	 *  never anything damage-shaped). No-op while on cooldown or out of charges. */
	UFUNCTION(BlueprintCallable, Category = "Landfall|Deterrent")
	void FireCharge();

	UPROPERTY(BlueprintAssignable, Category = "Landfall|Deterrent|Events")
	FOnDeterrentFiredSignature OnDeterrentFired;

	/** What this battery rings. Placed reference -- one PALAWAN, one battery, no
	 *  targeting logic needed for a single scripted convoy chokepoint. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Landfall|Deterrent")
	TObjectPtr<AIBPalawanActor> Target;

	/** Socket name reported to Target::ReactToFlinch/OnFlinch, for whichever limb
	 *  this battery is authored to be ringing. Cosmetic label only. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Landfall|Deterrent")
	FName TargetSocket = TEXT("LeadLimb");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Landfall|Deterrent", meta = (ClampMin = "0.1"))
	float FireCooldown = 2.0f;

	/** -1 = unlimited. "The gun line" is one scripted sequence at a chokepoint,
	 *  not a reusable weapon -- cap it if you want the player to feel the limit. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Landfall|Deterrent")
	int32 MaxCharges = -1;

	UFUNCTION(BlueprintPure, Category = "Landfall|Deterrent")
	bool IsOnCooldown() const { return CooldownRemaining > 0.0f; }

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<class UStaticMeshComponent> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Landfall|Deterrent")
	FText InteractPrompt;

private:
	float CooldownRemaining = 0.0f;
	int32 ChargesFired = 0;
};
