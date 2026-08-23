#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Combat/AdsSettings.h"
#include "WeaponCombatData.generated.h"

/**
 * The power-scaling half of a weapon's data, PLUS the ADS handling that rides
 * along with "how this weapon fights" (zoom, spread, aim handling). Combat/
 * WeaponVisualData.h holds the other half (mesh, viewmodel scale/offset, fire
 * cosmetics) and, as of this asset's CombatData field, is the ONE thing you
 * attach to an item/rack/loadout -- this asset is reached through that link
 * rather than assigned separately, so a weapon is one reference to wire up,
 * not two. Split out of the old UWeaponDataAsset so balance tuning and
 * presentation tuning can be iterated independently -- the Weapon Generator's
 * auto-balance roll (WeaponGeneratorLibrary.h) only ever needs to touch THIS
 * asset, with no risk of clobbering a hand-authored mesh/FX setup living on a
 * separate visual asset.
 *
 * UHitscanWeaponComponent reads this directly for BaseDamage/MaxRange/FireRate/Ads,
 * resolved via UWeaponVisualData::CombatData rather than held as its own separate
 * reference -- see that class's own header for the mesh/scale/offset half.
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

	/** Aim-down-sights tuning (zoom, sight alignment, spread, handling). Lives here
	 *  (not on the Visual asset) because zoom/spread/handling are combat-feel
	 *  concerns, same bucket as damage/range/fire-rate. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ADS")
	FIBAdsSettings Ads;
};
