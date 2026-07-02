#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "HitscanWeaponComponent.generated.h"

class UWeaponDataAsset;

/**
 * Drop-in hitscan gun for any pawn (used to arm the template first-person character
 * without Blueprint graph work). Binds left mouse on possession and fires using the
 * project's damage pipeline: DamageableInterface first, generic engine damage otherwise.
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class IRONBREACH_API UHitscanWeaponComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UHitscanWeaponComponent();

	UFUNCTION(BlueprintCallable, Category = "Weapon")
	void Fire();

protected:
	virtual void BeginPlay() override;

	/** Optional data asset; overrides the loose values below when set. */
	UPROPERTY(EditAnywhere, Category = "Weapon")
	TObjectPtr<UWeaponDataAsset> WeaponData;

	UPROPERTY(EditAnywhere, Category = "Weapon", meta = (ClampMin = "0"))
	float Damage = 25.0f;

	UPROPERTY(EditAnywhere, Category = "Weapon", meta = (ClampMin = "100"))
	float Range = 5000.0f;

	UPROPERTY(EditAnywhere, Category = "Weapon", meta = (ClampMin = "0.05"))
	float FireInterval = 0.2f;

private:
	void TryBindInput();

	float LastFireTime = -1000.0f;
	FTimerHandle BindRetryHandle;
};
