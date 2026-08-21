// WeaponAssetActions.cpp
#include "EditorTools/WeaponAssetActions.h"

#if WITH_EDITOR

#include "EditorTools/WeaponGeneratorLibrary.h"
#include "EditorTools/ItemIconCaptureLibrary.h"
#include "Combat/WeaponCombatData.h"
#include "Items/IBItemDefinition.h"
#include "Misc/PackageName.h"

void UWeaponAssetActions::GenerateWeaponVariant(UWeaponCombatData* SourceWeapon)
{
	if (!SourceWeapon)
	{
		return;
	}

	const FString SourcePackagePath = SourceWeapon->GetOutermost()->GetName(); // e.g. /Game/Weapons/Rifle/DA_Combat_AssultRifle
	// UWeaponCombatData has no name field of its own (that moved to UWeaponVisualData::WeaponName) --
	// the asset's own name is the only identity available here.
	const FString SourceName = SourceWeapon->GetName();

	FWeaponGenerationParams Params;
	Params.NewWeaponName = SourceName + TEXT("_Variant");
	Params.TargetFolderPath = FPackageName::GetLongPackagePath(SourcePackagePath);
	Params.SourceTemplatePath = SourcePackagePath;
	// This action clones the clicked weapon's exact stats under a new name -- it's
	// not a Class/Tier roll, so opt out of the Weapon Generator panel's auto-balance
	// (which defaults on and would otherwise overwrite these with fresh random stats).
	Params.bAutoBalanceFromClassAndTier = false;
	Params.BaseDamage = SourceWeapon->BaseDamage;
	Params.FireRate = SourceWeapon->FireRate;
	Params.MaxRange = SourceWeapon->MaxRange;

	UWeaponGeneratorLibrary::GenerateWeaponAsset(Params);
}

void UWeaponAssetActions::CaptureIconFromMesh(UIBItemDefinition* Item)
{
	if (!Item)
	{
		return;
	}

	UItemIconCaptureLibrary::CaptureItemIcon(Item);
}

#endif // WITH_EDITOR
