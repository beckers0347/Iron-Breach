#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TargetingComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnTargetChangedSignature, AActor*, NewTarget, AActor*, OldTarget);

/**
 * Lock-on / target acquisition v1 (board item um-08 — the Targeting_System HUD asset
 * plugs into OnTargetChanged / GetLockedTarget).
 *
 * Local and cosmetic: each machine scans for itself and the lock drives HUD + aim
 * assist only. Authoritative damage still comes from the server's own trace in
 * UHitscanWeaponComponent — a spoofed lock changes nothing that matters.
 *
 * Scans on a timer (not per-tick): damageable pawns inside MaxRange whose angle to the
 * owner's view axis is under ConeHalfAngleDegrees; closest angle wins, distance breaks
 * ties. Works on any pawn — infantry, mech hull, or gunner seat.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UTargetingComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UTargetingComponent();

	UFUNCTION(BlueprintPure, Category = "Targeting")
	AActor* GetLockedTarget() const { return LockedTarget; }

	UFUNCTION(BlueprintCallable, Category = "Targeting")
	void SetTargetingEnabled(bool bEnabled);

	UPROPERTY(BlueprintAssignable, Category = "Targeting|Events")
	FOnTargetChangedSignature OnTargetChanged;

	/** Cone half-angle around the view axis a target must sit inside, in degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Targeting", meta = (ClampMin = "1.0", ClampMax = "60.0"))
	float ConeHalfAngleDegrees = 15.0f;

	/** Acquisition range in cm. Default 150 m — mech engagement distance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Targeting", meta = (ClampMin = "500.0"))
	float MaxRange = 15000.0f;

	/** Seconds between scans. Scanning every frame buys nothing but heat. */
	UPROPERTY(EditAnywhere, Category = "Targeting", meta = (ClampMin = "0.05"))
	float ScanInterval = 0.2f;

	/** Require line of sight (visibility trace) to hold a lock. */
	UPROPERTY(EditAnywhere, Category = "Targeting")
	bool bRequireLineOfSight = true;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void Scan();
	bool GetViewPoint(FVector& OutLocation, FVector& OutDirection) const;
	void SetLockedTarget(AActor* NewTarget);

	UPROPERTY()
	TObjectPtr<AActor> LockedTarget;

	FTimerHandle ScanTimerHandle;
	bool bTargetingEnabled = true;
};
