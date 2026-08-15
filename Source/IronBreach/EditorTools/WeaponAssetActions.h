// WeaponAssetActions.h
//
// Adds a "Generate Weapon Variant" entry to the right-click menu for
// UWeaponDataAsset assets in the Content Browser. To activate: create an
// Editor Utility Blueprint (Content Browser -> Add -> Editor Utilities ->
// Editor Utility Blueprint) that subclasses UWeaponAssetActions, THEN open its
// Class Defaults and add UWeaponDataAsset to the "Supported Classes" array.
//
// UAssetActionUtility::GetSupportedClass() -- the C++-overridable filter hook
// from older engine versions -- is deprecated as of UE5.8: it's now a
// BlueprintImplementableEvent, not a virtual, so it can't be overridden here
// at all. Epic replaced it with the designer-facing SupportedClasses array
// (visible in Class Defaults), which is why that step above is required.
#pragma once

#include "CoreMinimal.h"

// AssetActionUtility (Blutility) is editor-only and only linked when
// Target.Type == TargetType.Editor (see IronBreach.Build.cs) -- this module
// also builds as a plain Game target, so the whole class must be compiled out there.
#if WITH_EDITOR

#include "AssetActionUtility.h"
#include "WeaponAssetActions.generated.h"

class UWeaponDataAsset;

UCLASS()
class IRONBREACH_API UWeaponAssetActions : public UAssetActionUtility
{
	GENERATED_BODY()

public:
	// Duplicates the clicked weapon into a new "<Name>_Variant" asset alongside it,
	// carrying over its current stats as the starting point.
	UFUNCTION(CallInEditor, Category = "Weapon System")
	void GenerateWeaponVariant(UWeaponDataAsset* SourceWeapon);
};

#endif // WITH_EDITOR
