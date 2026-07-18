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
	// Add this log
	UE_LOG(LogTemp, Warning, TEXT("Ads Blend: %f | FOV: %f"), Blend, ViewCamera->FieldOfView);

	if (BaseFov <= 0.0f) BaseFov = ViewCamera->FieldOfView;
	const float Zoom = FMath::Max(Settings.ZoomMultiplier, 1.0f);
	ViewCamera->SetFieldOfView(BaseFov / FMath::Lerp(1.0f, Zoom, Blend));
}

void UWeaponRigComponent::UpdateWeaponPose()
{

	// If Settings are default-initialized, this will be at 0,0,0
	FVector AdsLocation = Settings.ADSTransform.GetLocation();

	// Log the calculated position to the Output Log to see if it is 0,0,0
	UE_LOG(LogTemp, Warning, TEXT("Rig Target Location: %s"), *AdsLocation.ToString());
	// Hip pose calculation
	const FQuat HipRot = HipAnchorRotation.Quaternion();
	const FVector HipPos = HipAnchorLocation - HipRot.RotateVector(GripLocal);

	// FIX: ADS pose - use the Transform location as the target position directly 
	// without subtracting AimLocal, as the rig already handles local socket alignment
	const FVector AdsPos = Settings.ADSTransform.GetLocation();

	FVector Pos = FMath::Lerp(HipPos, AdsPos, Blend);
	const FQuat Rot = FQuat::Slerp(HipRot, Settings.ADSTransform.GetRotation(), Blend); // Added Rotation blend

	WeaponMesh->SetRelativeLocation(Pos + Sway);
	WeaponMesh->SetRelativeRotation(Rot * WeaponMountRotation.Quaternion());
}

void UWeaponRigComponent::UpdateScope()
{
	const bool bWantScope = Settings.bUseScopeOverlay && Blend >= ScopeBlendThreshold;

	// Add this to your Output Log to see if the visibility is being toggled off[cite: 2]
	UE_LOG(LogTemp, Warning, TEXT("Is Scope Visible: %s"), bWantScope ? TEXT("True") : TEXT("False"));

	if (bWantScope == bScopeVisible) return;
	// ... rest of function[cite: 2]
}
