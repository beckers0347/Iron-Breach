// WeaponAssetActions.h
//
// Adds right-click Content Browser actions for weapon-related assets:
//  - "Generate Weapon Variant" on UWeaponDataAsset
//  - "Capture Icon From Mesh" on UIBItemDefinition
// To activate: create an Editor Utility Blueprint (Content Browser -> Add ->
// Editor Utilities -> Editor Utility Blueprint) that subclasses
// UWeaponAssetActions, THEN open its Class Defaults and add BOTH
// UWeaponDataAsset and UIBItemDefinition to the "Supported Classes" array.
// Multi-select works natively -- select several DA_Item_* assets at once and
// "Capture Icon From Mesh" runs once per selected asset.
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
class UIBItemDefinition;

UCLASS()
class IRONBREACH_API UWeaponAssetActions : public UAssetActionUtility
{
	GENERATED_BODY()

public:
	// Duplicates the clicked weapon into a new "<Name>_Variant" asset alongside it,
	// carrying over its current stats as the starting point.
	UFUNCTION(CallInEditor, Category = "Weapon System")
	void GenerateWeaponVariant(UWeaponDataAsset* SourceWeapon);

	// Renders the item's linked weapon mesh in an isolated lightbox and assigns
	// the resulting icon to Item->Icon. See ItemIconCaptureLibrary.h for the
	// tunable defaults (lighting, exposure, capture angle) if a result looks off.
	UFUNCTION(CallInEditor, Category = "Weapon System")
	void CaptureIconFromMesh(UIBItemDefinition* Item);
};

#endif // WITH_EDITOR
