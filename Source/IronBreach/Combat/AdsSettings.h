#pragma once

#include "CoreMinimal.h"
#include "AdsSettings.generated.h"

/**
 * Per-weapon aim-down-sights tuning. Port of the Unity AdsSettings.
 *
 * Composes into UWeaponVisualData via a single field:
 *     UPROPERTY(EditDefaultsOnly) FIBAdsSettings Ads;
 * Existing weapon visual data assets pick up these defaults automatically.
 *
 * UNITS: Unreal is centimetres (Unity was metres). Distance defaults below
 * are the Unity values * 100. Degrees and multipliers are unchanged.
 *
 * TWO ADS MODES (reconciles the Jul-18 authored-transform redesign with the
 * original socket solve — both survive, per weapon):
 *
 *  1. SOCKET-DRIVEN (default, bUseAuthoredAdsTransform = false)
 *     The rig pulls the weapon's Aim socket onto the camera's forward axis at
 *     AimPointDistance. Sights centre exactly for any weapon with an authored
 *     Aim socket — zero per-weapon tuning. Use this unless you have a reason
 *     not to.
 *
 *  2. AUTHORED (bUseAuthoredAdsTransform = true)
 *     The rig poses the weapon mesh at ADSTransform VERBATIM — no socket
 *     solve, no mount rotation stacked on top. WYSIWYG: pose the WeaponMesh
 *     component in the details panel during PIE (F8 to eject while aiming),
 *     copy the exact Location/Rotation values into the DA. What you copied is
 *     what gets applied.
 */
USTRUCT(BlueprintType)
struct FIBAdsSettings
{
	GENERATED_BODY()

	// ---- Zoom ----
	/** Camera zoom while aiming. 1 = none. Rifles ~1.35, shotguns ~1.15, snipers 4+ (pair with scope overlay). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Zoom", meta = (ClampMin = "1.0", ClampMax = "12.0"))
	float ZoomMultiplier = 1.35f;

	/** Seconds to raise the weapon fully onto the sight line. Doubles as the ease-out time. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Zoom", meta = (ClampMin = "0.05", ClampMax = "0.6"))
	float AdsTime = 0.22f;

	// ---- Sight alignment ----
	/** How far in front of the camera the weapon's Aim socket sits at full ADS, in CM
	 *  (Unity 0.22m -> 22cm). Socket-driven mode only. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Sight",
		meta = (ClampMin = "5.0", ClampMax = "200.0", EditCondition = "!bUseAuthoredAdsTransform"))
	float AimPointDistance = 22.0f;

	/** Opt in to the hand-authored ADS pose below instead of the socket solve. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Sight")
	bool bUseAuthoredAdsTransform = false;

	/** Authored camera-relative pose the weapon MESH snaps to at full ADS, applied verbatim
	 *  (no socket solve, no mount rotation added). Author via the F8-eject recipe in
	 *  Docs/ADS_WEAPON_HANDLING_WIRING.md. Identity means "mesh at the camera origin" — do
	 *  not enable the flag without authoring this. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Sight",
		meta = (EditCondition = "bUseAuthoredAdsTransform"))
	FTransform ADSTransform;

	// ---- Accuracy ----
	/** Spread cone half-angle in degrees when hip firing. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Accuracy", meta = (ClampMin = "0.0", ClampMax = "15.0"))
	float HipSpreadDegrees = 3.5f;

	/** Spread cone half-angle in degrees at full ADS. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Accuracy", meta = (ClampMin = "0.0", ClampMax = "15.0"))
	float AdsSpreadDegrees = 0.35f;

	// ---- Handling ----
	/** Movement speed multiplier at full ADS. Blends in as the weapon raises. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Handling", meta = (ClampMin = "0.2", ClampMax = "1.0"))
	float MoveSpeedMultiplier = 0.7f;

	// ---- Scoped weapons ----
	/** Snipers: swap to a full-screen scope overlay near full ADS instead of zooming the viewmodel. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Scope")
	bool bUseScopeOverlay = false;

	/** Hide the weapon model while the scope overlay is up. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ADS|Scope")
	bool bHideWeaponInScope = true;
};
