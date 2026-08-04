#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "IBKaijuAIController.generated.h"

/**
 * Minimal kaiju brain: steer at the nearest player and walk. No navmesh —
 * a scaled kaiju doesn't match the human nav agent, and a creature this size
 * walks through anything small enough to path around. Server-only.
 */
UCLASS()
class IRONBREACH_API AIBKaijuAIController : public AAIController
{
	GENERATED_BODY()

public:
	AIBKaijuAIController();

	virtual void Tick(float DeltaTime) override;

protected:
	/** Stop closing once inside this range (cm, pre-scale). Scaled by the pawn's actor scale. */
	UPROPERTY(EditDefaultsOnly, Category = "Kaiju AI", meta = (ClampMin = "0"))
	float StopDistance = 300.0f;

	/** How often to re-pick the nearest player. Cheap, but no need to do it every frame. */
	UPROPERTY(EditDefaultsOnly, Category = "Kaiju AI", meta = (ClampMin = "0.05"))
	float RetargetInterval = 0.5f;

private:
	AActor* FindNearestPlayer() const;

	TWeakObjectPtr<AActor> CurrentTarget;
	float TimeSinceRetarget = 0.0f;
};