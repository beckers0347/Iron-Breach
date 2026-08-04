#include "Kaiju/IBKaijuAIController.h"
#include "IronBreach.h"
#include "Kaiju/IBCharacter_Kaiju.h"
#include "Combat/HealthComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"

AIBKaijuAIController::AIBKaijuAIController()
{
	PrimaryActorTick.bCanEverTick = true;
}

AActor* AIBKaijuAIController::FindNearestPlayer() const
{
	APawn* Self = GetPawn();
	UWorld* World = GetWorld();
	if (!Self || !World) return nullptr;

	AActor* Best = nullptr;
	float BestDistSq = TNumericLimits<float>::Max();

	for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
	{
		APlayerController* PC = It->Get();
		APawn* Candidate = PC ? PC->GetPawn() : nullptr;
		if (!Candidate) continue;

		const float DistSq = FVector::DistSquared(Candidate->GetActorLocation(), Self->GetActorLocation());
		if (DistSq < BestDistSq)
		{
			BestDistSq = DistSq;
			Best = Candidate;
		}
	}
	return Best;
}

void AIBKaijuAIController::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	APawn* Self = GetPawn();
	if (!Self || !Self->HasAuthority()) return;

	// A dead kaiju stops walking.
	if (const AIBCharacter_Kaiju* Kaiju = Cast<AIBCharacter_Kaiju>(Self))
	{
		if (const UHealthComponent* Health = Kaiju->FindComponentByClass<UHealthComponent>())
		{
			if (Health->IsDepleted()) return;
		}
	}

	TimeSinceRetarget += DeltaTime;
	if (TimeSinceRetarget >= RetargetInterval || !CurrentTarget.IsValid())
	{
		TimeSinceRetarget = 0.0f;
		CurrentTarget = FindNearestPlayer();
	}

	AActor* Target = CurrentTarget.Get();
	if (!Target) return;

	// Steer on the horizontal plane only — no walking uphill into the sky.
	FVector ToTarget = Target->GetActorLocation() - Self->GetActorLocation();
	ToTarget.Z = 0.0f;

	// Scale the stop distance with the creature so a 60m kaiju doesn't stand on your face.
	const float ScaledStop = StopDistance * Self->GetActorScale3D().GetMax();
	if (ToTarget.SizeSquared() <= FMath::Square(ScaledStop)) return;

	Self->AddMovementInput(ToTarget.GetSafeNormal(), 1.0f);
}