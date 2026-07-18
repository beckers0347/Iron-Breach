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
	UE_LOG(LogIronBreach, VeryVerbose, TEXT("[WeaponRig] Blend: %f | FOV: %f"), Blend, ViewCamera->FieldOfView);

	if (BaseFov <= 0.0f) BaseFov = ViewCamera->FieldOfView;
	const float Zoom = FMath::Max(Settings.ZoomMultiplier, 1.0f);
	ViewCamera->SetFieldOfView(BaseFov / FMath::Lerp(1.0f, Zoom, Blend));
}

void UWeaponRigComponent::UpdateWeaponPose()
{
	// Hip pose: solve for the mesh origin such that the Grip socket lands on HipAnchor.
	const FQuat HipRot = HipAnchorRotation.Quaternion();
	const FVector HipPos = HipAnchorLocation - HipRot.RotateVector(GripLocal);

	// ADS pose: same pattern, but solve for the mesh origin such that the Aim socket
	// lands on the authored ADS target. This is what actually makes sights line up —
	// without subtracting AimLocal here, the mesh ROOT (not the sight) sits at the
	// target, so the Aim socket is off by however far it sits from the mesh origin.
	const FQuat AdsRot = Settings.ADSTransform.GetRotation();
	const FVector AdsPos = Settings.ADSTransform.GetLocation() - AdsRot.RotateVector(AimLocal);

	const FVector Pos = FMath::Lerp(HipPos, AdsPos, Blend);
	const FQuat Rot = FQuat::Slerp(HipRot, AdsRot, Blend);

	WeaponMesh->SetRelativeLocation(Pos + Sway);
	WeaponMesh->SetRelativeRotation(Rot * WeaponMountRotation.Quaternion());
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

	UE_LOG(LogIronBreach, Verbose, TEXT("[WeaponRig] scope overlay -> %s"), bScopeVisible ? TEXT("visible") : TEXT("hidden"));
}
