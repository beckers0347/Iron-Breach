#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Combat/AdsSettings.h"
#include "WeaponVisualData.generated.h"

class UNiagaraSystem;
class USoundBase;
class UStaticMesh;

/**
 * The presentation half of a weapon's data. Combat/WeaponCombatData.h holds
 * the power-scaling half (damage, fire rate, range). Everything about how the
 * weapon looks, sounds, and handles lives here: viewmodel mesh/scale/
 * alignment, fire cosmetics (tracer/sound), and ADS tuning (zoom, spread,
 * handling) -- none of it moves the balance needle, so it iterates freely
 * without touching the Weapon Generator's stat rolls.
 *
 * UIBItemDefinition holds a reference here alongside its UWeaponCombatData
 * sibling. AIBCharacter_Infantry::ApplyWeaponData reads this for the
 * viewmodel swap and feeds Ads/alignment to UWeaponRigComponent.
 */
UCLASS(BlueprintType)
class IRONBREACH_API UWeaponVisualData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	/** Display/identity tag -- logging and the Weapon Generator's naming, not
	 *  a balance concern. Kept here since it travels with "what the weapon
	 *  presents as" rather than "how hard it hits." */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Identity")
	FName WeaponName;

	// TObjectPtr: Epic-standard for UPROPERTY object references (UE5+, required direction for UE6)
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Effects")
	TObjectPtr<UNiagaraSystem> MFXTracer;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Effects")
	TObjectPtr<USoundBase> FireSound;

	/** Aim-down-sights tuning (zoom, sight alignment, spread, handling). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ADS")
	FIBAdsSettings Ads;

	/** Scale applied to the first-person viewmodel mesh when this weapon is equipped.
	 *  The template rifle is authored at full world scale, so most weapons will want
	 *  something in the 0.4-1.0 range to read as "held" rather than filling the screen.
	 *  Applied by AIBCharacter_Infantry::SetWeaponMeshScale() in BeginPlay/ApplyWeaponData —
	 *  tune alongside the rig's Hip Anchor since a smaller weapon sits closer to camera. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel", meta = (ClampMin = "0.01"))
	FVector ViewmodelScale = FVector(1.0f);

	/** Fine-alignment nudge for this weapon's viewmodel, layered on top of the
	 *  rig's shared WeaponMountRotation/Grip-socket solve (WeaponRigComponent::
	 *  SetWeaponAlignmentOffset). Use this to correct one mesh's alignment without
	 *  touching rig-wide settings or re-exporting the mesh with different sockets.
	 *  Rotation is applied in the mesh's own local space BEFORE the rig's
	 *  WeaponMountRotation; Location shifts where the Grip/Aim sockets are treated
	 *  as being, so it stays correct across Hip, ADS, and Sprint poses.
	 *
	 *  Only affects Hip pose, Socket-mode ADS, and Sprint pose — Authored ADS
	 *  transform mode (FIBAdsSettings::bUseAuthoredAdsTransform) is deliberately
	 *  verbatim and ignores this. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Alignment")
	FVector ViewmodelLocationOffset = FVector::ZeroVector;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel|Alignment")
	FRotator ViewmodelRotationOffset = FRotator::ZeroRotator;

	/** The first-person viewmodel mesh swapped in when this weapon becomes the
	 *  active slot (AIBCharacter_Infantry::ApplyWeaponData). Soft reference —
	 *  loaded synchronously only at the moment a weapon is actually equipped, same
	 *  "small, load-on-demand" reasoning as UIBItemDefinition::Icon.
	 *
	 *  Must carry the same named sockets WeaponRigComponent expects (Grip / Aim,
	 *  see WeaponRigComponent.h's class comment) or the viewmodel will pose at the
	 *  mesh origin instead of a held-looking position. Left unset = the character
	 *  keeps whatever mesh it already had rather than going blank, so it's safe to
	 *  generate/stock weapons before art exists — assign this once a mesh is ready. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Viewmodel")
	TSoftObjectPtr<UStaticMesh> ViewmodelMesh;
};
