#include "World/IBSensorDoor.h"

#include "IronBreach.h"
#include "Animation/AnimSequence.h"
#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerState.h"
#include "TimerManager.h"

AIBSensorDoor::AIBSensorDoor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false; // only ticks while moving

	DoorRoot = CreateDefaultSubobject<USceneComponent>(TEXT("DoorRoot"));
	SetRootComponent(DoorRoot);

	DoorMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("DoorMesh"));
	DoorMesh->SetupAttachment(DoorRoot);
	DoorMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision); // BlockerBox does the blocking
	DoorMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	DoorMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;

	SensorBox = CreateDefaultSubobject<UBoxComponent>(TEXT("SensorBox"));
	SensorBox->SetupAttachment(DoorRoot);
	SensorBox->SetBoxExtent(FVector(200.f, 200.f, 150.f));
	SensorBox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	SensorBox->SetCollisionObjectType(ECC_WorldDynamic);
	SensorBox->SetCollisionResponseToAllChannels(ECR_Ignore);
	SensorBox->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	SensorBox->SetGenerateOverlapEvents(true);
	SensorBox->SetCanEverAffectNavigation(false);
	SensorBox->SetHiddenInGame(true);

	BlockerBox = CreateDefaultSubobject<UBoxComponent>(TEXT("BlockerBox"));
	BlockerBox->SetupAttachment(DoorRoot);
	BlockerBox->SetBoxExtent(FVector(10.f, 120.f, 160.f));
	BlockerBox->SetCollisionProfileName(TEXT("BlockAll"));
	BlockerBox->SetCanEverAffectNavigation(false);
	BlockerBox->SetHiddenInGame(true);
}

void AIBSensorDoor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	// Editor preview only; at runtime Progress starts at 0 (closed).
	const UWorld* World = GetWorld();
	if (World && !World->IsGameWorld() && OpenAnimation && DoorMesh)
	{
		ApplyProgress(EditorPreviewProgress);
	}
}

void AIBSensorDoor::BeginPlay()
{
	Super::BeginPlay();

	if (!OpenAnimation)
	{
		UE_LOG(LogIronBreach, Warning, TEXT("SensorDoor %s: no OpenAnimation set - door will not move."), *GetName());
	}
	if (!DoorMesh->GetSkeletalMeshAsset())
	{
		UE_LOG(LogIronBreach, Warning, TEXT("SensorDoor %s: DoorMesh has no skeletal mesh."), *GetName());
	}

	SensorBox->OnComponentBeginOverlap.AddDynamic(this, &AIBSensorDoor::HandleSensorBeginOverlap);
	SensorBox->OnComponentEndOverlap.AddDynamic(this, &AIBSensorDoor::HandleSensorEndOverlap);

	State = EIBDoorState::Closed;
	Progress = 0.f;
	bBlockerActive = true;
	BlockerBox->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	ApplyProgress(0.f);

	// Pawns already inside when play starts do not always generate a begin-overlap we can bind to.
	TArray<AActor*> Inside;
	SensorBox->GetOverlappingActors(Inside, APawn::StaticClass());
	for (AActor* Actor : Inside)
	{
		if (const APawn* Pawn = Cast<APawn>(Actor))
		{
			if (DoesPawnQualify(Pawn))
			{
				Occupants.Add(const_cast<APawn*>(Pawn));
			}
		}
	}

	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: BeginPlay. Duration=%.2fs CloseDelay=%.2fs PlayerOnly=%d Locked=%d Occupants=%d"),
		*GetName(), GetOpenDuration(), CloseDelay, bPlayerPawnsOnly, bLocked, Occupants.Num());

	if (Occupants.Num() > 0)
	{
		BeginOpening();
	}
}

bool AIBSensorDoor::DoesPawnQualify(const APawn* Pawn) const
{
	if (!Pawn)
	{
		return false;
	}
	if (!bPlayerPawnsOnly)
	{
		return true;
	}
	return Pawn->IsPlayerControlled() || Pawn->GetPlayerState() != nullptr;
}

void AIBSensorDoor::HandleSensorBeginOverlap(UPrimitiveComponent* /*OverlappedComponent*/, AActor* OtherActor,
	UPrimitiveComponent* /*OtherComp*/, int32 /*OtherBodyIndex*/, bool /*bFromSweep*/, const FHitResult& /*SweepResult*/)
{
	APawn* Pawn = Cast<APawn>(OtherActor);
	if (!DoesPawnQualify(Pawn))
	{
		UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: ignored overlap from %s (not a qualifying pawn)."),
			*GetName(), OtherActor ? *OtherActor->GetName() : TEXT("null"));
		return;
	}

	Occupants.Add(Pawn);
	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: %s entered sensor. Occupants=%d State=%d"),
		*GetName(), *Pawn->GetName(), Occupants.Num(), static_cast<int32>(State));
	BeginOpening();
}

void AIBSensorDoor::HandleSensorEndOverlap(UPrimitiveComponent* /*OverlappedComponent*/, AActor* OtherActor,
	UPrimitiveComponent* /*OtherComp*/, int32 /*OtherBodyIndex*/)
{
	APawn* Pawn = Cast<APawn>(OtherActor);
	if (!Pawn || Occupants.Remove(Pawn) == 0)
	{
		return;
	}

	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: %s left sensor. Occupants=%d"),
		*GetName(), *Pawn->GetName(), Occupants.Num());
	if (Occupants.Num() == 0)
	{
		ScheduleClose();
	}
}

void AIBSensorDoor::PruneOccupants()
{
	for (auto It = Occupants.CreateIterator(); It; ++It)
	{
		if (!It->IsValid())
		{
			It.RemoveCurrent();
		}
	}
}

