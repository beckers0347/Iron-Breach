#include "Combat/TargetingComponent.h"
#include "IronBreach.h"
#include "Combat/DamageableInterface.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Controller.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"
#include "Engine/HitResult.h"
#include "TimerManager.h"

UTargetingComponent::UTargetingComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // timer-driven scan
	SetIsReplicatedByDefault(false);           // local/cosmetic (see class comment)
}

void UTargetingComponent::BeginPlay()
{
	Super::BeginPlay();

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(ScanTimerHandle, this, &UTargetingComponent::Scan, ScanInterval, /*bLoop=*/true);
	}
}

void UTargetingComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(ScanTimerHandle);
	}
	Super::EndPlay(EndPlayReason);
}

void UTargetingComponent::SetTargetingEnabled(bool bEnabled)
{
	bTargetingEnabled = bEnabled;
	if (!bEnabled)
	{
		SetLockedTarget(nullptr);
	}
}

bool UTargetingComponent::GetViewPoint(FVector& OutLocation, FVector& OutDirection) const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	if (!Pawn) return false;

	FRotator ViewRot;
	if (AController* PawnController = Pawn->GetController())
	{
		PawnController->GetPlayerViewPoint(OutLocation, ViewRot);
	}
	else
	{
		Pawn->GetActorEyesViewPoint(OutLocation, ViewRot);
	}
	OutDirection = ViewRot.Vector();
	return true;
}

void UTargetingComponent::Scan()
{
	if (!bTargetingEnabled) return;

	UWorld* World = GetWorld();
	AActor* OwnerActor = GetOwner();
	if (!World || !OwnerActor) return;

	FVector ViewLoc, ViewDir;
	if (!GetViewPoint(ViewLoc, ViewDir)) return;

	const float CosLimit = FMath::Cos(FMath::DegreesToRadians(ConeHalfAngleDegrees));

	// Candidates: anything damageable. The interface is the project's one damage contract
	// (enemies, kaiju, players), which makes it the natural lock filter too.
	TArray<AActor*> Candidates;
	UGameplayStatics::GetAllActorsWithInterface(World, UDamageableInterface::StaticClass(), Candidates);

	AActor* Best = nullptr;
	float BestScore = -1.0f; // higher = better (alignment first, distance as tiebreak)

	for (AActor* Candidate : Candidates)
	{
		if (!Candidate || Candidate == OwnerActor) continue;

		// Never lock our own vehicle chain (seat -> hull, hull -> seat, own infantry pawn).
		if (Candidate->IsAttachedTo(OwnerActor) || OwnerActor->IsAttachedTo(Candidate)) continue;
		if (Candidate->GetOwner() == OwnerActor || OwnerActor->GetOwner() == Candidate) continue;

		const FVector ToTarget = Candidate->GetActorLocation() - ViewLoc;
		const float Dist = ToTarget.Size();
		if (Dist > MaxRange || Dist < KINDA_SMALL_NUMBER) continue;

		const float CosAngle = FVector::DotProduct(ToTarget / Dist, ViewDir);
		if (CosAngle < CosLimit) continue;

		if (bRequireLineOfSight)
		{
			FHitResult Hit;
			FCollisionQueryParams Params;
			Params.AddIgnoredActor(OwnerActor);
			Params.AddIgnoredActor(Candidate);
			if (const APawn* OwnerPawn = Cast<APawn>(OwnerActor))
			{
				// Ignore the rest of our vehicle chain in the trace too.
				if (AActor* Parent = OwnerPawn->GetAttachParentActor()) Params.AddIgnoredActor(Parent);
			}
			if (World->LineTraceSingleByChannel(Hit, ViewLoc, Candidate->GetActorLocation(), ECC_Visibility, Params))
			{
				continue; // something solid in the way
			}
		}

		// Alignment dominates; nearer wins among near-equal alignment.
		const float Score = CosAngle * 10000.0f - Dist * 0.001f;
		if (Score > BestScore)
		{
			BestScore = Score;
			Best = Candidate;
		}
	}

	SetLockedTarget(Best);
}

void UTargetingComponent::SetLockedTarget(AActor* NewTarget)
{
	if (NewTarget == LockedTarget) return;

	AActor* Old = LockedTarget;
	LockedTarget = NewTarget;
	OnTargetChanged.Broadcast(NewTarget, Old);
}
