// WeaponGeneratorLibrary.h
//
// Editor-only content tool: spins up a new weapon by duplicating an existing
// UWeaponCombatData template (power-scaling only: BaseDamage/FireRate/MaxRange)
// and overriding its core combat stats. This tool intentionally never touches
// mesh/FX/ADS presentation at all -- that's UWeaponVisualData's job
// (Combat/WeaponVisualData.h), a separate asset the generator doesn't create or
// modify. Viewmodel meshes live on the character/weapon actor and are posed by
// WeaponRigComponent via named sockets (Grip/Aim), so there's nothing here for
// a generator to wire.
//
// Two modes, both going through the same GenerateWeaponAsset:
//  - Auto-balance (bAutoBalanceFromClassAndTier = true, the default -- what the
//    Weapon Generator panel uses): Damage/FireRate/MaxRange are rolled from
//    WeaponClass + Tier via WeaponBalanceTable.h.
//  - Manual (bAutoBalanceFromClassAndTier = false -- what
//    WeaponAssetActions::GenerateWeaponVariant uses): Damage/FireRate/MaxRange
//    are taken exactly as given, e.g. to clone an existing weapon's stats
//    verbatim under a new name.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "EditorTools/WeaponBalanceTable.h"
#include "WeaponGeneratorLibrary.generated.h"

class UWeaponCombatData;

USTRUCT(BlueprintType)
struct FWeaponGenerationParams
{
	GENERATED_BODY()

	/** Used to derive the new asset's file name (DA_Combat_<Name>[_<Tier>]). WeaponCombatData
	 *  has no name field of its own (that's UWeaponVisualData::WeaponName) -- this string only
	 *  drives the asset's file name. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator")
	FString NewWeaponName = "NewWeapon";

	/** Folder the new DA is created in. In auto-balance mode a Class subfolder is
	 *  appended automatically (e.g. .../Generated/Rifle/). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator")
	FString TargetFolderPath = "/Game/Weapons/Generated";

	/** Existing UWeaponCombatData asset to clone (a DA_Combat_* asset). Only the stat fields
	 *  below are overridden on the copy -- there's nothing else on a combat-data asset to carry
	 *  over, unlike the old combined UWeaponDataAsset this replaced. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator")
	FString SourceTemplatePath = "/Game/Weapons/Rifle/DA_AssultRifle";

	/** True (default): ignore BaseDamage/FireRate/MaxRange below and instead
	 *  auto-roll them from WeaponClass + Tier (WeaponBalanceTable.h) -- this is
	 *  the Weapon Generator panel's mode. False: use BaseDamage/FireRate/MaxRange
	 *  exactly as given -- used to clone an existing weapon's stats verbatim. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator")
	bool bAutoBalanceFromClassAndTier = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator", meta = (EditCondition = "bAutoBalanceFromClassAndTier"))
	EWeaponClass WeaponClass = EWeaponClass::Rifle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator", meta = (EditCondition = "bAutoBalanceFromClassAndTier"))
	EWeaponTier Tier = EWeaponTier::C;

	/** Auto-balance only. 0 = fresh random roll every call (default). Nonzero pins
	 *  the RNG so the same Name+Class+Tier+Seed always reproduces the same numbers. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator", meta = (EditCondition = "bAutoBalanceFromClassAndTier"))
	int32 RandomSeed = 0;

	/** Manual mode only (bAutoBalanceFromClassAndTier = false). Ignored otherwise. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator|Manual Override", meta = (ClampMin = "0", EditCondition = "!bAutoBalanceFromClassAndTier"))
	float BaseDamage = 25.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator|Manual Override", meta = (ClampMin = "0.01", EditCondition = "!bAutoBalanceFromClassAndTier"))
	float FireRate = 0.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Generator|Manual Override", meta = (ClampMin = "0", EditCondition = "!bAutoBalanceFromClassAndTier"))
	float MaxRange = 5000.0f;
};

UCLASS()
class IRONBREACH_API UWeaponGeneratorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Editor-only: duplicates Params.SourceTemplatePath into Params.TargetFolderPath as
	 *  DA_<CleanName>[_<Tier>], resolves stats (auto-balanced or manual, see
	 *  bAutoBalanceFromClassAndTier), overrides BaseDamage/FireRate/MaxRange,
	 *  saves, and returns the new asset. Returns nullptr outside the editor or if the
	 *  template can't be loaded. */
	UFUNCTION(BlueprintCallable, Category = "Weapon System|Editor Tools", meta = (DevelopmentOnly))
	static UWeaponCombatData* GenerateWeaponAsset(const FWeaponGenerationParams& Params);

	/** Shared success/failure toast so the Slate widget and the right-click asset action
	 *  give identical feedback. Editor-only. */
	static void SpawnWeaponGeneratorNotification(const FString& Message, bool bSuccess);
};
