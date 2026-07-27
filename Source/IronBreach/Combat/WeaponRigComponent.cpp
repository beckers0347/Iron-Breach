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

	// Cache socket offsets in weapon-root space. If the mesh lacks the sockets
	// we fall back to zero (weapon root aligns to the anchor) and warn once.
	GripLocal = SocketLocalOffset(GripSocket);
	AimLocal = SocketLocalOffset(AimSocket);

	if (WeaponMesh && (!WeaponMesh->DoesSocketExist(GripSocket) || !WeaponMesh->DoesSocketExist(AimSocket)))
	{
		UE_LOG(LogIronBreach, Warning,
			TEXT("[WeaponRig] weapon mesh '%s' missing Grip/Aim socket — using root alignment. Add sockets named '%s'/'%s'."),
			*GetNameSafe(WeaponMesh), *GripSocket.ToString(), *AimSocket.ToString());
	}
}

FVector UWeaponRigComponent::SocketLocalOffset(FName Socket) const
{
	if (WeaponMesh && Socket != NAME_None && WeaponMesh->DoesSocketExist(Socket))
	{
		// Socket transform relative to the mesh component origin == offset in weapon-root space.
		return WeaponMesh->GetSocketTransform(Socket, RTS_Component).GetLocation();
	}
	return FVector::ZeroVector;
}

void UWeaponRigComponent::SetAiming(bool bNewAiming)
{
	if (bWantAds == bNewAiming) return;
	bWantAds = bNewAiming;
	OnAimChanged.Broadcast(bNewAiming);
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
	const FQuat MountQuat = WeaponMountRotation.Quaternion();

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

	const FVector Pos = FMath::Lerp(HipPos, AdsPos, Blend);
	const FQuat Rot = FQuat::Slerp(HipRot, AdsRot, Blend);

	// Look sway: small positional lag against look input, suppressed on sights.
	FVector SwayTarget(-LookDelta.Y, -LookDelta.X, 0.0f);
	SwayTarget *= SwayAmount;
	SwayTarget = SwayTarget.GetClampedToMaxSize(SwayMax) * (1.0f - Blend * AdsSwayReduction);
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
