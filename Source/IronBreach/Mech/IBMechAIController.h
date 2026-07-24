#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "IBMechAIController.generated.h"

class UBehaviorTree;

UCLASS()
class IRONBREACH_API AIBMechAIController : public AAIController
{
	GENERATED_BODY()

public:
	AIBMechAIController();

	UPROPERTY(EditAnywhere, Category = "Mech AI")
	UBehaviorTree* MechBehaviorTree;

protected:
	virtual void BeginPlay() override;
	virtual void OnPossess(APawn* InPawn) override;
};