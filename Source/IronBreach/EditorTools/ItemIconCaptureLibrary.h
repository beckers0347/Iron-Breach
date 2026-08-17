// ItemIconCaptureLibrary.h
//
// Editor-only content tool: renders an item's linked weapon mesh in an isolated
// lightbox (spawned far above any real level geometry, and further isolated via
// PrimitiveRenderMode::PRM_UseShowOnlyList so nothing from whatever level
// happens to be open in the editor bleeds into frame) and bakes the capture into
// a saved Texture2D icon, assigned to UIBItemDefinition::Icon.
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ItemIconCaptureLibrary.generated.h"

class UIBItemDefinition;
class UTexture2D;

UCLASS()
class IRONBREACH_API UItemIconCaptureLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Captures Definition->WeaponData->ViewmodelMesh into a new Texture2D icon
	 *  saved under /Game/Items/Icons/Generated/T_Icon_<ItemName>, assigns it to
	 *  Definition->Icon, and saves Definition. Returns nullptr (with a toast
	 *  explaining why) outside the editor, if Definition has no WeaponData, or if
	 *  that WeaponData has no ViewmodelMesh assigned yet.
	 *
	 *  LightIntensity / ExposureBias are starting points, not guaranteed-correct
	 *  numbers -- there's no way to preview the render ahead of time, so treat the
	 *  first capture on a new mesh as a test: if it comes back too dark or blown
	 *  out, nudge these and run it again (it's instant and deterministic).
	 *
	 *  MeshRotationOverride corrects individual weapons whose mesh isn't authored
	 *  facing the default capture angle -- meshes here aren't guaranteed a
	 *  consistent forward axis (see WeaponRigComponent's WeaponMountRotation, the
	 *  same problem solved for viewmodel posing). */
	UFUNCTION(BlueprintCallable, Category = "Weapon System|Editor Tools", meta = (DevelopmentOnly))
	static UTexture2D* CaptureItemIcon(UIBItemDefinition* Definition, int32 Resolution = 256,
		float LightIntensity = 15000.0f, float ExposureBias = 2.0f, FRotator MeshRotationOverride = FRotator::ZeroRotator);
};