void AIBSensorDoor::ScheduleClose()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(CloseTimer, this, &AIBSensorDoor::OnCloseTimer, FMath::Max(CloseDelay, 0.01f), false);
		UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: close timer set (%.2fs)."), *GetName(), CloseDelay);
	}
}

void AIBSensorDoor::OnCloseTimer()
{
	PruneOccupants();
	if (Occupants.Num() > 0)
	{
		UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: close timer fired but %d occupant(s) inside - staying open."),
			*GetName(), Occupants.Num());
		return;
	}
	BeginClosing();
}

void AIBSensorDoor::BeginOpening()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(CloseTimer);
	}
	if (bLocked)
	{
		UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: locked - not opening."), *GetName());
		return;
	}
	if (State == EIBDoorState::Open || State == EIBDoorState::Opening)
	{
		return;
	}
	SetState(EIBDoorState::Opening);
	SetActorTickEnabled(true);
}

void AIBSensorDoor::BeginClosing()
{
	if (State == EIBDoorState::Closed || State == EIBDoorState::Closing)
	{
		return;
	}
	SetState(EIBDoorState::Closing);
	SetActorTickEnabled(true);
}

void AIBSensorDoor::RequestOpen()
{
	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: RequestOpen."), *GetName());
	BeginOpening();
}

void AIBSensorDoor::RequestClose()
{
	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: RequestClose (occupants=%d)."), *GetName(), Occupants.Num());
	BeginClosing();
}

void AIBSensorDoor::SetLocked(bool bNewLocked)
{
	bLocked = bNewLocked;
	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: locked=%d."), *GetName(), bLocked);
	if (!bLocked && Occupants.Num() > 0)
	{
		BeginOpening();
	}
}

float AIBSensorDoor::GetOpenDuration() const
{
	if (OpenDurationOverride > 0.f)
	{
		return OpenDurationOverride;
	}
	return OpenAnimation ? FMath::Max(OpenAnimation->GetPlayLength(), 0.05f) : 1.f;
}

void AIBSensorDoor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float Step = DeltaSeconds / GetOpenDuration();
	if (State == EIBDoorState::Opening)
	{
		ApplyProgress(Progress + Step);
		if (Progress >= 1.f)
		{
			SetState(EIBDoorState::Open);
			SetActorTickEnabled(false);
			if (Occupants.Num() == 0)
			{
				ScheduleClose(); // opened remotely (RequestOpen / unlocked) with nobody around
			}
		}
	}
	else if (State == EIBDoorState::Closing)
	{
		ApplyProgress(Progress - Step);
		if (Progress <= 0.f)
		{
			SetState(EIBDoorState::Closed);
			SetActorTickEnabled(false);
		}
	}
	else
	{
		SetActorTickEnabled(false);
	}
}

void AIBSensorDoor::ApplyProgress(float NewProgress)
{
	Progress = FMath::Clamp(NewProgress, 0.f, 1.f);

	if (OpenAnimation && DoorMesh)
	{
		if (DoorMesh->AnimationData.AnimToPlay.Get() != static_cast<UAnimationAsset*>(OpenAnimation.Get()) || DoorMesh->GetAnimationMode() != EAnimationMode::AnimationSingleNode)
		{
			DoorMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
			DoorMesh->SetAnimation(OpenAnimation);
			DoorMesh->Stop();
		}
		DoorMesh->SetPosition(Progress * OpenAnimation->GetPlayLength(), false);
	}

	if (BlockerBox)
	{
		const bool bShouldBlock = Progress < BlockerReleaseProgress;
		if (bShouldBlock != bBlockerActive)
		{
			bBlockerActive = bShouldBlock;
			BlockerBox->SetCollisionEnabled(bShouldBlock ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
			UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: blocker %s at progress %.2f."),
				*GetName(), bShouldBlock ? TEXT("ON") : TEXT("OFF"), Progress);
		}
	}
}

void AIBSensorDoor::SetState(EIBDoorState NewState)
{
	if (State == NewState)
	{
		return;
	}
	State = NewState;
	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: state -> %d (progress %.2f)."),
		*GetName(), static_cast<int32>(State), Progress);
	OnDoorStateChanged.Broadcast(this, State);
}

void AIBSensorDoor::ConfigureDoor(USkeletalMesh* InMesh, UAnimSequence* InOpenAnimation)
{
	if (InMesh)
	{
		DoorMesh->SetSkeletalMeshAsset(InMesh);
	}
	OpenAnimation = InOpenAnimation;
	DoorMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	if (OpenAnimation)
	{
		DoorMesh->SetAnimation(OpenAnimation);
		DoorMesh->Stop();
		DoorMesh->SetPosition(0.f, false);
	}
	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: ConfigureDoor mesh=%s anim=%s"),
		*GetName(), InMesh ? *InMesh->GetName() : TEXT("none"), OpenAnimation ? *OpenAnimation->GetName() : TEXT("none"));
}

void AIBSensorDoor::ConfigureVolumes(FVector SensorCenter, FVector SensorHalfExtent,
	FVector BlockerCenter, FVector BlockerHalfExtent, FRotator BlockerRotation)
{
	SensorBox->SetRelativeLocation(SensorCenter);
	SensorBox->SetBoxExtent(SensorHalfExtent);
	BlockerBox->SetRelativeLocation(BlockerCenter);
	BlockerBox->SetRelativeRotation(BlockerRotation);
	BlockerBox->SetBoxExtent(BlockerHalfExtent);
	UE_LOG(LogIronBreach, Verbose, TEXT("SensorDoor %s: ConfigureVolumes sensor=%s/%s blocker=%s/%s rot=%s"),
		*GetName(), *SensorCenter.ToString(), *SensorHalfExtent.ToString(),
		*BlockerCenter.ToString(), *BlockerHalfExtent.ToString(), *BlockerRotation.ToString());
}
