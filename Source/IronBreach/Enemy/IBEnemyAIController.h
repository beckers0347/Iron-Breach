#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "Perception/AIPerceptionTypes.h" // FAIStimulus is passed by value through a dynamic delegate; full type required
#include "IBEnemyAIController.generated.h"

class UAIPerceptionComponent;
class UAISenseConfig_Sight;
class AIBCharacter_Enemy;

UENUM(BlueprintType)
enum class EEnemyAIState : uint8
{
	Patrol		UMETA(DisplayName = "Patrol"),
	Chase		UMETA(DisplayName = "Chase"),
	Attack		UMETA(DisplayName = "Attack")
};

/**
 * Compact patrol/chase/attack brain driven by sight perception.
 * Kept deliberately small so the logic can be ported to a StateTree asset later.
 */
UCLASS()
class IRONBREACH_API AIBEnemyAIController : public AAIController
{
	GENERATED_BODY()

public:
	AIBEnemyAIController();

	/** Called by the pawn when it takes damage so we can aggro the attacker. */
	void NotifyDamagedBy(AController* InstigatedBy, AActor* DamageCauser);

	UFUNCTION(BlueprintPure, Category = "Enemy AI")
	EEnemyAIState GetAIState() const { return CurrentState; }

protected:
	virtual void OnPossess(APawn* InPawn) override;
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, Category = "Enemy AI")
	TObjectPtr<UAIPerceptionComponent> PerceptionComponent2;

	UPROPERTY()
	TObjectPtr<UAISenseConfig_Sight> SightConfig;

	// --- Tuning ---

	/** Radius around spawn point used to pick patrol destinations. */
	UPROPERTY(EditAnywhere, Category = "Enemy AI", meta = (ClampMin = "100"))
	float PatrolRadius = 1200.0f;

	/** Start shooting when target is within this range and visible. */
	UPROPERTY(EditAnywhere, Category = "Enemy AI", meta = (ClampMin = "100"))
	float AttackRange = 1500.0f;

	/** Give up the chase this many seconds after last seeing the target. */
	UPROPERTY(EditAnywhere, Category = "Enemy AI", meta = (ClampMin = "0"))
	float LoseInterestTime = 6.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy AI")
	float PatrolWalkSpeed = 200.0f;

	UPROPERTY(EditAnywhere, Category = "Enemy AI")
	float ChaseRunSpeed = 500.0f;

	UFUNCTION()
	void OnTargetPerceptionUpdated(AActor* Actor, FAIStimulus Stimulus);

private:
	void SetMaxWalkSpeed(float Speed);
	void StartNewPatrolMove();

	UPROPERTY()
	TObjectPtr<AIBCharacter_Enemy> EnemyPawn;

	UPROPERTY()
	TObjectPtr<AActor> TargetActor;

	EEnemyAIState CurrentState = EEnemyAIState::Patrol;
	FVector HomeLocation = FVector::ZeroVector;
	float LastSeenTime = -1000.0f;
};
