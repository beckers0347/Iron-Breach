#include "IBAnimInstance_Infantry.h"
#include "IBCharacter_Infantry.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/StaticMeshComponent.h" // ThirdPersonWeaponMesh->GetSocketLocation/Rotation below

void UIBAnimInstance_Infantry::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();
	OwningCharacter = Cast<AIBCharacter_Infantry>(TryGetPawnOwner());
}

void UIBAnimInstance_Infantry::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);

	// TryGetPawnOwner() can still be null for a frame or two around possession/
	// respawn (BeginPlay hasn't finished wiring the pawn<->controller link yet)
	// -- re-resolve here rather than only once in NativeInitializeAnimation, so
	// a respawned pawn's anim instance doesn't get stuck reading a stale/null
	// character forever.
	if (!OwningCharacter)
	{
		OwningCharacter = Cast<AIBCharacter_Infantry>(TryGetPawnOwner());
		if (!OwningCharacter)
		{
			return;
		}
	}

	const FVector Velocity = OwningCharacter->GetVelocity();
	Speed = Velocity.Size2D();

	// Direction relative to the actor's own facing, -180..180, 0 = forward.
	// Computed by hand (dot products against the actor's forward/right axes)
	// rather than pulling in UKismetAnimationLibrary, which lives in the
	// AnimGraphRuntime module -- not currently a dependency of this one, and
	// not worth adding just for this single call.
	const FVector VelocityDir2D = Velocity.GetSafeNormal2D();
	if (!VelocityDir2D.IsNearlyZero())
	{
		const FRotator ActorRotation = OwningCharacter->GetActorRotation();
		const FRotationMatrix RotationMatrix(ActorRotation);
		const float ForwardDot = FVector::DotProduct(VelocityDir2D, RotationMatrix.GetScaledAxis(EAxis::X));
		const float RightDot = FVector::DotProduct(VelocityDir2D, RotationMatrix.GetScaledAxis(EAxis::Y));
		Direction = FMath::RadiansToDegrees(FMath::Atan2(RightDot, ForwardDot));
	}

	if (const UCharacterMovementComponent* Movement = OwningCharacter->GetCharacterMovement())
	{
		bIsInAir = Movement->IsFalling();
	}

	bIsCrouching = OwningCharacter->bIsCrouched; // inherited public ACharacter property
	bIsSprinting = OwningCharacter->IsSprinting();
	bIsCarrying = OwningCharacter->IsCarrying();
	bIsArmed = OwningCharacter->IsArmed();
	bIsAiming = OwningCharacter->IsAiming();
	ActiveWeaponSlot = OwningCharacter->GetActiveWeaponSlot();
	bIsDead = OwningCharacter->IsDead();

	UpdateWeaponHandIKTargets();
}

void UIBAnimInstance_Infantry::UpdateWeaponHandIKTargets()
{
	// OwningCharacter is guaranteed non-null here -- NativeUpdateAnimation already
	// bailed out above if it couldn't resolve one this frame.
	UStaticMeshComponent* ThirdPersonWeapon = OwningCharacter->GetThirdPersonWeaponMesh();
	if (!ThirdPersonWeapon)
	{
		return;
	}

	// Matches what the AnimGraph's old (thread-unsafe) GetSocketLocation/Rotation
	// calls returned: a missing socket falls back to the component's own world
	// transform rather than asserting, same fallback behavior USceneComponent
	// already guarantees -- nothing new to handle here.
	static const FName GripSocket(TEXT("Grip"));
	static const FName OffHandGripSocket(TEXT("OffHandGrip"));

	RightHandGripLocation = ThirdPersonWeapon->GetSocketLocation(GripSocket);
	RightHandGripRotation = ThirdPersonWeapon->GetSocketRotation(GripSocket);
	LeftHandGripLocation = ThirdPersonWeapon->GetSocketLocation(OffHandGripSocket);
	LeftHandGripRotation = ThirdPersonWeapon->GetSocketRotation(OffHandGripSocket);
}
