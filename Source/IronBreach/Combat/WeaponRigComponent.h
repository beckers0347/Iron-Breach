#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Combat/AdsSettings.h"
#include "WeaponRigComponent.generated.h"

class UCameraComponent;
class UMeshComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAimChangedSignature, bool, bIsAiming);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnScopeOverlayChangedSignature, bool, bVisible);

/**
 * First-person weapon rig. Port of the Unity WeaponRig + WeaponViewProfile.
 *
 * Owns viewmodel posing (hip + ADS), ADS zoom, spread blend and the
 * scope-overlay signal. Weapons describe their own geometry via named
 * sockets on the weapon mesh (Grip / Aim / Muzzle) and the rig computes
 * placement — so a weapon that looks held wrong is fixed by moving the
 * socket on the mesh, never by touching rig code:
 *
 *  - Hip pose:  the Grip socket is aligned to the authored HipAnchor offset.
 *  - ADS pose:  TWO MODES, chosen per weapon in FIBAdsSettings:
 *      socket-driven (default) — the Aim socket is pulled onto the camera's
 *        forward axis at Ads.AimPointDistance; exact sights for any weapon
 *        with an authored Aim socket, zero tuning.
 *      authored (Ads.bUseAuthoredAdsTransform) — the mesh is posed at
 *        Ads.ADSTransform VERBATIM (no socket solve, no mount rotation
 *        stacked). WYSIWYG with the F8-eject authoring recipe.
 *
 * ADS is a smoothed 0..1 blend, not a bool — pose, FOV, spread and move speed
 * all read the blend, so partial-raise firing works and nothing snaps.
 *
 * Cosmetic only: this poses the local player's viewmodel. It does not
 * replicate; each machine runs its own rig for its own view. Authoritative
 * fire direction/spread is read from GetCurrentSpreadDegrees() by the server.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class IRONBREACH_API UWeaponRigComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UWeaponRigComponent();

	/** Wire the rig to the owner's first-person camera and the viewmodel mesh it should pose. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Rig")
	void SetReferences(UCameraComponent* InCamera, UMeshComponent* InWeaponMesh);

	/** Feed the current weapon's ADS tuning (call when the loadout changes). */
	UFUNCTION(BlueprintCallable, Category = "Weapon Rig")
	void SetAdsSettings(const FIBAdsSettings& InSettings) { Settings = InSettings; }

	/** Per-weapon fine-alignment nudge, layered on top of WeaponMountRotation
	 *  below (see UWeaponVisualData::ViewmodelLocationOffset/RotationOffset for the
	 *  designer-facing side of this). Call whenever the equipped weapon changes,
	 *  same as SetAdsSettings -- safe to call in any order relative to
	 *  SetReferences, since this re-runs that same socket cache internally so the
	 *  two never end up disagreeing about the current offset. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Rig")
	void SetWeaponAlignmentOffset(FVector LocationOffset, FRotator RotationOffset);

	/** Raise/lower the sights. Blend is smoothed internally. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Rig")
	void SetAiming(bool bNewAiming);

	UFUNCTION(BlueprintPure, Category = "Weapon Rig")
	bool IsAiming() const { return bWantAds; }

	/** Tuck the weapon in against the chest while sprinting (blended, same smoothing
	 *  pattern as SetAiming). Character-side sprint/aim/crouch are already mutually
	 *  exclusive (see AIBCharacter_Infantry::StartSprint), so this only ever needs to
	 *  blend from whatever the hip/ADS pose currently is toward SprintAnchor — it
	 *  doesn't need to know or care which of those it's coming from. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Rig")
	void SetSprinting(bool bNewSprinting);

	UFUNCTION(BlueprintPure, Category = "Weapon Rig")
	bool IsSprinting() const { return bWantSprint; }

	/** Smoothed 0..1 ADS blend. 0 = hip, 1 = fully on sights. */
	UFUNCTION(BlueprintPure, Category = "Weapon Rig")
	float GetAdsBlend() const { return Blend; }

	/** Current spread cone half-angle in degrees, blended hip -> ADS. */
	UFUNCTION(BlueprintPure, Category = "Weapon Rig")
	float GetCurrentSpreadDegrees() const { return FMath::Lerp(Settings.HipSpreadDegrees, Settings.AdsSpreadDegrees, Blend); }

	/** Multiply infantry move speed by this. Blends toward Ads.MoveSpeedMultiplier as the weapon raises. */
	UFUNCTION(BlueprintPure, Category = "Weapon Rig")
	float GetMoveSpeedMultiplier() const { return FMath::Lerp(1.0f, Settings.MoveSpeedMultiplier, Blend); }

	/** Multiply look input by this so zoomed aim isn't twitchy. Tracks the actual FOV ratio. */
	UFUNCTION(BlueprintPure, Category = "Weapon Rig")
	float GetLookSensitivityMultiplier() const;

	UPROPERTY(BlueprintAssignable, Category = "Weapon Rig|Events")
	FOnAimChangedSignature OnAimChanged;

	UPROPERTY(BlueprintAssignable, Category = "Weapon Rig|Events")
	FOnScopeOverlayChangedSignature OnScopeOverlayChanged;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Camera-relative hip pose the Grip socket snaps to. Lower-right of centre so the
	 *  rifle reads as held without blocking the view (X fwd, Y right, Z up). Tune to taste. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Hip")
	FVector HipAnchorLocation = FVector(30.0f, 12.0f, -20.0f);

	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Hip")
	FRotator HipAnchorRotation = FRotator(0.0f, -3.0f, 0.0f);

	/** Camera-relative pose the Grip socket snaps to while sprinting -- pulled in close
	 *  and near-centred (small Y) so the weapon sits against the chest rather than out
	 *  to the side. Same space/solve as HipAnchorLocation; tune to taste per weapon
	 *  silhouette. Defaults assume the same X-forward/Y-right/Z-up convention as hip. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sprint")
	FVector SprintAnchorLocation = FVector(14.0f, 2.0f, -16.0f);

	/** Sprint pose rotation. The previous version leaned mostly on Pitch, which angled
	 *  the muzzle up/down -- reads as the weapon standing on end (vertical). Swapped the
	 *  weight onto Yaw (swings the barrel across the body) and Roll (cants the weapon
	 *  onto its side), which is what actually lays it flat across the chest horizontally. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sprint")
	FRotator SprintAnchorRotation = FRotator(8.0f, -75.0f, 65.0f);

	/** Seconds for the hip<->sprint blend to settle, same SmoothDamp-style approach used
	 *  for ADS (see Settings.AdsTime) rather than a separate literal interp speed. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sprint", meta = (ClampMin = "0.05"))
	float SprintTransitionTime = 0.2f;

	/** How much sprint suppresses look-sway, on top of whatever ADS is already applying.
	 *  A tucked weapon shouldn't track the camera as tightly as a hip/aimed one. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sprint", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float SprintSwayReduction = 0.9f;

	/** Check this to force the sprint pose on regardless of actual input -- lets you
	 *  tune SprintAnchorLocation/Rotation above by eye without holding Shift the whole
	 *  time. Tick it during Play In Editor (select this component under the character
	 *  in the World Outliner/Details panel while PIE is running), nudge the two anchor
	 *  values above, and the viewmodel updates live since UpdateWeaponPose() re-reads
	 *  them every frame -- no need to stop and restart PIE between tweaks. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Weapon Rig|Sprint")
	bool bDebugForceSprintPose = false;

	/** Socket on the weapon mesh where the primary hand grips. Snapped to HipAnchor at hip. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sockets")
	FName GripSocket = TEXT("Grip");

	/** Rear sight / optic centre socket. Pulled onto the camera axis at full ADS. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sockets")
	FName AimSocket = TEXT("Aim");

	/** Corrects the weapon mesh's authored facing so the barrel points forward (+X).
	 *  The template rifle is modelled facing sideways, so we yaw it -90. Adjust here
	 *  (usually a 90 or 180 yaw) if a different weapon points the wrong way.
	 *  NOT applied in authored-ADS mode — that pose is verbatim. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sockets")
	FRotator WeaponMountRotation = FRotator(0.0f, -90.0f, 0.0f);

	// ---- Look sway ----
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sway", meta = (ClampMin = "0.0"))
	float SwayAmount = 0.35f; // cm per unit look delta

	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sway", meta = (ClampMin = "0.0"))
	float SwayMax = 3.0f;

	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sway", meta = (ClampMin = "0.01"))
	float SwayResponse = 12.0f;

	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Sway", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float AdsSwayReduction = 0.85f;

	/** Blend at which the scope overlay engages for bUseScopeOverlay weapons. */
	UPROPERTY(EditAnywhere, Category = "Weapon Rig|Scope", meta = (ClampMin = "0.5", ClampMax = "1.0"))
	float ScopeBlendThreshold = 0.85f;

