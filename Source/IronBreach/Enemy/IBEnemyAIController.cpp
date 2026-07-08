#include "Enemy/IBEnemyAIController.h"
#include "Enemy/IBCharacter_Enemy.h"
#include "IronBreach.h"
#include "Perception/AIPerceptionComponent.h"
#include "Perception/AISenseConfig_Sight.h"
#include "NavigationSystem.h"
#include "Navigation/PathFollowingComponent.h" // EPathFollowingStatus
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/World.h"

AIBEnemyAIController::AIBEnemyAIController()
{
	PrimaryActorTick.bCanEverTick = true;

	PerceptionComponent2 = CreateDefaultSubobject<UAIPerceptionComponent>(TEXT("PerceptionComp"));
	SightConfig = CreateDefaultSubobject<UAISenseConfig_Sight>(TEXT("SightConfig"));

	SightConfig->SightRadius = 3000.0f;
	SightConfig->LoseSightRadius = 3400.0f;
	SightConfig->PeripheralVisionAngleDegrees = 75.0f;
	SightConfig->DetectionByAffiliation.bDetectEnemies = true;
	SightConfig->DetectionByAffiliation.bDetectNeutrals = true;
	SightConfig->DetectionByAffiliation.bDetectFriendlies = true;

	PerceptionComponent2->ConfigureSense(*SightConfig);
	PerceptionComponent2->SetDominantSense(SightConfig->GetSenseImplementation());
	SetPerceptionComponent(*PerceptionComponent2);
}

void AIBEnemyAIController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	EnemyPawn = Cast<AIBCharacter_Enemy>(InPawn);
	HomeLocation = InPawn ? InPawn->GetActorLocation() : FVector::ZeroVector;

	if (PerceptionComponent2)
	{
		PerceptionComponent2->OnTargetPerceptionUpdated.AddDynamic(this, &AIBEnemyAIController::OnTargetPerceptionUpdated);
	}

	SetMaxWalkSpeed(PatrolWalkSpeed);
	StartNewPatrolMove();
}

void AIBEnemyAIController::OnTargetPerceptionUpdated(AActor* Actor, FAIStimulus Stimulus)
{
	// Any player-controlled pawn is a valid target (co-op aware)
	const APawn* AsPawn = Cast<APawn>(Actor);
	if (!AsPawn || !AsPawn->IsPlayerControlled()) return;

	if (Stimulus.WasSuccessfullySensed())
	{
		TargetActor = Actor;
		LastSeenTime = GetWorld()->GetTimeSeconds();
	}
	// On lost sight we keep TargetActor until LoseInterestTime expires (handled in Tick)
}

void AIBEnemyAIController::NotifyDamagedBy(AController* InstigatedBy, AActor* DamageCauser)
{
	APawn* Attacker = nullptr;
	if (InstigatedBy)
	{
		Attacker = InstigatedBy->GetPawn();
	}
	if (!Attacker)
	{
		Attacker = Cast<APawn>(DamageCauser);
	}
	if (Attacker && Attacker->IsPlayerControlled())
	{
		TargetActor = Attacker;
		LastSeenTime = GetWorld()->GetTimeSeconds();
	}
}

void AIBEnemyAIController::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (!EnemyPawn || EnemyPawn->IsDead()) return;

	const float Now = GetWorld()->GetTimeSeconds();

	// Direct sight check every tick. This intentionally doesn't rely on AIPerception
	// events (belt and suspenders) — perception can silently fail to register listeners.
	if (!TargetActor)
	{
		const float SightRange = SightConfig ? SightConfig->SightRadius : 3000.0f;
		if (AActor* Spotted = FindNearestVisiblePlayerPawn(SightRange))
		{
			TargetActor = Spotted;
			LastSeenTime = Now;
			UE_LOG(LogIronBreach, Log, TEXT("%s spotted %s"), *GetNameSafe(EnemyPawn), *GetNameSafe(Spotted));
		}
	}

	// Drop the target if we haven't seen them in a while
	if (TargetActor && (Now - LastSeenTime) > LoseInterestTime)
	{
		TargetActor = nullptr;
	}

	// Drop dead targets immediately: a respawn-pending corpse detaches from its
	// controller, so it stops being player-controlled the moment it dies.
	if (const APawn* TargetPawn = Cast<APawn>(TargetActor.Get()))
	{
		if (!TargetPawn->IsPlayerControlled())
		{
			TargetActor = nullptr;
		}
	}

	const EEnemyAIState PreviousState = CurrentState;

	if (TargetActor)
	{
		const float Dist = FVector::Dist(EnemyPawn->GetActorLocation(), TargetActor->GetActorLocation());
		const bool bCanSee = LineOfSightTo(TargetActor);

		if (bCanSee)
		{
			LastSeenTime = Now;
		}

		if (bCanSee && Dist <= AttackRange)
		{
			CurrentState = EEnemyAIState::Attack;
			StopMovement();
			SetFocus(TargetActor);
			EnemyPawn->FireAt(TargetActor);
		}
		else
		{
			CurrentState = EEnemyAIState::Chase;
			SetFocus(TargetActor);
			SetMaxWalkSpeed(ChaseRunSpeed);
			MoveToActor(TargetActor, AttackRange * 0.6f, true);
		}
	}
	else
	{
		CurrentState = EEnemyAIState::Patrol;
		ClearFocus(EAIFocusPriority::Gameplay);
		SetMaxWalkSpeed(PatrolWalkSpeed);

		// Pick a new wander point when the previous move finished
		if (GetMoveStatus() == EPathFollowingStatus::Idle)
		{
			StartNewPatrolMove();
		}
	}

	if (PreviousState != CurrentState)
	{
		UE_LOG(LogIronBreach, Verbose, TEXT("%s AI state: %d -> %d"), *GetNameSafe(EnemyPawn), (int32)PreviousState, (int32)CurrentState);
	}
}

void AIBEnemyAIController::SetMaxWalkSpeed(float Speed)
{
	if (EnemyPawn && EnemyPawn->GetCharacterMovement())
	{
		EnemyPawn->GetCharacterMovement()->MaxWalkSpeed = Speed;
	}
}

AActor* AIBEnemyAIController::FindNearestVisiblePlayerPawn(float MaxRange) const
{
	if (!EnemyPawn) return nullptr;

	const FVector From = EnemyPawn->GetActorLocation();
	AActor* Best = nullptr;
	float BestDist = MaxRange;

	// AI runs server-side only, where every player's controller exists.
	for (FConstPlayerControllerIterator It = GetWorld()->GetPlayerControllerIterator(); It; ++It)
	{
		const APlayerController* PC = It->Get();
		APawn* Candidate = PC ? PC->GetPawn() : nullptr;
		if (!Candidate) continue;

		const float Dist = FVector::Dist(From, Candidate->GetActorLocation());
		if (Dist <= BestDist && LineOfSightTo(Candidate))
		{
			Best = Candidate;
			BestDist = Dist;
		}
	}
	return Best;
}

void AIBEnemyAIController::StartNewPatrolMove()
{
	if (!EnemyPawn) return;

	if (UNavigationSystemV1* NavSys = UNavigationSystemV1::GetCurrent(GetWorld()))
	{
		FNavLocation Result;
		if (NavSys->GetRandomReachablePointInRadius(HomeLocation, PatrolRadius, Result))
		{
			MoveToLocation(Result.Location, 50.0f);
		}
	}
}
