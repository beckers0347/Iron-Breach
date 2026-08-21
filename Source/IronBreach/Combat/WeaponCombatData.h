#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "WeaponCombatData.generated.h"

/**
 * The power-scaling half of a weapon's data. Combat/WeaponVisualData.h holds
 * the other half (mesh, viewmodel scale/offset, fire effects, ADS handling).
 * Split out of the old UWeaponDataAsset so balance tuning and presentation
 * tuning can be iterated independently -- the Weapon Generator's auto-balance
 * roll (WeaponGeneratorLibrary.h) only ever needs to touch THIS asset now,
 * with no risk of clobbering a hand-authored mesh/FX/ADS setup living on a
 * separate visual asset.
 *
 * UHitscanWeaponComponent reads this directly for BaseDamage/MaxRange/FireRate.
 * UIBItemDefinition holds a reference here alongside its UWeaponVisualData
 * sibling (see that class's own header for what moved there).
 */
UCLASS(BlueprintType)
class IRONBREACH_API UWeaponCombatData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Stats")
	float BaseDamage = 25.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Stats")
	float MaxRange = 5000.0f; // 50 meters

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon Stats", meta = (ClampMin = "0.01"))
	float FireRate = 0.15f; // Time between shots
};
