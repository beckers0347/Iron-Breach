#include "Combat/WeaponRigComponent.h"
#include "IronBreach.h"
#include "Camera/CameraComponent.h"
#include "Components/MeshComponent.h"

UWeaponRigComponent::UWeaponRigComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// Pose after the camera/control rotation has updated this frame.
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
	SetIsReplicatedByDefault(false); // Local viewmodel only.
}

void UWeaponRigComponent::BeginPlay()
{
	Super::BeginPlay();
	if (ViewCamera)
	{
		BaseFov = ViewCamera->FieldOfView;
	}
}

void UWeaponRigComponent::SetReferences(UCameraComponent* InCamera, UMeshComponent* InWeaponMesh)
{
	ViewCamera = InCamera;
	WeaponMesh = InWeaponMesh;

	if (ViewCamera)
	{
		BaseFov = ViewCamera->FieldOfView;
	}

	// Cache socket offsets in weapon-root space, folding in whatever per-weapon
	// alignment offset is currently set (zero by default -- see
	// SetWeaponAlignmentOffset, which re-runs this same cache so the two never
	// disagree regardless of call order). If the mesh lacks the sockets we fall
	// back to zero (weapon root aligns to the anchor) and warn once.
	//
	// PerWeaponLocationOffset (UWeaponVisualData::ViewmodelLocationOffset) is a
	// fixed, absolute-space nudge in CM -- deliberately NOT scaled by the mesh's
	// current ViewmodelScale, unlike SocketLocalOffset()'s result. It's authored
	// as "shift the socket this many cm," and that has to mean the same physical
	// distance regardless of how small a weapon's ViewmodelScale is, or a designer
	// dialing it in has no idea how big a number to type for a given mesh's scale --
	// worse, on a very small ViewmodelScale (the floor relaxation now allows values
	// far below 1.0) a scaled offset shrinks in lockstep and the nudge stops doing
	// anything visible at all. A previous version of this scaled the offset by
	// MeshScale to fix ADS landing wildly wrong on non-SMG weapons; that turned out
	// to be the AIBCharacter_Infantry::ResolveAdsSettings bug (reading the wrong,
	// deprecated Ads field) rather than this, so it's back to unscaled -- re-tune
	// ViewmodelLocationOffset per weapon if positions drift now that this changed.
	GripLocal = SocketLocalOffset(GripSocket) + PerWeaponLocationOffset;
	AimLocal = SocketLocalOffset(AimSocket) + PerWeaponLocationOffset;

	if (WeaponMesh && (!WeaponMesh->DoesSocketExist(GripSocket) || !WeaponMesh->DoesSocketExist(AimSocket)))
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[WeaponRig] weapon mesh '%s' missing Grip/Aim socket — using root alignment. Add sockets named '%s'/'%s'."),
			*GetNameSafe(WeaponMesh), *GripSocket.ToString(), *AimSocket.ToString());
	}
}

void UWeaponRigComponent::SetWeaponAlignmentOffset(FVector LocationOffset, FRotator RotationOffset)
{
	PerWeaponLocationOffset = LocationOffset;
	PerWeaponMountOffset = RotationOffset;

	// Re-derive the cached socket offsets against the new alignment immediately,
	// rather than waiting for the next SetReferences() call -- SetWeaponMeshScale
	// re-triggers SetReferences on every scale change, which would otherwise
	// silently reset this back to a zero offset if this were the only place
	// folding PerWeaponLocationOffset in.
	SetReferences(ViewCamera, WeaponMesh);
}

FVector UWeaponRigComponent::SocketLocalOffset(FName Socket) const
{
	if (WeaponMesh && Socket != NAME_None && WeaponMesh->DoesSocketExist(Socket))
	{
		// RTS_Component returns the socket's transform as authored on the mesh asset —
		// it does NOT scale with WeaponMesh's current RelativeScale3D. UpdateWeaponPose()
		// rotates this offset and uses it directly as a translation, so it must represent
		// the socket's ACTUAL offset from the mesh origin at the mesh's current size, or a
		// scaled weapon (see UWeaponVisualData::ViewmodelScale) grips/aims off-anchor.
		const FVector RawLocal = WeaponMesh->GetSocketTransform(Socket, RTS_Component).GetLocation();
		return RawLocal * WeaponMesh->GetRelativeScale3D();
	}
	return FVector::ZeroVector;
}

void UWeaponRigComponent::SetAiming(bool bNewAiming)
{
	if (bWantAds == bNewAiming) return;
	bWantAds = bNewAiming;
	OnAimChanged.Broadcast(bNewAiming);
}

void UWeaponRigComponent::SetSprinting(bool bNewSprinting)
{
	bWantSprint = bNewSprinting;
}

float UWeaponRigComponent::GetLookSensitivityMultiplier() const
{
	if (!ViewCamera || BaseFov <= 0.0f) return 1.0f;
	return ViewCamera->FieldOfView / BaseFov;
}

void UWeaponRigComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!ViewCamera) return;

	// Smoothed blend toward hip(0)/ADS(1). Exponential approach tuned so it
	// lands within ~AdsTime seconds — the equivalent of the Unity SmoothDamp.
	const float Target = bWantAds ? 1.0f : 0.0f;
	const float InterpSpeed = 1.0f / FMath::Max(Settings.AdsTime, 0.05f) * 2.5f;
	Blend = FMath::FInterpTo(Blend, Target, DeltaTime, InterpSpeed);

	// Same smoothed approach as the ADS blend above, independent axis -- character-side
	// mutual exclusion (can't sprint while aiming/crouched) means these two blends never
	// need to fight over the same frame, but they're tracked separately regardless so
	// UpdateWeaponPose() can layer sprint on top of whatever hip/ADS pose is current.
	// bDebugForceSprintPose ORs in on top of the real input so the pose can be tuned by
	// eye in the Details panel without needing to hold Shift the whole time.
	const float SprintTarget = (bWantSprint || bDebugForceSprintPose) ? 1.0f : 0.0f;
	const float SprintInterpSpeed = 1.0f / FMath::Max(SprintTransitionTime, 0.05f) * 2.5f;
	SprintBlend = FMath::FInterpTo(SprintBlend, SprintTarget, DeltaTime, SprintInterpSpeed);

	UpdateFov();

	if (WeaponMesh)
	{
		UpdateWeaponPose();
		UpdateScope();
	}

	LookDelta = FVector2D::ZeroVector; // consumed this frame
}

void UWeaponRigComponent::UpdateFov()
{
	if (BaseFov <= 0.0f) BaseFov = ViewCamera->FieldOfView;
	const float Zoom = FMath::Max(Settings.ZoomMultiplier, 1.0f);
	ViewCamera->SetFieldOfView(BaseFov / FMath::Lerp(1.0f, Zoom, Blend));
}

void UWeaponRigComponent::UpdateWeaponPose()
{
	// Per-weapon offset (PerWeaponMountOffset, zero by default) is applied FIRST,
	// in the mesh's own local space, then the rig-wide WeaponMountRotation on top
	// -- a weapon with no offset behaves exactly as before this existed.
	const FQuat MountQuat = WeaponMountRotation.Quaternion() * PerWeaponMountOffset.Quaternion();

	// Hip pose: solve for the mesh origin such that the Grip socket lands on HipAnchor.
	// The mount correction is part of the final rotation, so it must be folded in BEFORE
	// rotating socket offsets — otherwise a weapon with authored sockets gets its grip
	// offset rotated in the wrong frame and the pose drifts sideways.
	const FQuat HipRot = HipAnchorRotation.Quaternion() * MountQuat;
	const FVector HipPos = HipAnchorLocation - HipRot.RotateVector(GripLocal);

	FQuat AdsRot;
	FVector AdsPos;
	if (Settings.bUseAuthoredAdsTransform)
	{
		// Authored mode: VERBATIM. The value copied from the details panel is the value
		// applied — no socket solve, no mount stacking. If it looked right in the
		// viewport, it looks right in game.
		AdsRot = Settings.ADSTransform.GetRotation();
		AdsPos = Settings.ADSTransform.GetLocation();
	}
	else
	{
		// Socket mode (default): solve for the mesh origin such that the Aim socket sits
		// AimPointDistance straight ahead of the camera, sights level. Self-solving for
		// any weapon with an authored Aim socket; a socketless mesh aligns by its root.
		AdsRot = MountQuat;
		AdsPos = FVector(Settings.AimPointDistance, 0.0f, 0.0f) - AdsRot.RotateVector(AimLocal);
	}

	const FVector BasePos = FMath::Lerp(HipPos, AdsPos, Blend);
	const FQuat BaseRot = FQuat::Slerp(HipRot, AdsRot, Blend);

	// Sprint tuck: same solve as hip/ADS (grip socket pinned to an authored anchor),
	// then layered on top of the hip/ADS result via SprintBlend so the weapon eases
	// from whatever pose it was already in into "tucked against the chest".
	const FQuat SprintRot = SprintAnchorRotation.Quaternion() * MountQuat;
	const FVector SprintPos = SprintAnchorLocation - SprintRot.RotateVector(GripLocal);

	const FVector Pos = FMath::Lerp(BasePos, SprintPos, SprintBlend);
	const FQuat Rot = FQuat::Slerp(BaseRot, SprintRot, SprintBlend);

	// Look sway: small positional lag against look input, suppressed on sights and
	// further suppressed while sprinting (a tucked weapon shouldn't track look input
	// as tightly as a hip/aimed one).
	FVector SwayTarget(-LookDelta.Y, -LookDelta.X, 0.0f);
	SwayTarget *= SwayAmount;
	SwayTarget = SwayTarget.GetClampedToMaxSize(SwayMax)
		* (1.0f - Blend * AdsSwayReduction)
		* (1.0f - SprintBlend * SprintSwayReduction);
	Sway = FMath::VInterpTo(Sway, SwayTarget, GetWorld() ? GetWorld()->GetDeltaSeconds() : 0.016f, SwayResponse);

	WeaponMesh->SetRelativeLocation(Pos + Sway);
	WeaponMesh->SetRelativeRotation(Rot);
}

void UWeaponRigComponent::UpdateScope()
{
	const bool bWantScope = Settings.bUseScopeOverlay && Blend >= ScopeBlendThreshold;
	if (bWantScope == bScopeVisible) return;

	bScopeVisible = bWantScope;

	// UI (BP or a scope-overlay widget) binds this to show/hide the full-screen scope texture.
	OnScopeOverlayChanged.Broadcast(bScopeVisible);

	// Snipers typically hide the viewmodel once the scope overlay is up.
	if (Settings.bHideWeaponInScope && WeaponMesh)
	{
		WeaponMesh->SetVisibility(!bScopeVisible, /*bPropagateToChildren=*/true);
	}
}
