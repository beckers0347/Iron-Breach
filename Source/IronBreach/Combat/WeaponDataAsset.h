#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Combat/AdsSettings.h"
#include "WeaponDataAsset.generated.h"

class UNiagaraSystem;
class USoundBase;

UCLASS(BlueprintType)
class IRONBREACH_API UWeaponDataAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Stats")
	FName WeaponName;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Stats")
	float BaseDamage = 25.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Stats")
	float MaxRange = 5000.0f; // 50 meters

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Stats", meta = (ClampMin = "0.01"))
	float FireRate = 0.15f; // Time between shots

	// TObjectPtr: Epic-standard for UPROPERTY object references (UE5+, required direction for UE6)
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Effects")
	TObjectPtr<UNiagaraSystem> MFXTracer;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Effects")
	TObjectPtr<USoundBase> FireSound;

	/** Aim-down-sights tuning (zoom, sight alignment, spread, handling). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ADS")
	FIBAdsSettings Ads;
};
