#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "IBMechAIController.generated.h"

class UBehaviorTree;

/**
 * The AI co-pilot ("VIRGIL"). Possesses the AIBGunnerSeat when no human holds it —
 * the SAME pawn a human gunner possesses, so parity is by construction (Caryatid doc
 * u3-05). It never possesses the hull, and it never claims a seat on its own:
 * possession is not boarding — seat assignment is owned by AIBMech_Base.
 *
 * Combat behavior (target selection, firing, response calls) arrives with its
 * behavior tree; today it holds the seat so the crew model is always complete.
 * Per the drama spec §5.5 it must be deterministic when it does fire — no
 * stochastic misses, ever.
 */
UCLASS()
class IRONBREACH_API AIBMechAIController : public AAIController
{
	GENERATED_BODY()

public:
	AIBMechAIController();

	UPROPERTY(EditAnywhere, Category = "Mech AI")
	TObjectPtr<UBehaviorTree> MechBehaviorTree;

protected:
	virtual void BeginPlay() override;
	virtual void OnPossess(APawn* InPawn) override;
	virtual void OnUnPossess() override;
};