public:
	/** Feed the frame's look delta (post-sensitivity) so the weapon sways naturally. Optional. */
	UFUNCTION(BlueprintCallable, Category = "Weapon Rig")
	void SetLookDelta(FVector2D Delta) { LookDelta = Delta; }

private:
	void UpdateFov();
	void UpdateWeaponPose();
	void UpdateScope();
	FVector SocketLocalOffset(FName Socket) const;

	UPROPERTY()
	TObjectPtr<UCameraComponent> ViewCamera;

	UPROPERTY()
	TObjectPtr<UMeshComponent> WeaponMesh;

	FIBAdsSettings Settings;

	FVector GripLocal = FVector::ZeroVector; // Grip socket offset in weapon-root space
	FVector AimLocal = FVector::ZeroVector;  // Aim socket offset in weapon-root space

	// Persistent per-weapon alignment (SetWeaponAlignmentOffset), zero by default.
	// SetReferences() folds PerWeaponLocationOffset into GripLocal/AimLocal every
	// time it runs (including from SetWeaponMeshScale's re-cache on scale change),
	// so this stays correct regardless of call order.
	FVector PerWeaponLocationOffset = FVector::ZeroVector;
	FRotator PerWeaponMountOffset = FRotator::ZeroRotator;

	float Blend = 0.0f;
	float SprintBlend = 0.0f;
	float BaseFov = 0.0f;
	bool bWantAds = false;
	bool bWantSprint = false;
	bool bScopeVisible = false;

	FVector Sway = FVector::ZeroVector;
	FVector2D LookDelta = FVector2D::ZeroVector;
};
