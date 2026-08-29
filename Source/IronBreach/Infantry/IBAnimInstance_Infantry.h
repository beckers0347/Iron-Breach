#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Items/IBItemTypes.h" // EIBEquipSlot -- ActiveWeaponSlot below
#include "IBAnimInstance_Infantry.generated.h"

class AIBCharacter_Infantry;

/**
 * Native driver for the Infantry AnimGraph.
 *
 * Shane: "can we do the ABP in C++ and I can just add the Animation Sequences
 * after?" -- reparent ABP_InfantryTripo3D (Class Settings -> Parent Class) to
 * this class and every property below shows up as a Get node in the AnimGraph,
 * already fed from the real character state once a tick. No Blueprint Event
 * Graph casting/polling needed to get at Speed, Direction, IsArmed, etc. --
 * this class does that in NativeUpdateAnimation, off AIBCharacter_Infantry's
 * own public accessors (IsArmed/IsSprinting/IsAiming/IsCarrying/IsDead/
 * GetActiveWeaponSlot -- added alongside this class specifically so it has
 * something public to read), so animation-side state can't quietly drift from
 * gameplay-side state the way the old bIsArmed did before SetUnarmed() started
 * syncing it (see that function's comment in IBCharacter_Infantry.cpp -- this
 * class reads the same accessor that fix relies on, not the raw field).
 *
 * WHAT THIS DOESN'T DO: build the actual state machine/blend spaces. Unreal's
 * Python API can't script AnimGraph node creation (checked directly against
 * the 5.x Python API docs -- unreal.AnimBlueprint only exposes target_skeleton/
 * get_animation_graphs/get_nodes_of_class/add_node_asset_override, nothing to
 * add new nodes), and that's equally true from C++: AnimGraph node networks are
 * Blueprint graph data (EdGraph), not something a UAnimInstance subclass's own
 * C++ defines. So once this compiles and the ABP is reparented to it, wiring
 * the State Machine and dragging the InfantryTripo3D AnimSequences into
 * states/blend spaces is still a by-hand step in the ABP editor -- this class
 * just means that step is "wire the graph using these ready-made variables"
 * rather than "also build an Event Graph to go fetch them first."
 *
 * Speed + Direction alone should be enough to drive a standard 2D locomotion
 * Blend Space the same way BS_Armed_Locomotion/BS_Unarmed_Locomotion already
 * work elsewhere in this project -- same convention (cm/s Speed, -180..180
 * Direction), so sample points can be set up the same way.
 */
UCLASS()
class IRONBREACH_API UIBAnimInstance_Infantry : public UAnimInstance
{
	GENERATED_BODY()

public:
	virtual void NativeInitializeAnimation() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

	// --- Locomotion ---

	/** Ground speed, cm/s (Z zeroed -- falling shouldn't read as running). */
	UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
	float Speed = 0.0f;

	/** -180..180: movement direction relative to the actor's own facing.
	 *  0 = forward, +90 = strafing right, -90 = strafing left, +-180 = backward.
	 *  Standard X axis for a 2D locomotion blend space. */
	UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
	float Direction = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
	bool bIsInAir = false;

	UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
	bool bIsCrouching = false;

	UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
	bool bIsSprinting = false;

	UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
	bool bIsCarrying = false;

	// --- Combat ---

	/** Drives the Armed/Unarmed split -- see IBCharacter_Infantry::SetUnarmed(). */
	UPROPERTY(BlueprintReadOnly, Category = "Combat")
	bool bIsArmed = false;

	UPROPERTY(BlueprintReadOnly, Category = "Combat")
	bool bIsAiming = false;

	UPROPERTY(BlueprintReadOnly, Category = "Combat")
	EIBEquipSlot ActiveWeaponSlot = EIBEquipSlot::WeaponPrimary;

	// --- Health ---

	UPROPERTY(BlueprintReadOnly, Category = "Health")
	bool bIsDead = false;

	// --- Weapon hand-IK targets ---
	//
	// WHY THESE EXIST: ABP_InfantryTripo3D's LeftHand/RightHand "Transform (Modify)
	// Bone" nodes used to call ThirdPersonWeaponMesh->GetSocketLocation/Rotation
	// live inside the AnimGraph (a cross-actor "Get ThirdPersonWeaponMesh" property
	// access). The compiler flags exactly that as thread-unsafe -- and it's not a
	// nitpick: with the AnimGraph evaluated on the animation worker thread (this
	// project's default), that impure call silently fails to evaluate instead of
	// erroring, so the Modify Bone nodes were fed a stale/zero target every frame.
	// The hands never actually tracked ThirdPersonWeaponMesh at all; the FPS
	// viewmodel (WeaponMesh) only *looked* held because WeaponRigComponent poses it
	// natively in C++ on the game thread every tick, independent of this bug.
	//
	// FIX: compute the grip targets here, in NativeUpdateAnimation (game thread,
	// same place Speed/Direction/etc. above are computed), then have the ABP's
	// Modify Bone nodes read these BlueprintReadOnly variables directly instead of
	// calling GetSocketLocation/Rotation themselves. A plain variable Get is a pure
	// data read the thread-safe AnimGraph can use without restriction -- same
	// reasoning as every other property on this class.
	//
	// World-space, matching what GetSocketLocation/GetSocketRotation returned
	// before -- set the Modify Bone nodes' Translation/Rotation Space to World
	// Space when rewiring so the values plug in unchanged.

	/** World location of ThirdPersonWeaponMesh's "Grip" socket (primary/trigger hand). */
	UPROPERTY(BlueprintReadOnly, Category = "Weapon|HandIK")
	FVector RightHandGripLocation = FVector::ZeroVector;

	/** World rotation of ThirdPersonWeaponMesh's "Grip" socket (primary/trigger hand). */
	UPROPERTY(BlueprintReadOnly, Category = "Weapon|HandIK")
	FRotator RightHandGripRotation = FRotator::ZeroRotator;

	/** World location of ThirdPersonWeaponMesh's "OffHandGrip" socket (support hand). */
	UPROPERTY(BlueprintReadOnly, Category = "Weapon|HandIK")
	FVector LeftHandGripLocation = FVector::ZeroVector;

	/** World rotation of ThirdPersonWeaponMesh's "OffHandGrip" socket (support hand). */
	UPROPERTY(BlueprintReadOnly, Category = "Weapon|HandIK")
	FRotator LeftHandGripRotation = FRotator::ZeroRotator;

private:
	UPROPERTY(Transient)
	TObjectPtr<AIBCharacter_Infantry> OwningCharacter;

	/** Game-thread-safe helper behind RightHandGripLocation/Rotation and
	 *  LeftHandGripLocation/Rotation above -- see their comments for why this
	 *  can't just happen inline in the AnimGraph. */
	void UpdateWeaponHandIKTargets();
};
