#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "IBSensorDoor.generated.h"

class USceneComponent;
class USkeletalMeshComponent;
class UBoxComponent;
class USkeletalMesh;
class UAnimSequence;
class APawn;
class UPrimitiveComponent;
class AIBSensorDoor;

UENUM(BlueprintType)
enum class EIBDoorState : uint8
{
	Closed,
	Opening,
	Open,
	Closing
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FIBDoorStateChanged, AIBSensorDoor*, Door, EIBDoorState, NewState);

/**
 * A skeletal-mesh door driven by a proximity sensor.
 *
 * - SensorBox detects pawns (ECC_Pawn overlap). First qualifying pawn in => door opens.
 *   Last one out => door closes after CloseDelay seconds.
 * - DoorMesh plays a single "Open" UAnimSequence. We never "play" it: we drive its position
 *   from Progress (0 = closed, 1 = fully open), so closing is simply the animation in reverse
 *   and a door can reverse mid-swing.
 * - BlockerBox blocks movement while the door is (mostly) closed and is released once
 *   Progress passes BlockerReleaseProgress, so the doorway is solid when shut.
 *
 * Logic runs locally on each machine (no replication). Qualification is by player-ness
 * (controller or PlayerState), which is valid on clients for all player pawns.
 * Tick is only enabled while the door is moving.
 */
UCLASS()
class IRONBREACH_API AIBSensorDoor : public AActor
{
	GENERATED_BODY()

public:
	AIBSensorDoor();

	// ---- Components -------------------------------------------------------------------
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
	TObjectPtr<USceneComponent> DoorRoot;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
	TObjectPtr<USkeletalMeshComponent> DoorMesh;

	// Overlap-only trigger that detects approaching pawns.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
	TObjectPtr<UBoxComponent> SensorBox;

	// Solid while the door is closed.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Door")
	TObjectPtr<UBoxComponent> BlockerBox;

	// ---- Config -----------------------------------------------------------------------
	// Animation that goes closed -> open. Played via SetPosition, forwards to open, backwards to close.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	TObjectPtr<UAnimSequence> OpenAnimation;

	// Seconds to go fully closed <-> fully open. <= 0 uses the animation's own length.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "0.0"))
	float OpenDurationOverride = 0.f;

	// Seconds after the last pawn leaves the sensor before the door starts closing.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "0.0"))
	float CloseDelay = 2.0f;

	// If true only player pawns open the door; if false any pawn does.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	bool bPlayerPawnsOnly = true;

	// While locked the sensor will not open the door. (Does not close an already open door.)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	bool bLocked = false;

	// BlockerBox collision is released once Progress passes this value while opening,
	// and restored once the door has closed back below it.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float BlockerReleaseProgress = 0.35f;

	// Editor-only: drag to pose the door in the viewport (0 closed .. 1 open).
	UPROPERTY(EditAnywhere, Category = "Door|Editor", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float EditorPreviewProgress = 0.f;

	// ---- Events -----------------------------------------------------------------------
	UPROPERTY(BlueprintAssignable, Category = "Door")
	FIBDoorStateChanged OnDoorStateChanged;

	// ---- API --------------------------------------------------------------------------
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Door")
	void RequestOpen();

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Door")
	void RequestClose();

	UFUNCTION(BlueprintCallable, Category = "Door")
	void SetLocked(bool bNewLocked);

	UFUNCTION(BlueprintPure, Category = "Door")
	EIBDoorState GetDoorState() const { return State; }

	UFUNCTION(BlueprintPure, Category = "Door")
	float GetProgress() const { return Progress; }

	// Used by the editor import script: assigns the mesh and animation.
	UFUNCTION(BlueprintCallable, Category = "Door")
	void ConfigureDoor(USkeletalMesh* InMesh, UAnimSequence* InOpenAnimation);

	// Used by the editor import script: positions the two boxes (actor-local space, cm).
	UFUNCTION(BlueprintCallable, Category = "Door")
	void ConfigureVolumes(FVector SensorCenter, FVector SensorHalfExtent,
		FVector BlockerCenter, FVector BlockerHalfExtent, FRotator BlockerRotation);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void OnConstruction(const FTransform& Transform) override;

	UFUNCTION()
	void HandleSensorBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UFUNCTION()
	void HandleSensorEndOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

private:
	bool DoesPawnQualify(const APawn* Pawn) const;
	void PruneOccupants();
	void BeginOpening();
	void BeginClosing();
	void ScheduleClose();
	void OnCloseTimer();
	void SetState(EIBDoorState NewState);
	void ApplyProgress(float NewProgress);
	float GetOpenDuration() const;

	EIBDoorState State = EIBDoorState::Closed;
	float Progress = 0.f;
	bool bBlockerActive = true;
	FTimerHandle CloseTimer;

	// Qualifying pawns currently inside the sensor.
	TSet<TWeakObjectPtr<APawn>> Occupants;
};
