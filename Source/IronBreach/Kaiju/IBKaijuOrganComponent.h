#pragma once

#include "CoreMinimal.h"
#include "Components/SphereComponent.h"
#include "IBKaijuOrganComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnOrganStateChangedSignature, bool, bNowDestroyed);

/**
 * One destructible weak point on a kaiju (raid phase 2, OrganDisable).
 *
 * It IS the collision: a sphere that blocks the same ECC_Pawn channel the
 * hitscan traces use, so aiming at the glowing sac hits THIS component and
 * the kaiju can route damage by HitResult. Add N of these to the kaiju BP,
 * push each one proud of the mesh surface (a fully-buried organ can never
 * be hit — the body capsule eats the trace first).
 *
 * Rules of the phase, enforced by the kaiju not by us:
 *   - while armored, organ hits feed the armor pool like any other hit
 *   - in the organ phase, organ hits burn the organ's own pool
 *   - each destroyed organ chunks the boss's real health (the stagger reward)
 *   - all organs down -> the kaiju goes Exposed (the execute window)
 *
 * Cosmetics (glow, burst FX, gore) are BP-side via OnOrganStateChanged —
 * this class replicates state and owns no visuals, per the FX/gameplay split.
 */
UCLASS(ClassGroup = (IronBreach), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UIBKaijuOrganComponent : public USphereComponent
{
	GENERATED_BODY()

public:
	UIBKaijuOrganComponent();

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

	/** 0 = inherit the species' OrganHealth (the normal case). Set per-organ
	 *  only for asymmetric anatomies (a hard heart behind a soft throat). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Organ", meta = (ClampMin = "0.0"))
	float OrganHealthOverride = 0.0f;

	UPROPERTY(BlueprintAssignable, Category = "Organ|Events")
	FOnOrganStateChangedSignature OnOrganStateChanged;

	UFUNCTION(BlueprintPure, Category = "Organ")
	bool IsOrganDestroyed() const { return bDestroyed; }

	UFUNCTION(BlueprintPure, Category = "Organ")
	float GetOrganHealthPercent() const { return (MaxOrganHealth > 0.0f) ? FMath::Clamp(CurrentOrganHealth / MaxOrganHealth, 0.0f, 1.0f) : 0.0f; }

	/** Server-only, called by the owning kaiju once at phase start. */
	void InitOrgan(float SpeciesOrganHealth);

	/** Server-only. Returns true if THIS call destroyed the organ. */
	bool ApplyOrganDamage(float Amount);

protected:
	UPROPERTY(ReplicatedUsing = OnRep_Destroyed, VisibleAnywhere, BlueprintReadOnly, Category = "Organ")
	bool bDestroyed = false;

	/** Replicated for HUD/damage-number use; gameplay decisions stay server-side. */
	UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category = "Organ")
	float CurrentOrganHealth = 0.0f;

	UPROPERTY(Replicated, VisibleAnywhere, BlueprintReadOnly, Category = "Organ")
	float MaxOrganHealth = 0.0f;

	UFUNCTION()
	void OnRep_Destroyed();
};
